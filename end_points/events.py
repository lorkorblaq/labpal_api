from flask_restful import Resource, reqparse, abort
from flask import jsonify
from bson.objectid import ObjectId
from datetime import datetime
from engine import db_clinical, client, org_users_db, get_org_name

USERS_COLLECTION = org_users_db['users']
TODOS_COLLECTION = db_clinical['to-do']

# Custom date type function for reqparse
def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Not a valid date: '{s}'. Use YYYY-MM-DD format.")

def valid_time(s):
    try:
        return datetime.strptime(s, "%I:%M %p").time()
    except ValueError:
        raise ValueError(f"Not a valid time: '{s}'. Use HH:MM AM/PM format.")

def valid_datetime(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %I:%M %p")
    except ValueError:
        raise ValueError(f"Not a valid datetime: '{s}'. Use YYYY-MM-DD HH:MM AM/PM format.")
# Initialize the request parser

events_parser = reqparse.RequestParser()
events_parser.add_argument("date", type=valid_date, required=False, help="Date in YYYY-MM-DD format")
events_parser.add_argument("time", type=valid_time, required=False, help="Please state time in HH:MM AM/PM format")
events_parser.add_argument("datetime", type=valid_datetime, required=False)
events_parser.add_argument("machine", type=str, required=False)
events_parser.add_argument("items", type=str, action='append', required=False)
events_parser.add_argument("frequency", type=str, action='append', required=False)
events_parser.add_argument("category", type=str, required=False)
events_parser.add_argument("rootCause", type=str, required=False)
events_parser.add_argument("actioning", type=str, required=False)
events_parser.add_argument("occurrence", type=str, action='append', required=False)
# events_parser.add_argument("actioning", type=str, required=False)
events_parser.add_argument("comments", type=str, required=False)
events_parser.add_argument("task", type=str, action='append', required=False, help="List of tasks")
events_parser.add_argument("resolved", type=bool, required=False, help="True if checked, otherwise False")

class EventPush(Resource):
    def post(self, user_id, lab_name, event_type):
        try:
            orgname = get_org_name(user_id)
            EVENTS_COLLECTION = client[orgname+'_db'][lab_name+'_events']
        except ValueError as e:
            abort(404, message=str(e)) 
        args = events_parser.parse_args()
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        if not user:
            return {"message": "User does not exist"}, 400
        if event_type not in ['qc', 'machine', 'operations', 'tasks']:
            return {"message": "Event type not supported"}, 400

        event = {
            "user": f"{user.get('firstname')} {user.get('lastname')}",
            "event_type": event_type,
            "created_at": datetime.now()
        }

        datetimer = datetime.combine(args["date"], args["time"] if args["time"] else datetime.min.time())
        # print(datetimer)

        if event_type == 'qc':
            event.update({
                "date": datetimer,
                "machine": args["machine"],
                "items": args["items"],
                "rootCause": args["rootCause"],
                "actioning": args["actioning"]
            })
        elif event_type == 'machine':
            # print(args['category'])
            if args['category'] not in ['Maintenance', 'Downtime', 'Troubleshooting']:
                return {"message": "Category not supported"}, 400
            event.update({
                "category": args['category'],
                "machine": args["machine"],
                "datetime": datetimer
            })
            if args['category'] == 'Maintenance':
                event.update({
                    "frequency": args["frequency"],
                    "comments": args["comments"],
                })
            else:
                args['category'] == 'Downtime' or 'Troubleshooting'
                event.update({
                    "resolved": args["resolved"],
                    "rootCause": args["rootCause"],
                    "actioning": args["actioning"]
                })
        elif event_type == 'operations':
            event.update({
                "date": datetimer,
                "occurrence": args["occurrence"],
                "actioning": args["actioning"]
            })
        EVENTS_COLLECTION.insert_one(event)
        return {"message": "Event created successfully"}, 200

class EventGetOne(Resource):
    def get(self, user_id, lab_name, event_id):
        try:
            orgname = get_org_name(user_id)
            EVENTS_COLLECTION = client[orgname+'_db'][lab_name+'_events']
        except ValueError as e:
            abort(404, message=str(e)) 
        # Validate input parameters
        if not user_id or not event_id:
            return {"message": "User id and event id are required"}, 400

        # Check if the user exists
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        if not user:
            return {"message": "User does not exist"}, 400

        # Find the event by event_id
        event = EVENTS_COLLECTION.find_one({'_id': ObjectId(event_id)})
        if not event:
            return {"message": "Event does not exist"}, 400

        # Construct the result dictionary
        result_dict = {
            "event_id": str(event["_id"]),
            "user": event.get("user", ""),
            "event_type": event.get("event_type", ""),
            "created_at": event.get("created_at", "")
        }
        if event['event_type'] == 'qc':
            result_dict.update({
                "date": event.get("date", ""),
                "machine": event.get("machine", ""),
                "items": event.get("items", ""),
                "rootCause": event.get("rootCause", ""),
                "actioning": event.get("actioning", ""),
            })
        elif event['event_type'] == 'machine':
            result_dict.update({
                "datetime": event.get("datetime", ""),
                "machine": event.get("machine", ""),
                "category": event.get("category", ""),
            })
            if result_dict["category"] == 'maintenance':
                result_dict.update({
                    "frequency": event.get("frequency", ""),
                    "comments": event.get("comments", "")
                })
            else:
                result_dict.update({
                    "resolved": event.get("resolved", ""),
                    "rootCause": event.get("rootCause", ""),
                    "actioning": event.get("actioning", "")
                })

        elif event['event_type'] == 'operations':
            result_dict.update({
                "date": event.get("date", ""),
                "occurence": event.get("occurence", ""),
                "actioning": event.get("actioning", "")
            })

        # Return the event data as JSON
        return jsonify(result_dict)

class EventGetAll(Resource):
    def get(self, user_id, lab_name, event_type):
        try:
            orgname = get_org_name(user_id)
            EVENTS_COLLECTION = client[orgname+'_db'][lab_name+'_events']
        except ValueError as e:
            abort(404, message=str(e)) 
        if not user_id:
            return {"message": "User id is required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        if event_type not in ['qc', 'machine', 'operations', 'tasks']:
            return {"message": "Event type not supported"}, 400
        events = EVENTS_COLLECTION.find({'event_type': event_type})
        result = []
        for event in events:
            print(event)
            result_dict = {
                "event_id": str(event["_id"]),
                "user": event.get("user", ""),
                "event_type": event.get("event_type", ""),
                "created_at": event.get("created_at", "")
            }
            if event['event_type'] == 'qc':
                result_dict.update({
                    "date": event.get("date", ""),
                    "machine": event.get("machine", ""),
                    "items": event.get("items", ""),
                    "rootCause": event.get("rootCause", ""),
                    "actioning": event.get("actioning", ""),
                })
            elif event['event_type'] == 'machine':
                result_dict.update({
                    "datetime": event.get("datetime", ""),
                    "machine": event.get("machine", ""),
                    "category": event.get("category", ""),
                })
                if result_dict["category"] == 'Maintenance':
                    result_dict.update({
                        "frequency": event.get("frequency", ""),
                        "comments": event.get("comments", "")
                    })
                else:
                    result_dict.update({
                        "resolved": event.get("resolved", ""),
                        "rootCause": event.get("rootCause", ""),
                        "actioning": event.get("actioning", "")
                    })

            elif event['event_type'] == 'operations':
                result_dict.update({
                    "date": event.get("date", ""),
                    "occurrence": event.get("occurrence", ""),
                    "actioning": event.get("actioning", "")
                })
            result.append(result_dict)
        return jsonify(result)

class EventPut(Resource):
    def put(self, user_id, lab_name, event_id):
        try:
            orgname = get_org_name(user_id)
            EVENTS_COLLECTION = client[orgname+'_db'][lab_name+'_events']
        except ValueError as e:
            abort(404, message=str(e)) 
        if user_id is None or event_id is None:
            return {"message": "User id and event id are required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        if not EVENTS_COLLECTION.find_one({'_id': ObjectId(event_id)}):
            return {"message": "Event does not exist"}, 400
        
        args = events_parser.parse_args()
        update_fields = {k: v for k, v in args.items() if v is not None}
        EVENTS_COLLECTION.update_one({'_id': ObjectId(event_id)}, {"$set": update_fields})
        return {"message": "Event updated successfully"}, 200

class EventDel(Resource):
    def delete(self, user_id, lab_name, event_id):
        try:
            orgname = get_org_name(user_id)
            EVENTS_COLLECTION = client[orgname+'_db'][lab_name+'_events']
        except ValueError as e:
            abort(404, message=str(e)) 
        if not user_id or not event_id:
            return {"message": "User id and event id are required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        if not EVENTS_COLLECTION.find_one({'_id': ObjectId(event_id)}):
            return {"message": "Event does not exist"}, 400
        EVENTS_COLLECTION.delete_one({'_id': ObjectId(event_id)})
        return {"message": "Event deleted successfully"}, 200


    def delete(self, user_id):
        if not user_id:
            return {"message": "User id is required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        TODOS_COLLECTION.delete_many({"user_id": ObjectId(user_id)})
        return {"message": "All to-dos deleted successfully"}, 200