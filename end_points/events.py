from flask_restful import Resource, reqparse, abort
from flask import jsonify
from bson.objectid import ObjectId
from datetime import datetime
from engine import db_clinical
import logging

USERS_COLLECTION = db_clinical['users']
EVENTS_COLLECTION = db_clinical['events']
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
    def post(self, user_id, event_type):
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
        date_str = datetimer.strftime("%Y-%m-%d")

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
    def get(self, user_id, event_id):
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
    def get(self, user_id, event_type):
        if not user_id:
            return {"message": "User id is required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        if event_type not in ['qc', 'machine', 'operations', 'tasks']:
            return {"message": "Event type not supported"}, 400
        events = EVENTS_COLLECTION.find({'event_type': event_type})
        result = []
        for event in events:
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
    def put(self, user_id, event_id):
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
    def delete(self, user_id, event_id):
        if not user_id or not event_id:
            return {"message": "User id and event id are required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        if not EVENTS_COLLECTION.find_one({'_id': ObjectId(event_id)}):
            return {"message": "Event does not exist"}, 400
        EVENTS_COLLECTION.delete_one({'_id': ObjectId(event_id)})
        return {"message": "Event deleted successfully"}, 200


class ToDoPush(Resource):
    def post(self, user_id):
        args = events_parser.parse_args()
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        if not user:
            return {"message": "User does not exist"}, 400
        datetimer = datetime.combine(args["date"], args["time"] if args["time"] else datetime.min.time())
        date_str = datetimer.strftime("%Y-%m-%d")
        # date_str = args.get("sdate")
        tasks = args.get("task", [])
        if not isinstance(tasks, list):
            tasks = [tasks]

        existing_todo = TODOS_COLLECTION.find_one({"user_id": ObjectId(user_id), "date": date_str})
        if existing_todo:
            if existing_todo.get("tasks") is None:
                existing_todo["tasks"] = []
            existing_todo["tasks"].extend(tasks)
            TODOS_COLLECTION.update_one({"_id": existing_todo["_id"]}, {"$set": {"tasks": existing_todo["tasks"]}})
        else:
            new_todo = {
                "user_id": ObjectId(user_id),
                "date": date_str,
                "tasks": tasks
            }
            TODOS_COLLECTION.insert_one(new_todo)
        
        return {"message": "To-do added successfully"}, 200

class ToDoPut(Resource):
    def put(self, user_id, date):
        if not user_id or not date:
            return {"message": "User id and date are required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        todo = TODOS_COLLECTION.find_one({"user_id": ObjectId(user_id), "date": date})
        if not todo:
            return {"message": "To-do does not exist"}, 400
        args = events_parser.parse_args()
        update_fields = {k: v for k, v in args.items() if v is not None}
        TODOS_COLLECTION.update_one({"_id": todo["_id"]}, {"$set": update_fields})
        return {"message": "To-do updated successfully"}, 200


class ToDoGetOne(Resource):
    def get(self, user_id, date):
        if not user_id or not date:
            return {"message": "User id and date are required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        todo = TODOS_COLLECTION.find_one({"user_id": ObjectId(user_id), "date": date})
        if not todo:
            return {"message": "To-do does not exist"}, 400
        return jsonify({
            "user_id": str(todo["user_id"]),
            "date": todo["date"],
            "tasks": todo["tasks"]
        })

class ToDoGetAll(Resource):
    def get(self, user_id):
        if not user_id:
            return {"message": "User id is required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        todos = TODOS_COLLECTION.find({"user_id": ObjectId(user_id)})
        result = []
        for todo in todos:
            result_dict = {
                "user_id": str(todo["user_id"]),
                "date": todo["date"],
                "tasks": todo["tasks"]
            }
            result.append(result_dict)
        return jsonify(result)


class ToDoDeleteTask(Resource):
    def delete(self, user_id, date, task):
        if not user_id or not date or not task:
            return {"message": "User id, date and task are required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        todo = TODOS_COLLECTION.find_one({"user_id": ObjectId(user_id), "date": date})
        if not todo:
            return {"message": "To-do does not exist"}, 400
        if task not in todo["tasks"]:
            return {"message": "Task does not exist in to-do"}, 400
        todo["tasks"].remove(task)
        TODOS_COLLECTION.update_one({"_id": todo["_id"]}, {"$set": {"tasks": todo["tasks"]}})
        return {"message": "Task deleted successfully"}, 200

class ToDoDeleteDate(Resource):
    def delete(self, user_id, date):
        if not user_id or not date:
            return {"message": "User id and date are required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        todo = TODOS_COLLECTION.find_one({"user_id": ObjectId(user_id), "date": date})
        if not todo:
            return {"message": "To-do does not exist"}, 400
        TODOS_COLLECTION.delete_one({"_id": todo["_id"]})
        return {"message": "To-do deleted successfully"}, 200

class ToDoDeleteAll(Resource):
    def delete(self, user_id):
        if not user_id:
            return {"message": "User id is required"}, 400
        if not USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}):
            return {"message": "User does not exist"}, 400
        TODOS_COLLECTION.delete_many({"user_id": ObjectId(user_id)})
        return {"message": "All to-dos deleted successfully"}, 200