from flask_restful import Resource, abort, reqparse
from flask import jsonify, make_response, request
from bson import  ObjectId
from engine import  client, org_users_db, get_org_name
from flask_restful import reqparse
import math

USERS_COLLECTION = org_users_db['users']
ORG_COLLECTION = org_users_db['organisations']
item_parser = reqparse.RequestParser()

item_parser = reqparse.RequestParser()

# String fields
item_parser.add_argument("bench", type=str, help="Bench is required", required=False)
item_parser.add_argument("category", type=str, help="Category is required", required=False)
item_parser.add_argument("item", type=str, help="Item is required", required=False)
item_parser.add_argument("class", type=str, help="Class is required", required=False)
item_parser.add_argument("direction", type=str, help="direction is required", required=False)

# counts/levels
item_parser.add_argument("quantity", type=float, help="Quantity in store unit required", required=False)
item_parser.add_argument("reOrderLevel", type=int, help="Reorder level is required", required=False)

# Units
item_parser.add_argument("baseUnit", type=str, help="Base unit is required", required=False)
item_parser.add_argument("storeUnit", type=str, help="Store unit is required", required=False)
item_parser.add_argument("purchaseUnit", type=str, help="Purchase unit is required", required=False)

# Ratios and pricing: handle as float or Decimal
item_parser.add_argument("baseUnit/day", type=float, help="Base unit per day is required", required=False)
item_parser.add_argument("baseUnit/storeUnit", type=float, help="Base unit per store unit is required", required=False)
item_parser.add_argument("storeUnit/purchaseUnit", type=float, help="Store unit per purchase unit is required", required=False)
item_parser.add_argument("price/purchaseUnit", type=float, help="Price per purchase unit is required", required=False)
        
