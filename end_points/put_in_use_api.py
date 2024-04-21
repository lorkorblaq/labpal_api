from flask import jsonify, request
from flask_restful import Resource, reqparse, abort, fields, marshal_with
from bson import ObjectId
from datetime import datetime, timedelta
from engine import db_clinical

PUT_IN_USE_COLLECTION = db_clinical['put in use']
ITEMS_COLLECTION = db_clinical['items']
USERS_COLLECTION = db_clinical['users']

put_in_use_parser = reqparse.RequestParser()

put_in_use_parser.add_argument("item", type=str, help="Item is required", required=False)
put_in_use_parser.add_argument("bench", type=str, help="Bench is required", required=False)
put_in_use_parser.add_argument("machine", type=str, help="Machine is required", required=False)
put_in_use_parser.add_argument("quantity", type=int, help="Quantity is required", required=False)
put_in_use_parser.add_argument("description", type=str, help="Description is required", required=False)

class P_in_usePush(Resource):
    def post(self, user_id):
        try:
            utc_now = datetime.now()
            wat_time = utc_now + timedelta(hours=1)
            args = put_in_use_parser.parse_args()
            user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
            item = ITEMS_COLLECTION.find_one({'item': args['item']})
            bench = item.get('bench')
            name = user.get('firstname') + ' ' + user.get('lastname')
            if not user:
                return {"message": "User does not exist, kindly contact Lorkorblaq"}, 400
            if not item:
                return {"message": "Item does not exist, kindly contact Lorkorblaq"}, 400

            # Get the item's _id to use as a reference
            # item_id = str(item['_id'])

            # Insert into put_in_use collection
            piu = {
                'user': name,
                'item': args["item"],
                'bench': bench,
                'machine': args["machine"],
                'quantity': args["quantity"],
                'description': args["description"],
                'created at': wat_time,
            }
            inserted_id = PUT_IN_USE_COLLECTION.insert_one(piu).inserted_id 
            inserted_id = str(inserted_id)           
            response = {
                "message": "Item put in use successfully",
                'piu_id': inserted_id
            }
            return response, 200
        except Exception as e:
            return {"message": "Error occured while pushing put in use item", "error": str(e)}

class P_in_usePut(Resource):
    def get_piu_by_id(self, piu_id):
        result = PUT_IN_USE_COLLECTION.find_one({'_id': ObjectId(piu_id)})
        if not result:
            abort(404, message="This put in use item was not found")
        return result
    
    def put(self, piu_id):
        utc_now = datetime.utcnow()
        wat_time = utc_now + timedelta(hours=1)
        args = put_in_use_parser.parse_args()
        item = ITEMS_COLLECTION.find_one({'item': args['item']})

        # if not item:
        #     abort(404, message="Item not found, kindly contact Lorkorblaq")
        
        result = self.get_piu_by_id(piu_id)
        # item_id = item['_id']
        # print(item_id)
        # result['item'] = item_id
        for key, value in args.items():
            if value is not None:
                result[key] = value

        result['updated_at'] = wat_time
        PUT_IN_USE_COLLECTION.replace_one({'_id': ObjectId(piu_id)}, result)

        response = {"message": "Your data has been updated successfully",}
        return response, 200
        
class P_in_useDelete(Resource):
    def get_piu_by_id(self, piu_id):
        result = PUT_IN_USE_COLLECTION.find_one({'_id': ObjectId(piu_id)})
        if not result:
            abort(404, message="This put in use item was not found")
        return result
    def delete(self, piu_id):
        result = self.get_piu_by_id(piu_id)
        PUT_IN_USE_COLLECTION.delete_one({'_id': ObjectId(piu_id)})
        return jsonify({"message": f"Item has been deleted successfully"})

class P_in_useGetOne(Resource):
    def get(self, piu_id):
        try:
            result = PUT_IN_USE_COLLECTION.find_one({'_id': ObjectId(piu_id)})
            if not result:
                abort(404, message="Item not found")
            # for result in result:
            response = {
                    "_id":str(result['_id']),
                    "created at":result['created at'].strftime("%Y-%m-%d %H:%M:%S"),
                    "user":result['user'],
                    "item":result['item'],
                    "bench":result['bench'],
                    "machine":result['machine'],
                    "quantity":result['quantity'],
                    "description":result['description']}
            return response, 200
        except Exception as e:
            return {"message": "Error occured while fetching put in use item", "error": str(e)}

class P_in_useGetAll(Resource):
    def get(self):
        
        results = list(PUT_IN_USE_COLLECTION.find())
        if not results:
            abort(404, message="No Items put in use")
        piu_list = [{
                "_id":str(result['_id']),
                "created at":result['created at'].strftime("%Y-%m-%d %H:%M:%S"),
                "user":result['user'],
                "item":result['item'],
                "bench":result['bench'],
                "machine":result['machine'],
                "quantity":result['quantity'],
                "description":result['description']
                }for result in results]
        response = {"piu": piu_list}
        return response, 200
        

