from flask import jsonify, request
from flask_restful import Resource, reqparse, abort, fields, marshal_with
from bson import ObjectId
from datetime import datetime, timedelta
from engine import db_clinical, client, org_users_db, get_org_name
from werkzeug.exceptions import HTTPException

# CHANNELS_COLLECTION = db_clinical['channels']
# ITEMS_COLLECTION = db_clinical['items']

USERS_COLLECTION = org_users_db['users']
ORG_COLLECTION = org_users_db['organisations']

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
    def post(self, user_id, lab_name):
        try:
            # Fetch organization and collections
            org_name = get_org_name(user_id)
            ITEMS_COLLECTION = client[org_name + '_db'][lab_name + '_items']
            CHANNELS_COLLECTION = client[org_name + '_db'][lab_name + '_channels']
            LOT_EXP_COLLECTION = client[org_name + '_db'][lab_name + '_lot_exp']
        except ValueError as e:
            abort(404, message=str(e))

        try:
            # Get the current time
            utc_now = datetime.now()
            wat_now = utc_now + timedelta(hours=1)
            
            # Parse arguments and get user information
            args = channels_parser.parse_args()
            user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
            
            if not user:
                abort(400, message="User does not exist, kindly contact Lorkorblaq")
            
            if not org_name:
                abort(400, message="Organisation does not exist, kindly contact Lorkorblaq")
            
            # Verify lab access
            labs = user.get('labs_access')
            if lab_name not in labs:
                abort(403, message="You do not have access to this lab")

            # Fetch item from the collection
            item = ITEMS_COLLECTION.find_one({'item': args['item']})
            if not item:
                abort(400, message="Item does not exist, kindly contact Lorkorblaq")
            
            current_quantity = item.get('quantity', 0)

            # Check the conditions for "To" direction first
            if args['direction'] == "To":
                if current_quantity == 0:
                    abort(400, message="Item is already at zero quantity, cannot reduce further")
                elif current_quantity - args['quantity'] < 0:
                    abort(400, message="Quantity will result in a negative value and can't be allowed")

            # Prepare the channel data
            name = user.get('firstname') + ' ' + user.get('lastname')
            channel = {
                "user": name, 
                "item": args["item"], 
                "lot_numb": args["lot_numb"],
                "direction": args["direction"],
                "location": args["location"],
                "quantity": args["quantity"],
                "description": args["description"],
                'created at': wat_now,
            }
            
            # Insert the channel after validation passes
            inserted_id = CHANNELS_COLLECTION.insert_one(channel).inserted_id
            inserted_id = str(inserted_id)

            # Update the item and lot quantity based on the direction
            if args['direction'] == 'To':
                # Update the item's quantity by decreasing it
                ITEMS_COLLECTION.update_one(
                    {'item': args['item']},
                    {'$inc': {'quantity': -args['quantity']}}
                )
                # Update the lot expiry collection as well
                LOT_EXP_COLLECTION.update_one(
                    {'lot_numb': args['lot_numb']},
                    {'$inc': {'quantity': -args['quantity']}}
                )
            elif args['direction'] == 'From':
                # Update the item's quantity by increasing it
                ITEMS_COLLECTION.update_one(
                    {'item': args['item']},
                    {'$inc': {'quantity': args['quantity']}}
                )
                LOT_EXP_COLLECTION.update_one(
                    {'lot_numb': args['lot_numb']},
                    {'$inc': {'quantity': args['quantity']}}
                )

            # Return success response
            response = {
                "message": "Channel created successfully",
                "channel_id": inserted_id
            }
            return response, 200
        
        except HTTPException as e:
            # Let HTTP exceptions (abort) pass through without being caught
            raise e
        except Exception as e:
            # Handle any other error that occurs after validation
            return {"message": "Error occurred while pushing channel item", "error": str(e)}



