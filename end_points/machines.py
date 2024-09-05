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
machine_parser.add_argument("manufacturer", type=str, help="manufacturer is required", required=False)
machine_parser.add_argument("name_engineer", type=str, help="name engineer", required=False)
machine_parser.add_argument("contact_engineer", type=str, help="contact of engineer", required=False)

    # Example usage:

class MachineBulkPush(Resource):
    def post(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            MACHINES_COLLECTION = client[org_name+'_db'][lab_name+'_machines']

        except ValueError as e:
            abort(404, message=str(e))
        
        json_data = request.get_json()
        if not json_data:
            abort(400, message="No JSON data provided")
        
        # Ensure the required columns are present
        required_columns = {'name', 'serial_no', 'manufacturer', 'contact_engineer'}

        for entry in json_data:
            if not required_columns.issubset(entry.keys()):
                abort(400, message=f"Your data must contain the columns: {', '.join(required_columns)}")

            
            # Insert data into the MongoDB collection
            MACHINES_COLLECTION.insert_many(json_data)
            
            return make_response(jsonify({"message": "Data imported successfully"}), 201)
        
        # except Exception as e:
        #     abort(500, message=str(e))


class MachinePush(Resource):
    def post(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            MACHINES_COLLECTION = client[org_name+'_db'][lab_name+'_machines']
        except ValueError as e:
            abort(404, message=str(e))
        args = machine_parser.parse_args()
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        utc_now = datetime.now()
        wat_now = utc_now + timedelta(hours=1)
        print(org_name)
        if not user:
            return {"message": "User does not exist, kindly contact Lorkorblaq"}, 400
        elif not org_name:
            return {"message": "Organisation does not exist, kindly contact Lorkorblaq"}, 400
        machine = {
                "created at": wat_now,
                "name": args["name"], 
                "serial_number": args["serial_number"],
                "manufacturer": args["manufacturer"],
                "name_engineer": args["name_engineer"],
                "contact_engineer": args["contact_engineer"],
            }
        if not user:
            return {"message": "User does not exist, kindly contact Lorkorblaq"}, 400
        try:
            inserted_id = MACHINES_COLLECTION.insert_one(machine).inserted_id
            inserted_id = str(inserted_id)
            response = {
                "message": "Machine created successfully",
                "machine_id": inserted_id
            }
            return response, 200
        except Exception as e:
            return {"message": "Error occured while pushing machine", "error": str(e)}

class MachinePut(Resource):
    def put(self, user_id, lab_name, machine_id):
        try:
            org_name = get_org_name(user_id)
            MACHINES_COLLECTION = client[org_name + '_db'][lab_name + '_machines']
        except ValueError as e:
            abort(404, message=str(e))

        utc_now = datetime.now()
        args = machine_parser.parse_args()
        machine = MACHINES_COLLECTION.find_one({'_id': ObjectId(machine_id)})
        if not machine:
            abort(404, message="Machine not found")

        # Retrieve the current quantity before updates
        current_quantity = machine.get('quantity', 0)
        new_quantity = args.get('quantity')

        # Update the machine with new values
        for key, value in args.items():
            if value is not None:
                # Convert empty strings to None
                if isinstance(value, str) and value.strip() == '':
                    value = None
                machine[key] = value

        machine['updated_at'] = utc_now
        MACHINES_COLLECTION.replace_one({'_id': ObjectId(machine_id)}, machine)

        response = {"message": "Your data has been updated successfully"}
        return response, 200
    
class MachineDel(Resource):
     def delete(self, user_id, lab_name, machine_id):
        try:
            org_name = get_org_name(user_id)
            MACHINES_COLLECTION = client[org_name+'_db'][lab_name+'_machines']
        except ValueError as e:
            abort(404, message=str(e))

        MACHINES_COLLECTION.delete_one({'_id': ObjectId(machine_id)})
        return jsonify({"message": "Item has been deleted successfully"})

class MachineGetOne(Resource):
    def get(self,user_id, lab_name, machine_id):
        try:
            org_name = get_org_name(user_id)
            MACHINES_COLLECTION = client[org_name+'_db'][lab_name+'_machines']
        except ValueError as e:
            abort(404, message=str(e))
        try:
            machine = MACHINES_COLLECTION.find_one({'_id': ObjectId(machine_id)})
            if not machine:
                abort(404, message="Machine not found")
            # for machine in machine:
            response = {
                "_id": str(machine['_id']),
                "created at": machine['created at'].strftime("%Y-%m-%d %H:%M:%S"),
                "name": machine['name'],
                "serial_no": machine['serial_no'],
                "manufacturer": machine["manufacturer"],
                "contact_engineer": machine["contact_engineer"],
                "description": machine["description"]
            }
            return response, 200
        except Exception as e:
            return {"message": "Error occured while fetching put in use machine", "error": str(e)}

class MachineGetAll(Resource):
    def get(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            MACHINES_COLLECTION = client[org_name+'_db'][lab_name+'_machines']
        except ValueError as e:
            abort(404, message=str(e))
        machines = list(MACHINES_COLLECTION.find())
        if not machines:
            abort(404, message="No machine found")
        # utc_now = datetime.now()
        # wat_now = utc_now + timedelta(hours=1)
        print(machines)
        machine_list = [{
            "id": str(machine.get('_id')),
            "created at": machine.get('created at').strftime("%Y-%m-%d %H:%M:%S"),
            "name": machine.get('name', ""),
            "serial_number": machine.get('serial_number', ""),
            "manufacturer": machine.get("manufacturer", ""),
            "contact_engineer": machine.get("contact_engineer", ""),
            "description": machine.get("description", "")
        }for machine in machines]

        response = {"machines": machine_list}
        return response, 200

    def delete(self, user_id, lab_name):
        try:
            orgname = get_org_name(user_id)
            MACHINES_COLLECTION = client[orgname+'_db'][lab_name+'_machines']

        except ValueError as e:
            abort(404, message=str(e))
        
        try:
            result = MACHINES_COLLECTION.delete_many({})
            if result.deleted_count == 0:
                abort(404, message="No machines to delete")
            return make_response(jsonify({"message": "All machines deleted successfully"}), 200)
        except Exception as e:
            abort(500, message=str(e))