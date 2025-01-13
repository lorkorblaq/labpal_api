from flask import jsonify
from flask_restful import Resource, reqparse, abort, request
from datetime import datetime, timedelta
from engine import db_clinical, client, org_users_db, get_org_name
from bson import ObjectId
import pymongo
from dateutil import parser


USERS_COLLECTION = org_users_db['users']
lot_exp_parser = reqparse.RequestParser()
utc_now = datetime.now()
wat_now = utc_now + timedelta(hours=1)

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Not a valid date: '{0}'.".format(s))
lot_exp_parser.add_argument("item", type=str, help="Item is required", 
required=False)
lot_exp_parser.add_argument("lot_numb", type=str, help="Lot is required", 
required=False)
lot_exp_parser.add_argument("expiration", type=valid_date, help="expiration is required", required=False)

class Lot_exp_Push(Resource):
    def post(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            ITEMS_COLLECTION = client[org_name + '_db'][lab_name + '_items']
            LOT_EXP_COLLECTION = client[org_name + '_db'][lab_name + '_lot_exp']
        except ValueError as e:
            abort(404, message=str(e))

        args = lot_exp_parser.parse_args()
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        if not user:
            return {"message": "User does not exist, kindly contact the admin"}, 400
        lot_exp = {
                "item": args["item"], 
                "lot_numb": args["lot_numb"],
                "expiration": args["expiration"],
                "quantity": 0,
                "created at": wat_now,
            }
        item = ITEMS_COLLECTION.find_one({'item': args['item']})
        if not item:
            return {"message": "Item does not exist, kindly contact the admin"}, 400
        elif LOT_EXP_COLLECTION.find_one({'lot_numb': args['lot_numb']}):
            return {"message": "Lot number already exists"}, 400
        else:
            try:
                inserted_id = LOT_EXP_COLLECTION.insert_one(lot_exp).inserted_id
                inserted_id = str(inserted_id)
                response = {
                    "message": "lot exp created successfully",
                    "lot_exp_id": inserted_id
                    }
                return response, 200
            except Exception as e:
                return {"message": "Error occured while pushing item", "error": str(e)}



class Lot_exp_Bulk_Push(Resource):
    def post(self, user_id, lab_name):
        try:
            # Retrieve the organization name based on user ID
            orgname = get_org_name(user_id)
            # Access the specific items collection for the lab in the user's database
            ITEMS_COLLECTION = client[orgname+'_db'][lab_name+'_items']
            LOT_EXP_COLLECTION = client[orgname + '_db'][lab_name + '_lot_exp']

        except ValueError as e:
            # If a ValueError occurs (e.g., invalid user ID), return a 404 error with the exception message
            abort(404, message=str(e))

        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        if not user:
            return {"message": "User does not exist, kindly contact the admin"}, 400

        # Get the JSON data from the request
        json_data = request.get_json()
        if not json_data:
            # If no JSON data is provided in the request, return a 400 error
            abort(400, message="No JSON data provided")

        # Define the required columns that must be present in the input data
        required_columns = {'item', 'lot_numb', 'expiration', 'quantity'}
        not_found_items = []

        # Check each entry in the provided JSON data to ensure all required columns are present
        # for entry in json_data:
        #     if not required_columns.issubset(entry.keys()):
        #         # If any required column is missing, return a 400 error with a detailed message
        #         abort(400, message=f"Your data must contain the columns: {', '.join(required_columns)}")
        #     try:
        #         entry['expiration'] = parser.parse(entry['expiration'])
        #     except Exception as e:
        #         abort(400, message=f"Invalid expiration date format for lot {entry['lot_numb']}: {e}")


        try:
            for entry in json_data:
                # Validate required columns
                if not required_columns.issubset(entry.keys()):
                    abort(400, message=f"Your data must contain the columns: {', '.join(required_columns)}")

                # Convert expiration to datetime
                try:
                    entry['expiration'] = parser.parse(entry['expiration'])
                except Exception as e:
                    abort(400, message=f"Invalid expiration date format for lot {entry['lot_numb']}: {e}")

                item_name = entry['item']
                lot_numb = entry['lot_numb']
                quantity_to_add = entry['quantity']

                # Use upsert to handle both new and existing lots
                LOT_EXP_COLLECTION.update_one(
                    {'lot_numb': lot_numb},
                    {
                        '$inc': {'quantity': quantity_to_add},
                        '$setOnInsert': {
                            'item': item_name,
                            'expiration': entry['expiration'],
                            'created at': wat_now
                        },
                        '$set': {'updated at': wat_now}
                    },
                    upsert=True
                )

                # Update the corresponding item in ITEMS_COLLECTION
                item_result = ITEMS_COLLECTION.update_one(
                    {'item': item_name},
                    {'$inc': {'quantity': quantity_to_add}}
                )

                # If no document was modified in ITEMS_COLLECTION, the item was not found
                if item_result.matched_count == 0:
                    not_found_items.append(item_name)

            # Insert only the new items into the MongoDB collection
            response = {"message": "Lot numbers inserted successfully"}
            if not_found_items:
                response['note'] = f"The following items were not found in your inventory and were not updated: {', '.join(not_found_items)}"

            return response, 200
        except pymongo.errors.BulkWriteError as bwe:
            # Handle MongoDB bulk write errors
            abort(500, message=f"Bulk write error: {bwe.details}")
        except Exception as e:
            # Handle general errors
            abort(500, message=str(e))










class Lot_exp_Get(Resource):
    def get(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            ITEMS_COLLECTION = client[org_name + '_db'][lab_name + '_items']
            LOT_EXP_COLLECTION = client[org_name + '_db'][lab_name + '_lot_exp']
        except ValueError as e:
            abort(404, message=str(e))    
        lot_exps = list(LOT_EXP_COLLECTION.find())
        # print(results)
        if not lot_exps:
            abort(404, message="No lot available, kindly add via Channels")
        lotexp_list=[]
        # Convert ObjectId to string for JSON serialization
        
        for lot_exp in lot_exps:
            lot_exp["_id"] = str(lot_exp["_id"])
            lot_exp["item"] = str(lot_exp["item"])
            lot_exp["quantity"] = lot_exp["quantity"]
            lot_exp["expiration"] = lot_exp["expiration"].strftime("%Y-%m-%d")
            lot_exp["created at"] = lot_exp["created at"].strftime("%Y-%m-%d")
            lot_exp["updated at"] = lot_exp["updated at"].strftime("%Y-%m-%d")
            lotexp_list.append(lot_exp)
        response_data = {"lotexp": lotexp_list}
        # Create a Flask response with JSON data
        # print((response))
        return response_data, 200