class ChannelPut(Resource):    
    def put(self, user_id, lab_name, channel_id):
        try:
            org_name = get_org_name(user_id)
            ITEMS_COLLECTION = client[org_name + '_db'][lab_name + '_items']
            CHANNELS_COLLECTION = client[org_name + '_db'][lab_name + '_channels']
        except ValueError as e:
            abort(404, message=str(e))

        utc_now = datetime.now()
        args = channels_parser.parse_args()
        channel = CHANNELS_COLLECTION.find_one({'_id': ObjectId(channel_id)})
        if not channel:
            abort(404, message="Channel not found")

        # Retrieve the current quantity before updates
        current_quantity = channel.get('quantity', 0)
        new_quantity = args.get('quantity')

        if new_quantity is not None:
            try:
                new_quantity = float(new_quantity)
                # Calculate the difference
                quantity_diff = new_quantity - current_quantity

                if channel['direction'] == 'To':
                    ITEMS_COLLECTION.update_one({'item': channel['item']}, {'$inc': {'quantity': -quantity_diff}})
                elif channel['direction'] == 'From':
                    ITEMS_COLLECTION.update_one({'item': channel['item']}, {'$inc': {'quantity': quantity_diff}})
            except ValueError:
                abort(400, message="Quantity must be a valid number")

        # Update the channel with new values
        for key, value in args.items():
            if value is not None:
                # Convert empty strings to None
                if isinstance(value, str) and value.strip() == '':
                    value = None
                channel[key] = value

        channel['updated_at'] = utc_now
        CHANNELS_COLLECTION.replace_one({'_id': ObjectId(channel_id)}, channel)

        response = {"message": "Your data has been updated successfully"}
        return response, 200
    
class ChannelDel(Resource):
     def delete(self, user_id, lab_name, channel_id):
        try:
            org_name = get_org_name(user_id)
            ITEMS_COLLECTION = client[org_name+'_db'][lab_name+'_items']
            CHANNELS_COLLECTION = client[org_name+'_db'][lab_name+'_channels']
        except ValueError as e:
            abort(404, message=str(e))

        CHANNELS_COLLECTION.delete_one({'_id': ObjectId(channel_id)})
        return jsonify({"message": "Item has been deleted successfully"})

class ChannelGetOne(Resource):
    def get(self,user_id, lab_name, channel_id):
        try:
            org_name = get_org_name(user_id)
            CHANNELS_COLLECTION = client[org_name+'_db'][lab_name+'_channels']
        except ValueError as e:
            abort(404, message=str(e))
        try:
            channel = CHANNELS_COLLECTION.find_one({'_id': ObjectId(channel_id)})
            if not channel:
                abort(404, message="Channel not found")
            # for channel in channel:
            response = {
                    "_id":str(channel['_id']),
                    "created at":channel['created at'].strftime("%Y-%m-%d %H:%M:%S"),
                    "user":channel['user'],
                    "item":channel['item'],
                    "lot_numb": channel["lot_numb"],
                    "direction": channel["direction"],
                    "location": channel["location"],
                    "quantity":channel['quantity'],
                    "description":channel['description']}
            return response, 200
        except Exception as e:
            return {"message": "Error occured while fetching put in use item", "error": str(e)}

class ChannelGetAll(Resource):
    def get(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            CHANNELS_COLLECTION = client[org_name+'_db'][lab_name+'_channels']
        except ValueError as e:
            abort(404, message=str(e))
        channels = list(CHANNELS_COLLECTION.find())
        if not channels:
            abort(404, message="Channel not found")
        # utc_now = datetime.now()
        # wat_now = utc_now + timedelta(hours=1)

        channel_list = [{
            "_id": str(channel['_id']),
            "created at": channel.get('created at').strftime("%Y-%m-%d %H:%M:%S") if 'created at' in channel else None,
            "user": channel.get('user', 'Unknown User'),
            "item": channel.get('item', 'Unknown Item'),
            "lot_numb": channel.get("lot_numb", 'Unknown Lot Number'),
            "direction": channel.get("direction", 'Unknown Direction'),
            "location": channel.get("location", 'Unknown Location'),
            "quantity": channel.get('quantity', 0),
            "description": channel.get('description', 'No Description')
        } for channel in channels]

        response = {"channels": channel_list}
        return response, 200

        

