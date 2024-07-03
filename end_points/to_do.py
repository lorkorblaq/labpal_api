from flask_restful import Resource, reqparse, abort
from flask import jsonify
from bson.objectid import ObjectId
from datetime import datetime
from engine import db_clinical, client, org_users_db, get_org_name

USERS_COLLECTION = org_users_db['users']
TODOS_COLLECTION = org_users_db['to-do']

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
events_parser.add_argument("comments", type=str, required=False)
events_parser.add_argument("task", type=str, action='append', required=False, help="List of tasks")
events_parser.add_argument("resolved", type=bool, required=False, help="True if checked, otherwise False")

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