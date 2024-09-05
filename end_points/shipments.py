from flask import jsonify, request
from flask_restful import Resource, reqparse, abort, fields, marshal_with
from bson import ObjectId
from datetime import datetime, timedelta
from engine import client, org_users_db, get_org_name

# SHIPMENTS_COLLECTION = db_clinical['channels']
# ITEMS_COLLECTION = db_clinical['items']

USERS_COLLECTION = org_users_db['users']
ORG_COLLECTION = org_users_db['organisations']

shipments_parser = reqparse.RequestParser()

shipments_parser.add_argument("created_at", type=str, required=False)
shipments_parser.add_argument("create_lat_lng", type=str, help="Latitude and Longitude are required", required=False)
shipments_parser.add_argument("shipment_id", type=str, help="shipment id is required", required=False)
shipments_parser.add_argument("numb_of_packs", type=int, help="Number of packages is required", required=False)

shipments_parser.add_argument("picked_by", type=str, required=False)
shipments_parser.add_argument("pickup_loc", type=str, help="Pickup location is required", required=False)
shipments_parser.add_argument("pickup_time", type=str, required=False)
shipments_parser.add_argument("pickup_lat_lng", type=str, help="Location is required", required=False)

shipments_parser.add_argument("dropoff_by", type=str, required=False)
shipments_parser.add_argument("dropoff_loc", type=str, help="Drop off location is required", required=False)
shipments_parser.add_argument("dropoff_time", type=str, required=False)
shipments_parser.add_argument("dropoff_lat_lng", type=str, help="Location is required", required=False)

shipments_parser.add_argument("duration", type=int, required=False)
shipments_parser.add_argument("description", type=str, required=False)
shipments_parser.add_argument("completed", type=str, required=False)

