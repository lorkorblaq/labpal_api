from flask_restful import Resource, abort, reqparse
from flask import jsonify, make_response, request
from bson import json_util, ObjectId
from engine import db_clinical, client, org_users_db, get_org_name
from datetime import datetime, timedelta
import math

USERS_COLLECTION = org_users_db['users']
ORG_COLLECTION = org_users_db['organisations']
item_parser = reqparse.RequestParser()
item_parser.add_argument("item", type=str, help="item is required", required=False)
item_parser.add_argument("quantity", type=int, help="Quantity is required", required=False)
item_parser.add_argument("tests/vial", type=int, help="Tests per vial is required", required=False)
item_parser.add_argument("vials/pack", type=int, help="Vials per pack is required", required=False)
item_parser.add_argument("reOrderLevel", type=int, help="Reorder level is required", required=False)
item_parser.add_argument("class", type=str, help="Class is required", required=False)
item_parser.add_argument("category", type=str, help="Category is required", required=False)
item_parser.add_argument("tests/day", type=int, help="Tests per day is required", required=False)
item_parser.add_argument("bench", type=str, help="Bench is required", required=False)

    


def requiste(bench, days, categories, user_id, lab_name):
    try:
        orgname = get_org_name(user_id)
        ITEMS_COLLECTION = client[orgname+'_db'][lab_name+'_items']

    except ValueError as e:
        abort(404, message=str(e))
        
    query = {}
    if bench:
        query["bench"] = bench
    if categories:
        query["category"] = {"$in": categories}
    print("Query:", query)
    
    pipeline = [
        # Match documents based on the bench field
        {"$match": query},
        # Project the fields needed for calculations and convert to numeric types
        {"$project": {
            "bench": 1,
            "item": 1,
            "quantity": {"$toDouble": "$quantity"},
            "tests_per_day": {"$toDouble": "$tests/day"},
            "tests_per_vial": {"$toDouble": "$tests/vial"}
        }},
        {"$addFields": {
            "total_tests_in_stock": {"$multiply": ["$quantity", "$tests_per_vial"]},
            "quantity_test_requested": {"$multiply": ["$tests_per_day", days]}
        }},
        {"$addFields": {
            "total_days_to_last": {
                "$cond": {
                    "if": {"$gt": ["$tests_per_day", 0]},
                    "then": {"$ceil": {"$divide": ["$total_tests_in_stock", "$tests_per_day"]}},
                    "else": None
                }
            }
        }}
    ]
    
    # Execute the aggregation pipeline
    result = list(ITEMS_COLLECTION.aggregate(pipeline))
    
    # Convert MongoDB documents to dictionaries
    result_dicts = []
    for item in result:
        print("Item:", item)
        if item.get("total_tests_in_stock") is not None:
            if item.get("total_tests_in_stock") < item.get("quantity_test_requested"):
                item["amount_needed"] = item.get("quantity_test_requested") - item.get("total_tests_in_stock")
                amount_needed = math.ceil(item.get("amount_needed") / item.get("tests_per_vial"))
            else:
                item["amount_needed"] = 0
                amount_needed = 0

            result_dict = {
                "bench": item.get("bench", ""),
                "quantity": item.get("quantity", ""),
                "item": item.get("item", ""),
                "tests_per_day": item.get("tests_per_day", ""),
                "total_tests_in_stock": item.get("total_tests_in_stock", ""),
                "quantity_test_requested": item.get("quantity_test_requested", ""),
                "total_days_to_last": item.get("total_days_to_last", ""),
                "amount_needed": amount_needed
            }
            result_dicts.append(result_dict)
    
    # Return the result as JSON
    return result_dicts



    # Example usage:

class ItemsResource(Resource):
    def get(self, user_id, lab_name):  
        try:
            orgname = get_org_name(user_id)
            ITEMS_COLLECTION = client[orgname+'_db'][lab_name+'_items']

        except ValueError as e:
            abort(404, message=str(e))
        
        results = list(ITEMS_COLLECTION.find())
        if not results:
            abort(404, message="No Item Available")
        item_list=[]
        # Convert ObjectId to string for JSON serialization
        for result in results:
            result["_id"] = str(result["_id"])
            item_list.append(result)
        response_data = {"items": item_list}
        # Create a Flask response with JSON data
        # print((response))
        return response_data, 200

