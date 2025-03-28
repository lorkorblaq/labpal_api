from flask_restful import Resource, abort, reqparse
from flask import jsonify, make_response, request
from bson import json_util, ObjectId
from datetime import datetime, timedelta
from engine import client, org_users_db, get_org_name
import math
# from ..utils.tokens import generate_registration_url, decode_token, generate_reset_email_url



USERS_COLLECTION = org_users_db['users']
ORG_COLLECTION = org_users_db['org']

labs_parser = reqparse.RequestParser()
labs_parser.add_argument("lab_name", type=str, help="Lab name is required", required=False)
labs_parser.add_argument("region", type=str, help="Region is required", required=False)
labs_parser.add_argument("area", type=str, help="Area is required", required=False)


class LabsGet(Resource):
    def get(self, user_id):
        try:
            org_name = get_org_name(user_id)
            LABS_COLLECTION = client[org_name+'_db']['labs']
        except ValueError as e:
            abort(404, message=str(e))
        labs = list(LABS_COLLECTION.find())
        lab_list = [{
            "_id": str(lab['_id']),
            "created at": lab.get('created at').strftime("%Y-%m-%d %H:%M:%S") if 'created at' in lab else None,
            "lab_name": lab.get('lab_name', 'Unknown lab name'),
            "managers_email": lab.get('managers_email', 'Unknown managers email'),
            "users": lab.get('users', 'Unknown users'),
            "org_id": lab.get('org_id', 'Unknown Org is'),
            "area": lab.get('area', 'Unknown Area'),
            "region": lab.get('region', 'Unknown Region')
        } for lab in labs]
        response = make_response({'labs':lab_list}, 200)
        return response
    
class LabsPush(Resource):
    def post(self, user_id):
        org_name = get_org_name(user_id)
        LABS_COLLECTION = client[org_name+'_db']['labs']
        org = ORG_COLLECTION.find_one({'org_name': org_name}, {'_id': 1})
        print(org)
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}, {'role': 1})
        args = labs_parser.parse_args()

        if not org:
            abort(404, message="Organization not found")
        if not user:
            abort(404, message="User not found")
        if user['role'] != 'creator':
            abort(404, message="User is not permitted to create a lab")
        if LABS_COLLECTION.find_one({'lab_name': args['lab_name']}):
            abort(404, message="Lab already exists")

        org_id = str(org.get('_id'))

        lab = {
            "created_at": datetime.now(),
            "lab_name": args['lab_name'],  # Use 'name' since 'lab_name' is not in the parser
            "region": args['region'],  # Ensure 'region' is added to the parser
            "area": args['area'],      # Ensure 'area' is added to the parser
            'org_id': org_id,
            "users": [str(user_id)]
        }

        lab_id = LABS_COLLECTION.insert_one(lab).inserted_id
        if lab_id:
            ORG_COLLECTION.update_one({"org_name": org_name}, {"$push": {"labs": args['lab_name']}})
            USERS_COLLECTION.update_one({"_id": ObjectId(user_id)}, {"$push": {"labs_access": args['lab_name']}})

        response = make_response({'lab_id': str(lab_id)}, 200)
        return response