# vials/pack=storeUnit/purchaseUnit, tests/vial=baseUnit/storeUnit, tests/day = baseUnit/day

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
        # Match documents based on the bench field and categories
        {"$match": query},
        
        # Project the fields needed for calculations and convert to numeric types
        {"$project": {
            "bench": 1,
            "item": 1,
            "baseUnit":1,
            "storeUnit":1,
            "baseUnit/storeUnit":1,
            "quantity": {"$toDouble": "$quantity"},
            "baseUnit_per_day": {"$toDouble": "$baseUnit/day"},
            "baseUnit_per_storeUnit": {"$toDouble": "$baseUnit/storeUnit"}
        }},
        
        # Calculate total_baseUnit_in_store and quantity_baseUnit_requested
        {"$addFields": {
            "total_baseUnit_in_store": {
                "$cond": {
                    "if": {"$and": [{"$gt": ["$quantity", 0]}, {"$gt": ["$baseUnit_per_storeUnit", 0]}]},
                    "then": {"$multiply": ["$quantity", "$baseUnit_per_storeUnit"]},
                    "else": None
                }
            },
            "quantity_baseUnit_requested": {
                "$multiply": ["$baseUnit_per_day", days]
            }
        }},
        
        # Calculate total days the item will last based on daily consumption
        {"$addFields": {
            "total_days_to_last": {
                "$cond": {
                    "if": {"$gt": ["$baseUnit_per_day", 0]},
                    "then": {"$ceil": {"$divide": ["$total_baseUnit_in_store", "$baseUnit_per_day"]}},
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
        if item.get("total_baseUnit_in_store") is not None:
            if item.get("total_baseUnit_in_store") < item.get("quantity_baseUnit_requested"):
                item["amount_needed"] = item.get("quantity_baseUnit_requested") - item.get("total_baseUnit_in_store")
                amount_needed = math.ceil(item.get("amount_needed") / item.get("baseUnit_per_storeUnit"))
            else:
                item["amount_needed"] = 0
                amount_needed = 0

            result_dict = {
                "bench": item.get("bench", ""),
                "quantity": item.get("quantity", ""),
                "item": item.get("item", ""),
                "baseUnit": item.get("baseUnit",""),
                "storeUnit": item.get("storeUnit",""),
                "baseUnit/storeUnit": item.get("baseUnit/storeUnit",""),
                "baseUnit_per_day": item.get("baseUnit_per_day", ""),
                "total_baseUnit_in_store": item.get("total_baseUnit_in_store", ""),
                "quantity_baseUnit_requested": item.get("quantity_baseUnit_requested", ""),
                "total_days_to_last": item.get("total_days_to_last", ""),
                "amount_needed": amount_needed
            }
            result_dicts.append(result_dict)
    
    # Return the result as JSON
    return result_dicts

class ItemsGet(Resource):
    def get(self, user_id, lab_name):  
        try:
            # Retrieve organization name based on user ID
            orgname = get_org_name(user_id)
            # Access the specific items collection for the lab in the user's database
            ITEMS_COLLECTION = client[orgname+'_db'][lab_name+'_items']

        except ValueError as e:
            # If a ValueError occurs, return a 404 error with the exception message
            abort(404, message=str(e))
        
        # Fetch all items from the collection and store them in a list
        results = list(ITEMS_COLLECTION.find())
        if not results:
            # If no items are found, return a 404 error with a custom message
            abort(404, message="No Item Available")
        
        item_list = []
        # Loop through the results and convert each item's ObjectId to a string
        # This is necessary for proper JSON serialization
        for result in results:
            result["_id"] = str(result["_id"])
            item_list.append(result)
        
        # Create a dictionary containing the list of items to return as the response
        response_data = {"items": item_list}
        # Return the JSON response along with a 200 OK status code
        return response_data, 200

class ItemsBulkPush(Resource):
    def post(self, user_id, lab_name):
        try:
            # Retrieve the organization name based on user ID
            orgname = get_org_name(user_id)
            # Access the specific items collection for the lab in the user's database
            ITEMS_COLLECTION = client[orgname+'_db'][lab_name+'_items']
        except ValueError as e:
            # If a ValueError occurs (e.g., invalid user ID), return a 404 error with the exception message
            abort(404, message=str(e))

        # Get the JSON data from the request
        json_data = request.get_json()
        if not json_data:
            # If no JSON data is provided in the request, return a 400 error
            abort(400, message="No JSON data provided")

        # Define the required columns that must be present in the input data
        required_columns = {'item', 'bench', 'category', 'class', 'quantity', 
                            'reOrderLevel', 'baseUnit/day', 'baseUnit', 
                            'storeUnit', 'purchaseUnit', 'baseUnit/storeUnit', 
                            'storeUnit/purchaseUnit', 'price/purchaseUnit'}

        # Check each entry in the provided JSON data to ensure all required columns are present
        for entry in json_data:
            if not required_columns.issubset(entry.keys()):
                # If any required column is missing, return a 400 error with a detailed message
                abort(400, message=f"Your data must contain the columns: {', '.join(required_columns)}")

        try:
            # Get all item names in the bulk data
            item_names = [entry['item'] for entry in json_data]

            # Check for existing items in the collection that match the item names
            existing_items = ITEMS_COLLECTION.find({'item': {'$in': item_names}})
            existing_item_names = [item['item'] for item in existing_items]

            # Filter out items that already exist in the collection
            items_to_insert = [entry for entry in json_data if entry['item'] not in existing_item_names]

            if not items_to_insert:
                # If all items are duplicates, return a message indicating no data was inserted
                return make_response(jsonify({"message": "No new items to insert. Items already exist."}), 200)

            # Insert only the new items into the MongoDB collection
            ITEMS_COLLECTION.insert_many(items_to_insert)

            # Return a success message with a count of how many new items were inserted
            return make_response(jsonify({
                "message": f"{len(items_to_insert)} new items inserted successfully",
                "skipped_items due to duplication": existing_item_names
            }), 201)

        except Exception as e:
            # If an error occurs during the insertion process, return a 500 error with the exception message
            abort(500, message=str(e))

class ItemsPush(Resource):
    def post(self, user_id, lab_name):
        try:
            # Retrieve the organization name based on the user ID
            org_name = get_org_name(user_id)
            # Access the specific items collection for the lab in the user's database
            ITEMS_COLLECTION = client[org_name + '_db'][lab_name + '_items']
        except ValueError as e:
            # If a ValueError occurs (e.g., invalid user ID), return a 404 error with the exception message
            abort(404, message=str(e))

        # Parse the incoming request arguments (assuming item_parser is predefined)
        args = item_parser.parse_args()

        # Check if the user exists in the users collection
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        if not user:
            # If the user doesn't exist, return a 400 error with a message
            return {"message": "User does not exist, kindly contact Lorkorblaq"}, 400
        elif not org_name:
            # If the organization doesn't exist, return a 400 error
            return {"message": "Organisation does not exist, kindly contact Lorkorblaq"}, 400

        # Define the required fields for the item
        required_fields = {'item', 'bench', 'category', 'class', 'quantity', 
                           'reOrderLevel', 'baseUnit/day', 'baseUnit', 
                           'storeUnit', 'purchaseUnit', 'baseUnit/storeUnit', 
                           'storeUnit/purchaseUnit', 'price/purchaseUnit'}

        # Retrieve the labs access for the user (assuming user has access to labs)
        labs = user.get('labs_access')

        # Create the item dictionary using the parsed arguments
        items_list = {
            "item": args['item'],
            "bench": args['bench'],
            "category": args['category'],
            "class": args['class'],
            "quantity": args['quantity'],
            "reOrderLevel": args['reOrderLevel'],
            "baseUnit": args['baseUnit'],
            "storeUnit": args['storeUnit'],
            "purchaseUnit": args['purchaseUnit'],
            "baseUnit/day": args['baseUnit/day'],
            "baseUnit/storeUnit": args['baseUnit/storeUnit'],
            "storeUnit/purchaseUnit": args['storeUnit/purchaseUnit'],
            "price/purchaseUnit": args['price/purchaseUnit']
        }

        # Ensure all required fields are present in the items_list
        for x in items_list:
            if not required_fields.issubset(items_list.keys()):
                # If any required field is missing, return a 400 error with a detailed message
                abort(400, message=f"Your data must contain the fields: {', '.join(required_fields)}")

        # Check if an item with the same name already exists in the collection
        existing_item = ITEMS_COLLECTION.find_one({'item': args['item']})
        if existing_item:
            # If an item with the same name is found, return a 400 error
            abort(400, message=f"An item with the name '{args['item']}' already exists. Please use a unique item name.")
        
        try:
            # Insert the item into the MongoDB collection and retrieve the inserted ID
            inserted_id = ITEMS_COLLECTION.insert_one(items_list).inserted_id
            inserted_id = str(inserted_id)  # Convert ObjectId to string for JSON serialization

            # Create a response message with the inserted item's ID
            response = {
                "message": "Item created successfully",
                "item_id": inserted_id
            }
            return response, 201  # Return the response with a 201 Created status
        except Exception as e:
            # Handle any errors that occur during the insertion
            return {"message": "Error occurred while pushing item", "error": str(e)}

class ItemsPut(Resource):
    def put(self, user_id, lab_name):
        try:
            # Retrieve the organization name based on the user ID
            orgname = get_org_name(user_id)
            # Access the specific items collection for the lab in the user's database
            ITEMS_COLLECTION = client[orgname+'_db'][lab_name+'_items']
        except ValueError as e:
            # If a ValueError occurs (e.g., invalid user ID), return a 404 error with the exception message
            abort(404, message=str(e))
        
        # Parse the incoming request arguments (assuming item_parser is predefined)
        args = item_parser.parse_args()
        
        # Check if the 'item' argument is provided in the request
        if not args['item']:
            abort(404, message="Item not provided, kindly contact Lorkorblaq")
        
        # Retrieve the item document from the collection
        item = ITEMS_COLLECTION.find_one({'item': args['item']})
        
        # Check if the item exists in the collection
        if not item:
            abort(404, message="The item you are about to update doesn't exist")
        
        # Get the current quantity of the item
        current_quantity = item.get('quantity', 0)

        # If the direction is "To", decrease the quantity by the specified amount
        if args['direction'] == "To":
            # Ensure the new quantity will not be negative
            if current_quantity == 0:
                abort(400, message="Item is already at zero quantity, cannot reduce further")
            elif current_quantity - args['quantity'] < 0:
                abort(400, message="Quantity will result in a negative value and can't be allowed")
            
            
            # Update the item's quantity by decreasing it
            new_value = {'$inc': {'quantity': -args['quantity']}}
            ITEMS_COLLECTION.update_one({'item': args['item']}, new_value)
        
        # If the direction is "From", increase the quantity by the specified amount
        elif args['direction'] == "From":
            # Update the item's quantity by increasing it
            new_value = {'$inc': {'quantity': args['quantity']}}
            ITEMS_COLLECTION.update_one({'item': args['item']}, new_value)
        
        # Return a success message after the update is applied
        response = {"message": "Your data has been updated successfully"}
        return response, 200  # Return the response with a 200 OK status

class ItemsRequisite(Resource):
    def post(self, user_id, lab_name):  
        # Initialize the request parser to handle incoming POST request data    
        req_parser = reqparse.RequestParser()

        # Define required and optional arguments for the request
        req_parser.add_argument("bench", type=str, help="Bench is required", required=True)
        req_parser.add_argument("categories", type=str, action='append', required=False)
        req_parser.add_argument("days", type=int, help="Quantity is required", required=True)
        
        # Parse the arguments from the request
        args = req_parser.parse_args()

        # Extract the values from the parsed arguments
        bench = args['bench']
        days = args['days']
        # Get the list of categories, or an empty list if none are provided
        categories = args.get('categories', []) 

        # Call the `requiste` function with the provided data to perform the requisite calculation
        results = requiste(bench, days, categories, user_id, lab_name)
        
        # Debugging statement to print the results (can be removed or logged)
        print(results)

        # Create a response dictionary to send back to the client
        response = {"requested": results}

        # Return the response with a 200 OK status
        return response, 200
    
class ItemsDeleteResource(Resource):
    def delete(self, user_id, lab_name):
        try:
            # Retrieve the organization name based on the user ID
            orgname = get_org_name(user_id)
            # Access the items collection for the given lab in the user's database
            ITEMS_COLLECTION = client[orgname+'_db'][lab_name+'_items']

        except ValueError as e:
            # If an error occurs (e.g., invalid user ID), return a 404 error with the exception message
            abort(404, message=str(e))
        
        try:
            # Delete all items in the items collection
            result = ITEMS_COLLECTION.delete_many({})
            
            # If no items were deleted, return a 404 error
            if result.deleted_count == 0:
                abort(404, message="No items to delete")
            
            # If items were deleted, return a success message
            return make_response(jsonify({"message": "All items deleted successfully"}), 200)
        except Exception as e:
            # Handle any other errors that occur during deletion and return a 500 error
            abort(500, message=str(e))

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