class ItemsBulkPush(Resource):
    def post(self, user_id, lab_name):
        try:
            orgname = get_org_name(user_id)
            ITEMS_COLLECTION = client[orgname+'_db'][lab_name+'_items']

        except ValueError as e:
            abort(404, message=str(e))
        
        json_data = request.get_json()
        if not json_data:
            abort(400, message="No JSON data provided")
        
        # Ensure the required columns are present
        required_columns = {'item', 'quantity', 'tests/vial', 'vials/pack', 'reOrderLevel', 'class', 'category', 'tests/day', 'bench'}

        for entry in json_data:
            if not required_columns.issubset(entry.keys()):
                abort(400, message=f"Your data must contain the columns: {', '.join(required_columns)}")

            
            # Insert data into the MongoDB collection
            ITEMS_COLLECTION.insert_many(json_data)
            
            return make_response(jsonify({"message": "Data imported successfully"}), 201)
        
        # except Exception as e:
        #     abort(500, message=str(e))

class ItemsPush(Resource):
    def post(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            ITEMS_COLLECTION = client[org_name+'_db'][lab_name+'_items']
        except ValueError as e:
            abort(404, message=str(e))
        args = item_parser.parse_args()
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        if not user:
            return {"message": "User does not exist, kindly contact Lorkorblaq"}, 400
        elif not org_name:
            return {"message": "Organisation does not exist, kindly contact Lorkorblaq"}, 400
        labs = user.get('labs_access')
        if lab_name in labs:
            pass
        
        # item = MACHINES_COLLECTION.find_one({'item': args['item']})
        items_list = {
            "item": args['item'],
            "quantity": args['quantity'],
            "tests/vial": args['tests/vial'],
            "vials/pack": args['vials/pack'],
            "reOrderLevel": args['reOrderLevel'],
            "class": args['class'],
            "category": args['category'],
            "tests/day": args['tests/day'],
            "bench": args['bench'],
            }
        if not user:
                return {"message": "User does not exist, kindly contact Lorkorblaq"}, 400
        try:

            inserted_id = ITEMS_COLLECTION.insert_one(items_list).inserted_id
            inserted_id = str(inserted_id)

            response = {
                "message": "Item created successfully",
                "machine_id": inserted_id
            }
            return response, 200
        except Exception as e:
            return {"message": "Error occured while pushing item", "error": str(e)}

class ItemsPut(Resource):
    def put(self, user_id, lab_name):
        try:
            orgname = get_org_name(user_id)
            ITEMS_COLLECTION = client[orgname+'_db'][lab_name+'_items']

        except ValueError as e:
            abort(404, message=str(e))
        
        args = item_parser.parse_args()
        if not args['item']:
            abort(404, message="Item not provided, kindly contact Lorkorblaq")
        elif not ITEMS_COLLECTION.find_one({'item': args['item']}):
            abort(404, message="The item you about to update doesn't exists")
        filter = {'item': args['item']}
        if args['direction'] == "To": 
            new_value = {'$inc': {'quantity': -args['quantity']}}
            print(new_value)
            ITEMS_COLLECTION.update_one(filter, new_value)
        elif args['direction'] == "From":
            new_value = {'$inc': {'quantity': args['quantity']}}
            print(new_value)
            ITEMS_COLLECTION.update_one(filter, new_value)
        response = {"message": "Your data has been updated successfully",}
        return response, 200

class ItemsRequisite(Resource):
    def post(self, user_id, lab_name):      
        req_parser = reqparse.RequestParser()
        req_parser.add_argument("bench", type=str, help="Bench is required", required=True)
        req_parser.add_argument("categories", type=str, action='append', required=False)
        req_parser.add_argument("days", type=int, help="Quantity is required", required=True)
        args = req_parser.parse_args()

        bench = args['bench']
        days = args['days']
        categories = args.get('categories', [])  # Get list of categories or empty list if not provided        
        results = requiste(bench, days, categories, user_id, lab_name)
        print(results)
        response = results
        # for result in results:

        response = {"requested": results,}
        return response, 200
    
class ItemsDeleteResource(Resource):
    def delete(self, user_id, lab_name):
        try:
            orgname = get_org_name(user_id)
            ITEMS_COLLECTION = client[orgname+'_db'][lab_name+'_items']

        except ValueError as e:
            abort(404, message=str(e))
        
        try:
            result = ITEMS_COLLECTION.delete_many({})
            if result.deleted_count == 0:
                abort(404, message="No items to delete")
            return make_response(jsonify({"message": "All items deleted successfully"}), 200)
        except Exception as e:
            abort(500, message=str(e))