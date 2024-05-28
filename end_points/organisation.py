from flask import Flask, jsonify, request, abort
from flask_restful import Api, Resource, reqparse
from bson import ObjectId
from datetime import datetime, timedelta
from engine import db_clinical

ORGANISATION_COLLECTION = db_clinical['organisations']



class GetOrganisation(Resource):
    def get(self, name):
        result = ORGANISATION_COLLECTION.find_one({'name': name})
        if not result:
            return {"message": "Organisation not found"}, 404
        result['_id'] = str(result['_id'])
        return result, 200
    
class OrganisationPush(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("name", type=str, help="Name is required", required=True)
            parser.add_argument("address", type=str, help="Address is required", required=True)
            parser.add_argument("domain", type=str, help="Email is required", required=True)
            parser.add_argument("staff numb.", type=int, help="Staff number is required", required=True)
            parser.add_argument("created by", type=str, help="Created by is required", required=True)
            args = parser.parse_args()
            # Check if organisation already exists
            if ORGANISATION_COLLECTION.find_one({'name': args['name']}):
                return {"message": "Organisation already exists"}, 400
            # Insert organisation
            ORGANISATION_COLLECTION.insert_one(args)
            return {"message": "Organisation created successfully"}, 201
        except Exception as e:
            return {"message": "Error occured while creating organisation", "error": str(e)}
    
