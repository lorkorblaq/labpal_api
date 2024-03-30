from flask_restful import Resource, abort, reqparse
from flask import jsonify, make_response
from bson import json_util, ObjectId
from engine import db_clinical

ITEMS_COLLECTION = db_clinical['items']
item_parser = reqparse.RequestParser()
item_parser.add_argument("item", type=str, help="item is required", required=True)
item_parser.add_argument("direction", type=str, help="Direction is required", required=True)
item_parser.add_argument("in stock", type=int, help="Quantity is required", required=True)

class ItemsResource(Resource):
    def get(self):    
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

class ItemsPut(Resource):
    def put(self):
        # utc_now = datetime.utcnow()
        # wat_time = utc_now + timedelta(hours=1)
        args = item_parser.parse_args()
        if not args['item']:
            abort(404, message="Item not found, kindly contact Lorkorblaq")
        filter = {'item': args['item']}
        if args['direction'] == "To": 
            new_value = {'$inc': {'in stock': -args['in stock']}}
            ITEMS_COLLECTION.update_one(filter, new_value)
        elif args['direction'] == "From":
            new_value = {'$inc': {'in stock': args['in stock']}}
            ITEMS_COLLECTION.update_one(filter, new_value)
        response = {"message": "Your data has been updated successfully",}
        return response, 200
        
