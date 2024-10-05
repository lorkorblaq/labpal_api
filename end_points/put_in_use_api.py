from flask import jsonify, request
from flask_restful import Resource, reqparse, abort, fields, marshal_with
from bson import ObjectId
from datetime import datetime, timedelta
from engine import db_clinical, client, org_users_db, get_org_name
from werkzeug.exceptions import HTTPException


# PUT_IN_USE_COLLECTION = db_clinical['put in use']
ITEMS_COLLECTION = db_clinical['items']
USERS_COLLECTION = org_users_db['users']

put_in_use_parser = reqparse.RequestParser()

put_in_use_parser.add_argument("item", type=str, help="Item is required", required=False)
put_in_use_parser.add_argument("bench", type=str, help="Bench is required", required=False)
put_in_use_parser.add_argument("machine", type=str, help="Machine is required", required=False)
put_in_use_parser.add_argument("lot_numb", type=str, help="Lot numb is required", required=False)
put_in_use_parser.add_argument("quantity", type=int, help="Quantity is required", required=False)
put_in_use_parser.add_argument("description", type=str, help="Description is required", required=False)

class P_in_usePush(Resource):
    def post(self, user_id, lab_name):
        try:
            # Fetch organization and collections
            org_name = get_org_name(user_id)
            ITEMS_COLLECTION = client[org_name + '_db'][lab_name + '_items']
            PUT_IN_USE_COLLECTION = client[org_name + '_db'][lab_name + '_piu']
            LOT_EXP_COLLECTION = client[org_name + '_db'][lab_name + '_lot_exp']
        except ValueError as e:
            abort(404, message=str(e))

        try:
            # Get the current time
            utc_now = datetime.now()
            wat_now = utc_now + timedelta(hours=1)

            # Parse arguments
            args = put_in_use_parser.parse_args()
            user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})

            # Validate user existence
            if not user:
                abort(400, message="User does not exist, kindly contact support")

            # Fetch item and lot data
            item = ITEMS_COLLECTION.find_one({'item': args['item']})
            lot_exp = LOT_EXP_COLLECTION.find_one({'lot_numb': args['lot_numb']})

            # Validate item and lot existence
            if not item:
                abort(400, message="Item does not exist, kindly contact support")
            if not lot_exp:
                abort(400, message="Lot number does not exist, kindly contact support")

            # Validate lot association with item
            if lot_exp['item'] != args['item']:
                abort(400, message="Lot number is not associated with the given item, kindly contact support")

            # Validate quantity availability
            if item['quantity'] < args['quantity']:
                abort(400, message="Quantity to be put in use is more than available quantity in stock")
            if args['quantity'] <= 0:
                abort(400, message="Quantity in must be greater than zero")

            # Prepare the data to insert
            bench = item.get('bench')
            name = user.get('firstname') + ' ' + user.get('lastname')

            piu = {
                'user': name,
                'item': args["item"],
                'bench': bench,
                'machine': args["machine"],
                'lot_numb': args["lot_numb"],
                'quantity': args["quantity"],
                'description': args["description"],
                'created at': wat_now,
            }
            
            # Insert the item into the put in use collection
            inserted_id = PUT_IN_USE_COLLECTION.insert_one(piu).inserted_id
            inserted_id = str(inserted_id)

            if inserted_id:
                # Update item and lot quantity
                ITEMS_COLLECTION.update_one({'item': args['item']}, {'$inc': {'quantity': -args['quantity']}})
                LOT_EXP_COLLECTION.update_one({'lot_numb': args['lot_numb']}, {'$inc': {'quantity': -args['quantity']}})
            else:
                abort(400, message="Error occurred while pushing put in use item")

            # Return success response
            response = {
                "message": "Item put in use successfully",
                'piu_id': inserted_id
            }
            return response, 200
        
        except HTTPException as e:
            # Let HTTP exceptions (abort) pass through without being caught
            raise e
        except Exception as e:
            # Handle any other error that occurs
            return {"message": "Error occurred while pushing put in use item", "error": str(e)}

class P_in_usePut(Resource):
    def put(self, user_id, lab_name, piu_id):
        try:
            org_name = get_org_name(user_id)
            ITEMS_COLLECTION = client[org_name + '_db'][lab_name + '_items']
            PUT_IN_USE_COLLECTION = client[org_name + '_db'][lab_name + '_piu']
        except ValueError as e:
            abort(404, message=str(e))
        utc_now = datetime.now()
        args = put_in_use_parser.parse_args()
        item = ITEMS_COLLECTION.find_one({'item': args['item']})
        pius = PUT_IN_USE_COLLECTION.find_one({'_id': ObjectId(piu_id)})

        # if not item:
        #     abort(404, message="Item not found, kindly contact Lorkorblaq")
        
        # item_id = item['_id']
        # print(item_id)
        # result['item'] = item_id
        for key, value in args.items():
            if value is not None:
                pius[key] = value

        pius['updated_at'] = utc_now
        PUT_IN_USE_COLLECTION.replace_one({'_id': ObjectId(piu_id)}, pius)

        response = {"message": "Your data has been updated successfully",}
        return response, 200
        
class P_in_useDelete(Resource):
    def delete(self, user_id, lab_name, piu_id):
        try:
            org_name = get_org_name(user_id)
            PUT_IN_USE_COLLECTION = client[org_name + '_db'][lab_name + '_piu']
        except ValueError as e:
            abort(404, message=str(e))
        PUT_IN_USE_COLLECTION.delete_one({'_id': ObjectId(piu_id)})
        return jsonify({"message": f"Item has been deleted successfully"})

class P_in_useGetOne(Resource):
    def get(self, user_id, lab_name, piu_id):
        try:
            org_name = get_org_name(user_id)
            PUT_IN_USE_COLLECTION = client[org_name + '_db'][lab_name + '_piu']
        except ValueError as e:
            abort(404, message=str(e))
        try:
            pius = PUT_IN_USE_COLLECTION.find_one({'_id': ObjectId(piu_id)})
            if not pius:
                abort(404, message="Put in use ID not found")
            # for result in result:
            response = {
                    "_id":str(pius['_id']),
                    "created at":pius['created at'].strftime("%Y-%m-%d %H:%M:%S"),
                    "user":pius['user'],
                    "item":pius['item'],
                    "bench":pius['bench'],
                    "machine":pius['machine'],
                    "lot_numb": pius["lot_numb"],
                    "quantity":pius['quantity'],
                    "description":pius['description']}
            return response, 200
        except Exception as e:
            return {"message": "Error occured while fetching put in use item", "error": str(e)}

class P_in_useGetAll(Resource):
    def get(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            PUT_IN_USE_COLLECTION = client[org_name + '_db'][lab_name + '_piu']
        except ValueError as e:
            abort(404, message=str(e))

        pius = list(PUT_IN_USE_COLLECTION.find())
        if not pius:
            abort(404, message="No Items put in use")
        utc_now = datetime.now()
        piu_list = [{
            "_id": str(piu['_id']),
            "created at": piu.get('created at').strftime("%Y-%m-%d %H:%M:%S") if 'created at' in piu else None,
            "user": piu.get('user', 'Unknown User'),
            "item": piu.get('item', 'Unknown Item'),
            "bench": piu.get('bench', 'Unknown Bench'),
            "machine": piu.get('machine', 'Unknown Machine'),
            "lot_numb": piu.get("lot_numb", 'Unknown Lot Number'),
            "quantity": piu.get('quantity', 0),
            "description": piu.get('description', 'No Description')
        } for piu in pius]

        response = {"piu": piu_list}
        return response, 200

        

