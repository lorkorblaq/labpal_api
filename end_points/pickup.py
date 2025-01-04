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

{
  "_id": { "$oid": "676fb569fb709aa659a5b966" },
  "created_by": "Olorunfemi Oloko",
  "created_at": { "$date": "2024-12-28T09:23:04.882Z" },
  "request_id": "IFom86T",
  "pickup_loc": "clinicals_lagos",
  "dropoff_loc": "city_hospital_ikeja",
  "numb_of_samples": 3,
  "create_lat_lng": "6.545021",
  "delivery_status": "In Transit",
  "current_lat_lng": "6.593421,3.350635",
  "eta": "2024-12-28T10:30:00Z",
  "description": "Safe",
  "completed": "No",
  "accepted": "Yes",
  "rider_info": {
    "name": "Miracle John",
    "phone": "+2348012345678",
    "vehicle": "Bike",
    "current_lat_lng": "6.593421,3.350635"
  },
  "route_info": {
    "pickup_time": "2024-12-28T09:30:00Z",
    "waypoints": [
      { "lat_lng": "6.558112,3.342745", "description": "Checkpoint 1" },
      { "lat_lng": "6.580987,3.345612", "description": "Checkpoint 2" }
    ]
  },
  "urgency_level": "Standard",
  "tracking_url": "https://yourapp.com/track/IFom86T"
}



class RequestsPush(Resource):
    def post(self, user_id):
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
            utc_now = datetime.now()
            data = {
                "created_by": name,
                "created_at": utc_now,
                "request_id": args['request_id'],
                "pickup_loc": args['pickup_loc'],
                "numb_of_samples": args['numb_of_samples'],
                "create_lat_lng": args['create_lat_lng'],
                "description": args['description'],
                "completed": 'No'
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
        args = pickup_parser.parse_args()
        request_id = args.get('request_id')
        try:
            org_name = get_org_name(user_id)
            REQUEST_COLLECTION = client[org_name+'_db']['request_pickup']
        except ValueError as e:
            abort(404, message=str(e))

        utc_now = datetime.now()  # Use UTC for consistency
        request = REQUEST_COLLECTION.find_one({'request_id': request_id})
        if not request:
            abort(404, message="Request not found")

        # Update the request with new values
        for key, value in args.items():
            if value is not None:
                if isinstance(value, str) and value.strip() == '':
                    value = None
                request[key] = value

        accepted = args.get('accepted_by')
        if accepted:
            request['accepted_by'] = accepted
            request['accepted_time'] = utc_now
            request['accepted'] = 'Yes'
            request['updated_at'] = utc_now
        picked = args.get('picked_by')
        if picked:
            request['picked_by'] = picked
            request['pickup_time'] = utc_now
            request['picked'] = 'Yes'
            request['updated_at'] = utc_now

        dropped = args.get('dropped_by')
        if dropped:
            request['dropoff_time'] = utc_now
            request['updated_at'] = utc_now
            request['completed'] = 'Yes'

            # Calculate the duration between pickup_time and dropoff_time
            pickup_time = request.get('pickup_time')
            dropoff_time = request.get('dropoff_time')
            if pickup_time and dropoff_time:
                duration = dropoff_time - pickup_time
                total_minutes = duration.total_seconds() // 60  # Convert to minutes
                request['duration'] = total_minutes
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
                    "accepted": request.get('accepted', 'No'),
                    "accepted_by": request.get('accepted_by', 'Unknown User'),
                    "accepted_time": request.get('accepted_time').strftime("%Y-%m-%d %H:%M:%S") if 'accepted_time' in request else None,
                    "picked_by": request.get('picked_by', 'Not yet picked'),
                    "request_id": request.get('request_id', 'Unknown request id'),
                    "numb_of_samples": request.get("numb_of_samples", 'Unknown numb of samples'),
                    "pickup_loc": request.get("pickup_loc", 'Not yet picked'),
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
        # utc_now = datetime.now()
        # wat_now = utc_now + timedelta(hours=1)

        request_list = [{
            "id": str(request['_id']),
            "created_at": request.get('created_at').strftime("%Y-%m-%d %H:%M:%S") if 'created_at' in request else None,
            "created_by": request.get('created_by', 'Unknown User'),
            "accepted": request.get('accepted', 'No'),
            "accepted_by": request.get('accepted_by', 'Unknown User'),
            "accepted_time": request.get('accepted_time').strftime("%Y-%m-%d %H:%M:%S") if 'accepted_time' in request else None,
            "picked_by": request.get('picked_by', 'Not yet picked'),
            "request_id": request.get('request_id', 'Unknown request id'),
            "numb_of_samples": request.get("numb_of_samples", 'Unknown numb of samples'),
            "pickup_loc": request.get("pickup_loc", 'Not yet picked'),
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
