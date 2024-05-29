from flask_restful import Resource, abort, reqparse
from flask import jsonify, make_response, request
from bson import json_util, ObjectId
from engine import db_clinical
import math


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

class ItemsBulkPush(Resource):
    def post(self):
        try:
            json_data = request.get_json()
            if not json_data:
                abort(400, message="No JSON data provided")
            
            # Ensure the required columns are present
            required_columns = {'item', 'in stock', 'tests/vial', 'vials/pack', 'reOrderLevel', 'class', 'category', 'tests/day', 'bench'}

            for entry in json_data:
                if not required_columns.issubset(entry.keys()):
                    abort(400, message=f"JSON data must contain keys: {', '.join(required_columns)}")
            
            # Insert data into the MongoDB collection
            ITEMS_COLLECTION.insert_many(json_data)
            
            return make_response(jsonify({"message": "Data imported successfully"}), 201)
        
        except Exception as e:
            abort(500, message=str(e))

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
 
def requiste(bench, days, categories):
    query = {}
    if bench:
        query["bench"] = bench
    if categories:
        query["category"] = {"$in": categories}
    print(query)
    
    pipeline = [
        # Match documents based on the bench field
        {"$match": query},
        # Project the fields needed for calculations and convert to numeric types
        {"$project": {
            "bench": 1,
            "item": 1,
            "in_stock": {"$toDouble": "$in stock"},
            "tests_per_day": {"$toDouble": "$tests/day"},
            "tests_per_vial": {"$toDouble": "$tests/vial"}
        }},
        {"$addFields": {
            "total_tests_in_stock": {"$multiply": ["$in_stock", "$tests_per_vial"]},
            "total_days_to_last": {"$ceil": {"$divide": ["$total_tests_in_stock", "$tests_per_day"]}},
            "quantity_test_requested": {"$multiply": ["$tests_per_day", days]}
        }}
    ]
    
    # Execute the aggregation pipeline
    result = list(ITEMS_COLLECTION.aggregate(pipeline))
    
    # Convert MongoDB documents to dictionaries
    result_dicts = []
    for item in result:
        if item.get("total_tests_in_stock") < item.get("quantity_test_requested"):
            item["amount_needed"] = item.get("quantity_test_requested") - item.get("total_tests_in_stock")
            amount_needed = math.ceil(item.get("amount_needed") / item.get("tests_per_vial"))
        else:
            item["amount_needed"] = 0
            amount_needed = 0

        result_dict = {
            "bench": item.get("bench", ""),
            "in_stock": item.get("in_stock", ""),
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

class ItemsRequisite(Resource):
    def post(self, ):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument("bench", type=str, help="Bench is required", required=True)
        req_parser.add_argument("categories", type=str, action='append', required=False)
        req_parser.add_argument("days", type=int, help="Quantity is required", required=True)
        args = req_parser.parse_args()

        bench = args['bench']
        days = args['days']
        categories = args.get('categories', [])  # Get list of categories or empty list if not provided        
        results = requiste(bench, days, categories)
        print(results)
        response = results
        # for result in results:

        response = {"requested": results,}
        return response, 200

class ItemsDeleteResource(Resource):
    def delete(self):
        try:
            result = ITEMS_COLLECTION.delete_many({})
            if result.deleted_count == 0:
                abort(404, message="No items to delete")
            return make_response(jsonify({"message": "All items deleted successfully"}), 200)
        except Exception as e:
            abort(500, message=str(e))