class ShipmentsPush(Resource):
    def post(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            SHIPMENTS_COLLECTION = client[org_name+'_db'][lab_name+'_shipments']
        except ValueError as e:
            abort(404, message=str(e))
        try:
            args = shipments_parser.parse_args()
            user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
            if not user:
                return {"message": "User does not exist, kindly contact Lorkorblaq"}, 400
            elif not org_name:
                return {"message": "Organisation does not exist, kindly contact Lorkorblaq"}, 400
            labs = user.get('labs_access')
            if lab_name in labs:
                pass
            name = user.get('firstname') + ' ' + user.get('lastname')
            print('user_id2', user_id)
            utc_now = datetime.now()
            data = {
                "created_by": name,
                "created_at": utc_now,
                "shipment_id": args['shipment_id'],
                "numb_of_packs": args['numb_of_packs'],
                "pickup_loc": args['pickup_loc'],
                "dropoff_loc": args['dropoff_loc'],
                "create_lat_lng": args['create_lat_lng'],
                "description": args['description'],
                "completed": 'No'
                }
            shipments_data = SHIPMENTS_COLLECTION.find_one({'shipment_id': args['shipment_id']})

            if not shipments_data:
                inserted_id = SHIPMENTS_COLLECTION.insert_one(data).inserted_id
                inserted_id = str(inserted_id)
                response = {
                    "message": "Shipment created successfully",
                    "tracking_id": inserted_id
                }
                return response, 200
            else:
                return {"message": "Shipment already exists"}, 400

        except Exception as e:
            return {"message": "Error occured while creating shipment", "error": str(e)}

class ShipmentsPut(Resource):    
    def put(self, user_id, lab_name):
        args = shipments_parser.parse_args()
        shipment_id = args.get('shipment_id')
        try:
            org_name = get_org_name(user_id)
            SHIPMENTS_COLLECTION = client[org_name+'_db'][lab_name+'_shipments']
        except ValueError as e:
            abort(404, message=str(e))

        utc_now = datetime.now()  # Use UTC for consistency
        shipment = SHIPMENTS_COLLECTION.find_one({'shipment_id': shipment_id})
        if not shipment:
            abort(404, message="Shipment not found")

        # Update the shipment with new values
        for key, value in args.items():
            if value is not None:
                if isinstance(value, str) and value.strip() == '':
                    value = None
                shipment[key] = value

        picked = args.get('picked_by')
        if picked:
            shipment['picked_by'] = picked
            shipment['pickup_time'] = utc_now
            shipment['updated_at'] = utc_now

        dropped = args.get('dropoff_by')
        if dropped:
            shipment['dropoff_by'] = dropped
            shipment['dropoff_time'] = utc_now
            shipment['updated_at'] = utc_now
            shipment['completed'] = 'Yes'

            # Calculate the duration between pickup_time and dropoff_time
            pickup_time = shipment.get('created_at')
            dropoff_time = shipment.get('dropoff_time')
            if pickup_time and dropoff_time:
                duration = dropoff_time - pickup_time
                duration_days = f"{duration.days}D"
                duration_hours = f"{duration.seconds // 3600}H"
                duration_minutes = f"{(duration.seconds % 3600) // 60}M"
                duration_seconds = f"{duration.seconds % 60}S"

                shipment['duration'] = f"{duration_days}:{duration_hours}:{duration_minutes}:{duration_seconds}"


        SHIPMENTS_COLLECTION.replace_one({'shipment_id': shipment_id}, shipment)
        response = {"message": "Your data has been updated successfully"}
        
        return response, 200
    
class ShipmentsGetOne(Resource):
    def get(self,user_id, lab_name, shipment_id):
        try:
            org_name = get_org_name(user_id)
            SHIPMENTS_COLLECTION = client[org_name+'_db'][lab_name+'_shipments']
        except ValueError as e:
            abort(404, message=str(e))
        try:
            shipment = SHIPMENTS_COLLECTION.find_one({'_id': ObjectId(shipment_id)})
            if not shipment:
                abort(404, message="Channel not found")
            # for shipment in shipment:
            response = {
                    "_id":str(shipment['_id']),
                    "created at":shipment['created at'].strftime("%Y-%m-%d %H:%M:%S"),
                    "user":shipment['user'],
                    "item":shipment['item'],
                    "lot_numb": shipment["lot_numb"],
                    "direction": shipment["direction"],
                    "location": shipment["location"],
                    "quantity":shipment['quantity'],
                    "description":shipment['description']}
            return response, 200
        except Exception as e:
            return {"message": "Error occured while fetching put in use item", "error": str(e)}

class ShipmentsGetAll(Resource):
    def get(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            SHIPMENTS_COLLECTION = client[org_name+'_db'][lab_name+'_shipments']
        except ValueError as e:
            abort(404, message=str(e))
        shipments = list(SHIPMENTS_COLLECTION.find())
        if not shipments:
            abort(404, message="Shipment not found")
        # utc_now = datetime.now()
        # wat_now = utc_now + timedelta(hours=1)

        shipment_list = [{
            "id": str(shipment['_id']),
            "created_at": shipment.get('created_at').strftime("%Y-%m-%d %H:%M:%S") if 'created_at' in shipment else None,
            "created_by": shipment.get('created_by', 'Unknown User'),
            "picked_by": shipment.get('picked_by', 'Not yet picked'),
            "dropoff_by": shipment.get('dropoff_by', 'Not yet dropped'),
            "shipment_id": shipment.get('shipment_id', 'Unknown shipment id'),
            "numb_of_packs": shipment.get("numb_of_packs", 'Unknown numb of packs'),
            "pickup_loc": shipment.get("pickup_loc", 'Not yet picked'),
            "dropoff_loc": shipment.get("dropoff_loc", 'Not yet dropped'),
            "pickup_time": shipment.get('pickup_time').strftime("%Y-%m-%d %H:%M:%S") if 'pickup_time' in shipment else 'Not yet picked',
            "dropoff_time": shipment.get('dropoff_time').strftime("%Y-%m-%d %H:%M:%S") if 'dropoff_time' in shipment else 'Not yet dropped',
            "create_lat_lng": shipment.get('create_lat_lng', 'location'),
            "pickup_lat_lng": shipment.get('pickup_lat_lng', 'Not yet picked'),
            "dropoff_lat_lng": shipment.get('dropoff_lat_lng', 'Not yet dropped'),
            "duration": shipment.get('duration', 0),
            "description": shipment.get('description', 'No Description'),
            "completed": shipment.get('completed', False)
        } for shipment in shipments]

        response = {"shipments": shipment_list}
        return response, 200

class ShipmentsDel(Resource):
     def delete(self, user_id, lab_name, shipment_id):
        try:
            org_name = get_org_name(user_id)
            SHIPMENTS_COLLECTION = client[org_name+'_db'][lab_name+'_shipments']
        except ValueError as e:
            abort(404, message=str(e))

        SHIPMENTS_COLLECTION.delete_one({'_id': ObjectId(shipment_id)})
        return jsonify({"message": "Item has been deleted successfully"})
