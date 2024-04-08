from flask_restful import Resource, reqparse, abort, fields
from flask import jsonify
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from engine import db_clinical


USERS_COLLECTION = db_clinical['users']
print(USERS_COLLECTION.find())
user_parser = reqparse.RequestParser()
user_parser.add_argument("firstname", type=str, help="Name is required", required=False)
user_parser.add_argument("lastname", type=str, help="Name is required", required=False)
user_parser.add_argument("email", type=str, help="Email is required", required=False)
user_parser.add_argument("password", type=str, help="Password is required", required=False)
user_parser.add_argument("image", type=str, required=False)
user_parser.add_argument("title", type=str, required=False)
user_parser.add_argument("org", type=str, required=False)
user_parser.add_argument("mobile", type=int, required=False)
user_parser.add_argument("address", type=str, required=False)



class UserPush(Resource):
    # @marshal_with(user_fields)
    def post(self):
        args = user_parser.parse_args()

        if USERS_COLLECTION.find_one({'email': args['email']}):
            response = {"message": "Email already exists"}
            return response, 400

        hashed_password = generate_password_hash(args["password"])
        user = {
            "firstname": args["firstname"],
            "lastname": args["lastname"],
            "email": args["email"],
            "password": hashed_password,
            "title": args["title"],
            "mobile": args["mobile"],
            "address": args["address"]
        }
        result = USERS_COLLECTION.insert_one(user)
        response = {
            "message": f"{args['firstname']}, your account has been created successfully",
            "user_id": str(result.inserted_id),       
        }
        return response, 200

class UserPut(Resource):
    def put(self, user_id):
        args = user_parser.parse_args()
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        print(user)
        if not user:
            abort(404, message="User not found")

        for key, value in args.items():
            if value is not None:
                user[key] = value

        USERS_COLLECTION.update_one({'_id': ObjectId(user_id)}, {"$set": user})

        response = {
            "message": "Your account been updated successfully"
            }

        return response

class UserDel(Resource):
    def delete(self, user_id):
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})

        if not user:
            abort(404, message="User not found")

        USERS_COLLECTION.delete_one({'_id': ObjectId(user_id)})

        response = {
            "message": f"User {user_id} has been deleted successfully"
            }
        return response, 200

class UserGetOne(Resource):

    def get(self, user_id):
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})

        if not user:
            abort(404, message="User not found")

        response = {
            "id": str(user['_id']),
            "firstname": user['firstname'],
            "lastname": user['lastname'],
            "email": user['email'],
            "image": user.get('image', ""),
            "title": user.get('title', ""),
            "org": user.get('org', ""),
            "mobile": user.get('mobile', ""),
            "address": user.get('address', "")
        }
        return response, 200

class UsersGetAll(Resource):
    def get(self):
        users = list(USERS_COLLECTION.find())
        # print(users)
        if not users:
            abort(404, message="No users found")

        user_list = [{
            "id": str(user['_id']),
            "firstname": user['firstname'],
            "lastname": user['lastname'],
            "email": user['email'],
            "image": user.get('image', ""),
            "title": user.get('title', ""),
            "org": user.get('org', ""),
            "mobile": user.get('mobile', ""),
            "address": user.get('address', "")
        } for user in users]
        response = {"users": user_list}
        return response, 200
