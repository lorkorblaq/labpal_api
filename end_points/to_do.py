from flask_restful import Resource, reqparse, abort
from flask import jsonify
from bson.objectid import ObjectId
from datetime import datetime
from engine import org_users_db

USERS_COLLECTION = org_users_db['users']
TODOS_COLLECTION = org_users_db['to-do']
print(TODOS_COLLECTION)

# Custom date type function for reqparse
def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Not a valid date: '{s}'. Use YYYY-MM-DD format.")


    try:
        return datetime.strptime(s, "%Y-%m-%d %I:%M %p")
    except ValueError:
        raise ValueError(f"Not a valid datetime: '{s}'. Use YYYY-MM-DD HH:MM AM/PM format.")
# Initialize the request parser

events_parser = reqparse.RequestParser()
events_parser.add_argument("date", type=valid_date, required=False, help="Date in YYYY-MM-DD format")
events_parser.add_argument("comments", type=str, required=False)
events_parser.add_argument("task", type=dict, required=True, help="Task data is required")
events_parser.add_argument("resolved", type=bool, required=False, help="True if checked, otherwise False")

class ToDoPush(Resource):
    def post(self, user_id):
        args = events_parser.parse_args()
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        if not user:
            return {"message": "User does not exist"}, 400
        
        date = args.get("date")
        tasks = args.get("task", [])
        
        # Ensure tasks are correctly formatted as a list of dictionaries
        if isinstance(tasks, dict):
            tasks = [tasks]  # Convert single task dict to list of one task
        elif isinstance(tasks, list):
            tasks = [eval(task) if isinstance(task, str) else task for task in tasks]

        date_str = date.strftime("%Y-%m-%d")
        existing_todo = TODOS_COLLECTION.find_one({"user_id": user_id, "date": date_str})
        
        if existing_todo:
            if existing_todo.get("tasks") is None or not isinstance(existing_todo["tasks"], list):
                existing_todo["tasks"] = []
            existing_todo["tasks"].extend(tasks)
            TODOS_COLLECTION.update_one({"_id": existing_todo["_id"]}, {"$set": {"tasks": existing_todo["tasks"]}})
        else:
            new_todo = {
                "user_id": str(user_id),
                "date": date_str,
                "tasks": tasks
            }
            TODOS_COLLECTION.insert_one(new_todo)
        
        return {"message": "To-do added successfully"}, 200


class ToDoPut(Resource):
    def put(self, user_id, date):
        if not user_id or not date:
            return {"message": "User id and date are required"}, 400

        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        if not user:
            return {"message": "User does not exist"}, 400

        todo = TODOS_COLLECTION.find_one({"user_id": user_id, "date": date})
        if not todo:
            return {"message": "To-do does not exist"}, 400

        args = events_parser.parse_args()
        task_data = args.get("task")
        if not task_data:
            return {"message": "Task data is required"}, 400

        # Ensure task_data is a dictionary
        if isinstance(task_data, str):
            task_data = eval(task_data)

        tasks = todo.get("tasks", [])
        task_found = False
        for task in tasks:
            if task["text"] == task_data.get("oldText"):
                task["text"] = task_data.get("newText", task["text"])
                task["completed"] = task_data["completed"]
                task_found = True
                break

        if not task_found:
            return {"message": "Task not found"}, 404

        TODOS_COLLECTION.update_one({"_id": todo["_id"]}, {"$set": {"tasks": tasks}})
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
        
        todos = TODOS_COLLECTION.find({"user_id": user_id})
        result = []
        
        for todo in todos:
            tasks = todo.get("tasks", [])
            if isinstance(tasks, list) and all(isinstance(task, dict) for task in tasks):
                formatted_tasks = [{"text": task.get("text", ""), "completed": task.get("completed", False)} for task in tasks]
            else:
                # Handle the case where tasks are not in the expected format
                formatted_tasks = []
            
            result_dict = {
                "user_id": str(todo["user_id"]),
                "date": todo["date"],
                "tasks": formatted_tasks
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
        todo = TODOS_COLLECTION.find_one({"user_id": user_id, "date": date})
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