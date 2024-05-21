from flask_restful import Resource, abort, reqparse
from flask import jsonify, make_response
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
    ITEMS_COLLECTION.find(query, { "bench":1, "item":1, "in stock":1, "tests/day":1, "tests/vial":1 })
    pipeline = [
            # Match documents based on the bench field
            {"$match": query},
            # Project the fields needed for calculations
            {"$project": {
                "bench":1,
                "item":1,
                "in stock":1,
                "total_tests_in_stock": {"$multiply": ["$in stock", "$tests/vial"]},
                "tests_per_day": {"$ceil":"$tests/day"},
                "tests/vial":1
            }},
            {"$addFields": {
                # "quantity_needed": {"$ceil": {"$divide": [days, "$tests_per_day"]}},
                "total_tests_in_stock": {"$multiply": ["$in stock", "$tests/vial"]},
                "total_days_to_last": {"$ceil": {"$divide": ["$total_tests_in_stock", "$tests_per_day"]}},
            
                "quantity_test_requested": {"$multiply": ["$tests_per_day", days]},
                # "total_days_to_last": "$total_days_to_last",  # Include total_days_last in the final result
                "total_tests_in_stock": "$total_tests_in_stock"
            }}
        ]
        # Execute the aggregation pipeline
    result = list(ITEMS_COLLECTION.aggregate(pipeline))

     # Convert MongoDB documents to dictionaries
    result_dicts = []
    for item in result:
        if item.get("total_tests_in_stock") < item.get("quantity_test_requested"):
            item["amount_needed"] = item.get("quantity_test_requested") - item.get("total_tests_in_stock")
            amount_needed = math.ceil(item.get("amount_needed")/item.get("tests/vial"))
            # return amount_needed
        else:
            item["amount_needed"] = 0
            amount_needed = 0
            
        result_dict = {
            "bench": item.get("bench", ""),
            "in_stock": item.get("in stock", ""),
            "item": item.get("item", ""),
            "tests_per_day": item.get("tests/day", ""),
            "total_tests_in_stock": item.get("total_tests_in_stock", ""),
            "tests_per_day": item.get("tests_per_day", ""),
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
        response = results
        # for result in results:

        response = {"requested": results,}
        return response, 200