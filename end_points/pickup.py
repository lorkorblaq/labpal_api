from flask import jsonify, request
from flask_restful import Resource, reqparse, abort, fields, marshal_with
from bson import ObjectId
from datetime import datetime, timedelta
from engine import client, org_users_db, get_org_name

# REQUEST_COLLECTION = db_clinical['channels']
# ITEMS_COLLECTION = db_clinical['items']

USERS_COLLECTION = org_users_db['users']
ORG_COLLECTION = org_users_db['organisations']

pickup_parser = reqparse.RequestParser()

pickup_parser.add_argument("created_at", type=str, required=False)
pickup_parser.add_argument("create_lat_lng", type=str, help="Latitude and Longitude are required", required=False)
pickup_parser.add_argument("request_id", type=str, help="Request id is required", required=False)
pickup_parser.add_argument("numb_of_samples", type=int, help="Number of samples is required", required=False)
pickup_parser.add_argument("accepted_by", type=str, required=False)
pickup_parser.add_argument("pickup_time", type=str, required=False)

pickup_parser.add_argument("atPickup", type=str, required=False)
pickup_parser.add_argument("enroute_by", type=str, required=False)
pickup_parser.add_argument("assigned_by", type=str, required=False)
pickup_parser.add_argument("assigned_to", type=str, required=False)
pickup_parser.add_argument("picked_by", type=str, required=False)
pickup_parser.add_argument("pickup_loc", type=str, help="Pickup location is required", required=False)
pickup_parser.add_argument("pickup_time", type=str, required=False)

pickup_parser.add_argument("dropped_by", type=str, required=False)
pickup_parser.add_argument("dropoff_time", type=str, required=False)
pickup_parser.add_argument("dropoff_lat_lng", type=str, help="Location is required", required=False)

pickup_parser.add_argument("duration", type=int, required=False)
pickup_parser.add_argument("description", type=str, required=False)
pickup_parser.add_argument("completed", type=str, required=False)
pickup_parser.add_argument("delivery_status", type=str, required=False)
pickup_parser.add_argument("current_lat_lng", type=str, required=False)
pickup_parser.add_argument("rider_info", type=str, required=False)
pickup_parser.add_argument("urgency_level", type=str, required=False)
pickup_parser.add_argument("tracking_url", type=str, required=False)
pickup_parser.add_argument("eta", type=str, required=False)

class RequestsPush(Resource):
    def post(self, user_id):
        wat_now = datetime.now()
        try:
            org_name = get_org_name(user_id)
            REQUEST_COLLECTION = client[org_name+'_db']['request_pickup']
        except ValueError as e:
            abort(404, message=str(e))
        try:
            args = pickup_parser.parse_args()
            user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
            if not user:
                return {"message": "User does not exist, kindly contact Lorkorblaq"}, 400
            elif not org_name:
                return {"message": "Organisation does not exist, kindly contact Lorkorblaq"}, 400
            name = user.get('firstname') + ' ' + user.get('lastname')
            data = {
                "created_by": name,
                "created_at": wat_now,
                "request_id": args['request_id'],
                "pickup_loc": args['pickup_loc'],
                "numb_of_samples": args['numb_of_samples'],
                "create_lat_lng": args['create_lat_lng'],
                "description": args['description'],
                "completed": 'no'  
                }
            print(data)
            request_data = REQUEST_COLLECTION.find_one({'request_id': args['request_id']})

            if not request_data:
                inserted_id = REQUEST_COLLECTION.insert_one(data).inserted_id
                inserted_id = str(inserted_id)
                response = {
                    "message": "Request created successfully",
                    "tracking_id": inserted_id
                }
                return response, 200
            else:
                return {"message": "Request already exists"}, 400

        except Exception as e:
            return {"message": "Error occured while creating request", "error": str(e)}
        
