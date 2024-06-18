from flask import jsonify, request
from flask_restful import Resource, reqparse, abort, fields, marshal_with
from bson import ObjectId
from datetime import datetime, timedelta
from engine import db_clinical

CHANNELS_COLLECTION = db_clinical['channels']
ITEMS_COLLECTION = db_clinical['items']
LOT_EXP_COLLECTION = db_clinical['lot Exp']
USERS_COLLECTION = db_clinical['users']

channels_parser = reqparse.RequestParser()

channels_parser.add_argument("id", type=int, help="User ID is required", required=False)
channels_parser.add_argument("item", type=str, help="Item is required", 
required=False)
channels_parser.add_argument("lot_numb", type=str, help="Lot is required", 
required=False)
channels_parser.add_argument("direction", type=str, help="Direction is required", required=False)
channels_parser.add_argument("location", type=str, help="Location is required", required=False)
channels_parser.add_argument("quantity", type=int, help="Quantity is required", required=False)
channels_parser.add_argument("description", type=str, required=False)
def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Not a valid date: '{0}'.".format(s))

channels_parser.add_argument("expiration", type=valid_date, required=False)

class ChannelPush(Resource):
    def post(self, user_id):
        try:
            utc_now = datetime.now()
            wat_time = utc_now + timedelta(hours=1)
            args = channels_parser.parse_args()
            user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
            item = ITEMS_COLLECTION.find_one({'item': args['item']})
            name = user.get('firstname') + ' ' + user.get('lastname')
            channel = {
                    "user":  name, 
                    "item": args["item"], 
                    "lot_numb": args["lot_numb"],
                    "direction": args["direction"],
                    "location": args["location"],
                    "quantity": args["quantity"],
                    "description": args["description"],
                    'created at': wat_time,
                }
            if not user:
                return {"message": "User does not exist, kindly contact Lorkorblaq"}, 400
            if not item:
                return {"message": "Item does not exist, kindly contact Lorkorblaq"}, 400
            # try:
            #     if not lot_exp:
            #         lot_exp = {
            #             "lot": args["lot"],
            #             "expiration date": args["expiration"],
            #             "quantity": args["quantity"],
            #             "created at": wat_time
            #         }
            #         LOT_EXP_COLLECTION.insert_one(lot_exp)
            #         CHANNELS_COLLECTION.insert_one(channel)
            #         response = {
            #             "message": "The lot and Channel has been added successfully",
            #         }
            #         return response, 200
            # except:
            inserted_id = CHANNELS_COLLECTION.insert_one(channel).inserted_id
            inserted_id = str(inserted_id)
            response = {
                "message": "Channel created successfully",
                "channel_id": inserted_id
            }
            return response, 200
        except Exception as e:
            return {"message": "Error occured while pushing channel item", "error": str(e)}

class ChannelPut(Resource):
    def get_channel_by_id(self, channel_id):
        result = CHANNELS_COLLECTION.find_one({'_id': ObjectId(channel_id)})
        if not result:
            abort(404, message="This channel was not found")
        return result
    
    def put(self, channel_id):
        utc_now = datetime.utcnow()
        wat_time = utc_now + timedelta(hours=1)
        args = channels_parser.parse_args()
        item = ITEMS_COLLECTION.find_one({'item': args['item']})

        # if not item:
        #     abort(404, message="Item not found, kindly contact Lorkorblaq")
        
        result = self.get_channel_by_id(channel_id)
        # item_id = item['_id']
        # print(item_id)
        # result['item'] = item_id
        for key, value in args.items():
            if value is not None:
                result[key] = value

        result['updated_at'] = wat_time
        CHANNELS_COLLECTION.replace_one({'_id': ObjectId(channel_id)}, result)

        response = {"message": "Your data has been updated successfully",}
        return response, 200

class ChannelDel(Resource):
    def get_channel_by_id(self, channel_id):
        result = CHANNELS_COLLECTION.find_one({'_id': ObjectId(channel_id)})
        if not result:
            abort(404, message="This channel was not found")
        return result
    def delete(self, channel_id):
        result = self.get_channel_by_id(channel_id)
        CHANNELS_COLLECTION.delete_one({'_id': ObjectId(channel_id)})
        return jsonify({"message": "Item has been deleted successfully"})

class ChannelGetOne(Resource):
    def get(self, channel_id):
        try:
            result = CHANNELS_COLLECTION.find_one({'_id': ObjectId(channel_id)})
            if not result:
                abort(404, message="Item not found")
            # for result in result:
            response = {
                    "_id":str(result['_id']),
                    "created at":result['created at'].strftime("%Y-%m-%d %H:%M:%S"),
                    "user":result['user'],
                    "item":result['item'],
                    "lot_numb": result["lot_numb"],
                    "direction": result["direction"],
                    "location": result["location"],
                    "quantity":result['quantity'],
                    "description":result['description']}
            return response, 200
        except Exception as e:
            return {"message": "Error occured while fetching put in use item", "error": str(e)}

class ChannelGetAll(Resource):
    def get(self):
        results = list(CHANNELS_COLLECTION.find())
        if not results:
            abort(404, message="No channel")
        channel_list = [{
            "_id":str(result['_id']),
                "created at":result['created at'].strftime("%Y-%m-%d %H:%M:%S"),
                "user":result['user'],
                "item":result['item'],
                "lot_numb": result["lot_numb"],
                "direction": result["direction"],
                "location": result["location"],
                "quantity":result['quantity'],
                "description":result['description']
                }for result in results]
        response = {"channels": channel_list}
        return response, 200
        

