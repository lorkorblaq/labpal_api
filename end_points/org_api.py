from flask_restful import Resource, abort, reqparse
from flask import jsonify, make_response, request
from bson import json_util, ObjectId
from datetime import datetime, timedelta
from engine import client, org_users_db, get_org_name
import math


USERS_COLLECTION = org_users_db['users']
ORG_COLLECTION = org_users_db['organisations']

machine_parser = reqparse.RequestParser()
machine_parser.add_argument("name", type=str, help="name is required", required=False)
machine_parser.add_argument("serial_number", type=str, help="serial_no is required", required=False)


class OrgGetLabs(Resource):
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
            "lab_name": lab.get('lab_name', 'Unknown User'),
            "managers_email": lab.get('managers_email', 'Unknown Item'),
            "users": lab.get('users', 'Unknown Bench'),
            "org_id": lab.get('org_id', 'Unknown Machine')
        } for lab in labs]
        response = make_response({'labs':lab_list}, 200)
        # response.set_cookie('labs', lab_list, max_age=60*60*24 )
        return response