class RequestPut(Resource):
    def put(self, user_id):
        wat_now = datetime.now()
        args = pickup_parser.parse_args()
        request_id = args.get('request_id')
        
        try:
            org_name = get_org_name(user_id)
            REQUEST_COLLECTION = client[org_name+'_db']['request_pickup']
        except ValueError as e:
            abort(404, message=str(e))

        # Retrieve the request from the database
        request = REQUEST_COLLECTION.find_one({'request_id': request_id})
        if not request:
            abort(404, message="Request not found")

        # Check each field in sequence and update as necessary
        accepted = args.get('accepted_by')
        if accepted:
            if request.get('accepted') == 'yes':
                abort(400, message="Request has already been accepted")
            request['accepted_time'] = wat_now
            request['accepted'] = 'yes'

        assigned = args.get('assigned_to')
        if assigned:
            if request.get('accepted') != 'yes':
                abort(400, message="Request must be accepted before assigning")
            if request.get('assigned') == 'yes':
                abort(400, message="Request has already been assigned")
            request['assignedTime'] = wat_now
            request['assigned'] = 'yes'
            request['assigned_to'] = assigned

        enroute = args.get('enroute_by')
        if enroute:
            if request.get('assigned') != 'yes':
                abort(400, message="Request must be assigned before enroute")
            if request.get('enroute') == 'yes':
                abort(400, message="Request is already enroute")
            request['enrouteTime'] = wat_now
            request['enroute'] = 'yes'

        atPickup = args.get('atPickup')
        if atPickup:
            if request.get('enroute') != 'yes':
                abort(400, message="Request must be enroute before pickup")
            if request.get('atPickup') == 'yes':
                abort(400, message="Request is already at pickup")
            request['atPickupTime'] = wat_now
            request['atPickup'] = 'yes'

        picked = args.get('picked_by')
        if picked:
            if request.get('atPickup') != 'yes':
                abort(400, message="Request must be at pickup before being picked")
            if request.get('picked') == 'yes':
                abort(400, message="Request has already been picked")
            request['picked_by'] = picked
            request['pickup_time'] = wat_now
            request['picked'] = 'yes'

        dropped = args.get('dropped_by')
        if dropped:
            if request.get('picked') != 'yes':
                abort(400, message="Request must be picked before being dropped")
            if request.get('completed') == 'yes':
                abort(400, message="Request has already been completed")
            request['dropoff_time'] = wat_now
            request['completed'] = 'yes'

            # Calculate the duration between pickup_time and dropoff_time
            pickup_time = request.get('pickup_time')
            dropoff_time = request.get('dropoff_time')
            if pickup_time and dropoff_time:
                duration = dropoff_time - pickup_time
                total_minutes = duration.total_seconds() // 60  # Convert to minutes
                request['duration'] = total_minutes

        # Replace the request document in the database
        REQUEST_COLLECTION.replace_one({'request_id': request_id}, request)
        
        response = {"message": "Your data has been updated successfully"}
        return response, 200
    
class RequestGetOne(Resource):
    def get(self,user_id, request_id):
        try:
            org_name = get_org_name(user_id)
            REQUEST_COLLECTION = client[org_name+'_db']['request_pickup']
        except ValueError as e:
            abort(404, message=str(e))
        try:
            request = REQUEST_COLLECTION.find_one({'_id': ObjectId(request_id)})
            if not request:
                abort(404, message="Channel not found")
            # for request in request:
            response = {
                "id": str(request['_id']),
                "created_at": request.get('created_at').strftime("%Y-%m-%d %H:%M:%S") if 'created_at' in request else None,
                "created_by": request.get('created_by', 'Unknown User'),
                "accepted_by": request.get('accepted_by', 'Unknown User'),
                "accepted_time": request.get('accepted_time').strftime("%Y-%m-%d %H:%M:%S") if 'accepted_time' in request else None,
                "picked_by": request.get('picked_by', 'Not yet picked'),
                "request_id": request.get('request_id', 'Unknown request id'),
                "numb_of_samples": request.get("numb_of_samples", 'Unknown numb of samples'),
                "pickup_loc": request.get("pickup_loc", 'Not yet picked'),
                "enrouteTime": request.get('enrouteTime').strftime("%Y-%m-%d %H:%M:%S") if 'enrouteTime' in request else 'Not yet enroute',
                
                "assigned_to": request.get('assigned_to', 'not yet assigned'),
                "assigned_by": request.get('assigned_by', 'not yet assigned'),

                "accepted": request.get('accepted', 'no'),
                "assigned": request.get('assigned', 'no'),
                "atPickup": request.get('atPickup', 'no'),
                "picked": request.get('picked', 'no'),
                "enroute": request.get('enroute', 'no'),

                "enrouteTime": request.get('enrouteTime').strftime("%Y-%m-%d %H:%M:%S") if 'enrouteTime' in request else 'Not yet enroute',
                "assignedTime": request.get('assignedTime').strftime("%Y-%m-%d %H:%M:%S") if 'assignedTime' in request else 'Not yet assigned',
                "atPickupTime": request.get('atPickupTime').strftime("%Y-%m-%d %H:%M:%S") if 'atPickupTime' in request else 'Not yet at pick up',
                "pickup_time": request.get('pickup_time').strftime("%Y-%m-%d %H:%M:%S") if 'pickup_time' in request else 'Not yet picked',
                "dropoff_time": request.get('dropoff_time').strftime("%Y-%m-%d %H:%M:%S") if 'dropoff_time' in request else 'Not yet dropped',
                "create_lat_lng": request.get('create_lat_lng', 'location'),
                "dropoff_lat_lng": request.get('dropoff_lat_lng', 'Not yet dropped'),
                "duration": request.get('duration', 0),
                "description": request.get('description', 'No Description'),
                "completed": request.get('completed', False)}
            return response, 200
        except Exception as e:
            return {"message": "Error occured while fetching request", "error": str(e)}

class RequestGetAll(Resource):
    def get(self, user_id):
        try:
            org_name = get_org_name(user_id)
            REQUEST_COLLECTION = client[org_name+'_db']['request_pickup']
        except ValueError as e:
            abort(404, message=str(e))
        requests = list(REQUEST_COLLECTION.find())
        if not requests:
            abort(404, message="Request not found")

        request_list = [{
            "id": str(request['_id']),
            "created_at": request.get('created_at').strftime("%Y-%m-%d %H:%M:%S") if 'created_at' in request else None,
            "created_by": request.get('created_by', 'Unknown User'),
            "accepted_by": request.get('accepted_by', 'Unknown User'),
            "accepted_time": request.get('accepted_time').strftime("%Y-%m-%d %H:%M:%S") if 'accepted_time' in request else None,
            "picked_by": request.get('picked_by', 'Not yet picked'),
            "request_id": request.get('request_id', 'Unknown request id'),
            "numb_of_samples": request.get("numb_of_samples", 'Unknown numb of samples'),
            "pickup_loc": request.get("pickup_loc", 'Not yet picked'),
            "enrouteTime": request.get('enrouteTime').strftime("%Y-%m-%d %H:%M:%S") if 'enrouteTime' in request else 'Not yet enroute',
            
            "assigned_to": request.get('assigned_to', 'not yet assigned'),
            "assigned_by": request.get('assigned_by', 'not yet assigned'),

            "accepted": request.get('accepted', 'no'),
            "assigned": request.get('assigned', 'no'),
            "atPickup": request.get('atPickup', 'no'),
            "picked": request.get('picked', 'no'),
            "enroute": request.get('enroute', 'no'),

            "enrouteTime": request.get('enrouteTime').strftime("%Y-%m-%d %H:%M:%S") if 'enrouteTime' in request else 'Not yet enroute',
            "assignedTime": request.get('assignedTime').strftime("%Y-%m-%d %H:%M:%S") if 'assignedTime' in request else 'Not yet assigned',
            "atPickupTime": request.get('atPickupTime').strftime("%Y-%m-%d %H:%M:%S") if 'atPickupTime' in request else 'Not yet at pick up',
            "pickup_time": request.get('pickup_time').strftime("%Y-%m-%d %H:%M:%S") if 'pickup_time' in request else 'Not yet picked',
            "dropoff_time": request.get('dropoff_time').strftime("%Y-%m-%d %H:%M:%S") if 'dropoff_time' in request else 'Not yet dropped',
            "create_lat_lng": request.get('create_lat_lng', 'location'),
            "dropoff_lat_lng": request.get('dropoff_lat_lng', 'Not yet dropped'),
            "duration": request.get('duration', 0),
            "description": request.get('description', 'No Description'),
            "completed": request.get('completed', False)
        } for request in requests]

        response = {"requests": request_list}
        return response, 200

class RequestDel(Resource):
     def delete(self, user_id, request_id):
        try:
            org_name = get_org_name(user_id)
            REQUEST_COLLECTION = client[org_name+'_db']['request_pickup']
        except ValueError as e:
            abort(404, message=str(e))

        REQUEST_COLLECTION.delete_one({'_id': ObjectId(request_id)})
        return jsonify({"message": "Request has been deleted successfully"})
