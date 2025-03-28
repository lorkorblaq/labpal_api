from flask import jsonify, request
from flask_restful import Resource, reqparse, abort, fields, marshal_with
from bson import ObjectId
from datetime import datetime, timezone
from zoneinfo import ZoneInfo  # Python 3.9+from engine import client, org_users_db, get_org_name
from engine import client, org_users_db, get_org_name
from pymongo import DESCENDING
from mailer import app_mail



# SHIPMENTS_COLLECTION = db_clinical['channels']
# ITEMS_COLLECTION = db_clinical['items']

USERS_COLLECTION = org_users_db['users']
ORG_COLLECTION = org_users_db['organisations']

shipments_parser = reqparse.RequestParser()

shipments_parser.add_argument("created_at", type=str, required=False)
shipments_parser.add_argument("create_lat_lng", type=str, help="Latitude and Longitude are required", required=False)
shipments_parser.add_argument("shipment_id", type=str, help="shipment id is required", required=False)
shipments_parser.add_argument("top", type=str, help="Type of package is required", required=False)
shipments_parser.add_argument("numb_of_packs", type=int, help="Number of packages is required", required=False)
shipments_parser.add_argument("weight", type=float, help="Weight of packages is required", required=False)
shipments_parser.add_argument("vendor", type=str, help="Vendor is required", required=False)
shipments_parser.add_argument("price", type=str, required=False)

shipments_parser.add_argument("vendor_name", type=str, required=False)

shipments_parser.add_argument("picked_by", type=str, required=False)
shipments_parser.add_argument("pickup_loc", type=str, help="Pickup location is required", required=False)
shipments_parser.add_argument("pickup_time", type=str, required=False)
shipments_parser.add_argument("pickup_lat_lng", type=str, help="Location is required", required=False)

shipments_parser.add_argument("dropoff_by", type=str, required=False)
shipments_parser.add_argument("dropoff_loc", type=str, help="Drop off location is required", required=False)
shipments_parser.add_argument("dropoff_time", type=str, required=False)
shipments_parser.add_argument("dropoff_lat_lng", type=str, help="Location is required", required=False)

shipments_parser.add_argument("duration", type=int, required=False)
shipments_parser.add_argument("description", type=str, required=False)
shipments_parser.add_argument("completed", type=str, required=False)

class ShipmentsPush(Resource):
    def post(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            SHIPMENTS_COLLECTION = client[org_name+'_db']['shipments']
            LAB_COLLECTION = client[org_name+'_db']["labs"]
        except ValueError as e:
            abort(404, message=str(e))
        try:
            args = shipments_parser.parse_args()
            user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
            if not user:
                return {"message": "User does not exist, kindly contact admin"}, 400
            elif not org_name:
                return {"message": "Organisation does not exist, kindly contact Lorkorblaq"}, 400
            labs = user.get('labs_access')
            if lab_name in labs:
                pass

            name = user.get('firstname') + ' ' + user.get('lastname')
            print('user_id2', user_id)
            wat_now = datetime.now(ZoneInfo("UTC"))
            print('wat', wat_now)           
            fromLab = LAB_COLLECTION.find_one({'lab_name': args['pickup_loc'].lower()}, {'lab_name': 1, 'region': 1})
            toLab = LAB_COLLECTION.find_one({'lab_name': args['dropoff_loc'].lower()}, {'lab_name': 1, 'region': 1})

            # Ensure fromLab and toLab exist before calling .get()
            fromLabName = fromLab.get('lab_name') if fromLab else None
            toLabName = toLab.get('lab_name') if toLab else None
            print('fromLab', fromLabName)
            print('toLab', toLabName)

            # Check if labs exist
            if not fromLabName:
                return {"message": f"The {args['pickup_loc']} location not found"}, 400
            if not toLabName:
                return {"message": f"The {args['dropoff_loc']} location not found"}, 400

            # Prevent pickup and dropoff locations from being the same
            if fromLabName == toLabName:
                return {"message": "Pickup location and dropoff location cannot be the same"}, 400

            # Extract regions
            fromRegion = fromLab.get('region')
            toRegion = toLab.get('region')

            # Define the pricing based on regions
            REGION_PRICING = {
                "north": 18000,
                "west": 8000,
                "east": 9000
            }

            if fromLabName == "central_store":
                price = REGION_PRICING.get(toRegion, 0)  # Default to 0 if region is unknown
                firstInitialToRegion = toRegion[0].upper()
                Rcode = f"L{firstInitialToRegion}-{wat_now.strftime('%y%m%d%H%M')}-"
                regionCode = f"LN" if toRegion.lower() == "north" else f"LW" if toRegion.lower() == "west" else f"LE" if toRegion.lower() == "east" else f"LS" if toRegion.lower() == "south" else f"LU"
            elif toLabName == "central_store":
                price = REGION_PRICING.get(fromRegion, 0)
                firstInitialFromRegion = fromRegion[0].upper()
                Rcode = f"F{firstInitialFromRegion}-{wat_now.strftime('%y%m%d%H%M')}-"
                regionCode = f"FN" if fromRegion.lower() == "north" else f"FW" if fromRegion.lower() == "west" else f"FE" if fromRegion.lower() == "east" else f"FS" if fromRegion.lower() == "south" else f"FU"
            elif fromLabName != "central_store" and toLabName != "central_store":
                price = 12000
                firstInitialFromRegion = fromRegion[0].upper()
                firstInitialToRegion = toRegion[0].upper()
                Rcode = f"{firstInitialFromRegion}{firstInitialToRegion}-{wat_now.strftime('%y%m%d%H%M')}-"
                regionCode = f"N{toRegion[0].upper()}" if fromRegion.lower() == "north" else \
                             f"W{toRegion[0].upper()}" if fromRegion.lower() == "west" else \
                             f"E{toRegion[0].upper()}" if fromRegion.lower() == "east" else \
                             f"S{toRegion[0].upper()}" if fromRegion.lower() == "south" else \
                             f"U{toRegion[0].upper()}"

            # Generate the Serial Number for the Current Month
            current_month = wat_now.strftime('%Y-%m')
            latest_shipment = SHIPMENTS_COLLECTION.find_one(
                {
                    "created_at": {"$gte": datetime(wat_now.year, wat_now.month, 1)},
                    "shipment_id": {"$regex": f"^{regionCode}"}  # Filter by region code prefix
                },
                sort=[("created_at", DESCENDING)]
            )

            if latest_shipment and "shipment_id" in latest_shipment:
                try:
                    last_serial = int(latest_shipment["shipment_id"].split("-")[-1])  # Extract last serial
                    new_serial = last_serial + 1
                except ValueError:
                    new_serial = 1  # Fallback in case of parsing issue
            else:
                new_serial = 1  # Start from 1 if no shipments exist for the month

            # Final `shipment_id` with serial number
            shipment_id = f"{Rcode}{new_serial:03d}"  # Formats as "001", "002", etc.

            data = {
                "created_by": name,
                "created_at": wat_now,
                "shipment_id": shipment_id,
                "top": args['top'],
                "numb_of_packs": args['numb_of_packs'],
                "weight": args['weight'],
                "vendor": args['vendor'],
                "pickup_loc": fromLab.get('lab_name'),
                "dropoff_loc": toLab.get('lab_name'),
                "price": price,
                "from_region": fromRegion,
                "to_region": toRegion,
                "create_lat_lng": args['create_lat_lng'],
                "description": args['description'],
                "status": 'pending'
            }
            try:
                print('shipments_data', data)
                result = SHIPMENTS_COLLECTION.insert_one(data)
                print('resultship', result)
                # Verify insert success
                if result.inserted_id:
                    inserted_id = str(result.inserted_id)
                    response = {
                        "message": "Shipment created successfully",
                        "tracking_id": inserted_id
                    }
                    print('response', response)
                    return response, 200
                else:
                    print("🚨 MongoDB insert failed!")  # Debugging log
                    return {"message": "Failed to create shipment, please try again."}, 500  

            except Exception as e:
                print("🔥 Error during MongoDB insert:", str(e))  # Print full error
                return {"message": "Error occurred while creating shipment", "error": str(e)}, 500

        except Exception as e:
            return {"message": "Error occurred while creating shipment", "error": str(e)}

class ShipmentsPut(Resource):    
    def put(self, user_id, lab_name):
        args = shipments_parser.parse_args()
        shipment_id = args.get('shipment_id')
        try:
            org_name = get_org_name(user_id)
            SHIPMENTS_COLLECTION = client[org_name+'_db']['shipments']
        except ValueError as e:
            abort(404, message=str(e))

        utc_now = datetime.now(ZoneInfo("UTC"))
        wat_now = utc_now.astimezone(ZoneInfo("Africa/Lagos"))        
        shipment = SHIPMENTS_COLLECTION.find_one({'shipment_id': shipment_id})
        if not shipment:
            abort(404, message="Shipment not found")

        # Update the shipment with new values
        for key, value in args.items():
            if value is not None:
                if isinstance(value, str) and value.strip() == '':
                    value = None
                shipment[key] = value

        # picked = args.get('picked_by')
        # if picked:
        #     shipment['picked_by'] = picked
        #     shipment['pickup_time'] = wat_now
        #     shipment['updated_at'] = wat_now
        #     shipment['status'] = 'in-transit'

        dropped = args.get('dropoff_by')
        if dropped:
            shipment['dropoff_by'] = dropped
            shipment['dropoff_time'] = wat_now
            shipment['updated_at'] = wat_now
            shipment['status'] = 'delivered'

            # Calculate the duration between pickup_time and dropoff_time
            created_at = shipment.get('created_at')
            dropoff_time = shipment.get('dropoff_time')
            if created_at and dropoff_time:
                duration = dropoff_time - created_at
                total_minutes = duration.total_seconds() // 60  # Convert to minutes
                shipment['duration'] = total_minutes
            # if pickup_time and dropoff_time:
            #     duration = dropoff_time - pickup_time
            #     print('duration', duration)
            #     duration_days = f"{duration.days}D"
            #     duration_hours = f"{duration.seconds // 3600}H"
            #     duration_minutes = f"{(duration.seconds % 3600) // 60}M"
            #     duration_seconds = f"{duration.seconds % 60}S"

                # shipment['duration'] = f"{duration_days}:{duration_hours}:{duration_minutes}:{duration_seconds}"


        SHIPMENTS_COLLECTION.replace_one({'shipment_id': shipment_id}, shipment)
        response = {"message": "Your data has been updated successfully"}
        
        return response, 200
    
class ShipmentsGetOne(Resource):
    def get(self, user_id, lab_name, shipment_id):
        try:
            org_name = get_org_name(user_id)
            SHIPMENTS_COLLECTION = client[org_name + '_db']['shipments']
        except ValueError as e:
            abort(404, message=str(e))
        try:
            shipment = SHIPMENTS_COLLECTION.find_one({'_id': ObjectId(shipment_id)})
            if not shipment:
                abort(404, message="Shipment not found")

            # Convert timestamps to Africa/Lagos time zone
            def convert_to_lagos_time(timestamp):
                if timestamp:
                    # Ensure the timestamp is treated as UTC if it's naive
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    # Convert to Africa/Lagos timezone
                    return timestamp.astimezone(ZoneInfo("Africa/Lagos")).strftime("%Y-%m-%d %H:%M:%S")
                return None
            response = {
                "id": str(shipment['_id']),
                "created_at": convert_to_lagos_time(shipment.get('created_at')),
                "created_by": shipment.get('created_by', 'Unknown User'),
                "picked_by": shipment.get('picked_by', 'Not yet picked'),
                "dropoff_by": shipment.get('dropoff_by', 'Not yet dropped'),
                "shipment_id": shipment.get('shipment_id', 'Unknown shipment id'),
                "top": shipment.get('top', 'Unknown type of package'),
                "numb_of_packs": shipment.get("numb_of_packs", 'Unknown numb of packs'),
                "price": shipment.get("price", 'Unknown price'),
                "weight": shipment.get("weight", 'Unknown weight'),
                "vendor": shipment.get("vendor", 'Unknown vendor'),
                "pickup_loc": shipment.get("pickup_loc", 'Not yet picked'),
                "dropoff_loc": shipment.get("dropoff_loc", 'Not yet dropped'),
                "from_region": shipment.get("from_region", 'Unknown region'),
                "to_region": shipment.get("to_region", 'Unknown region'),
                "pickup_time": convert_to_lagos_time(shipment.get('pickup_time')),
                "dropoff_time": convert_to_lagos_time(shipment.get('dropoff_time')),
                "create_lat_lng": shipment.get('create_lat_lng', 'location'),
                "pickup_lat_lng": shipment.get('pickup_lat_lng', 'Not yet picked'),
                "dropoff_lat_lng": shipment.get('dropoff_lat_lng', 'Not yet dropped'),
                "duration": shipment.get('duration', 0),
                "description": shipment.get('description', 'No Description'),
                "status": shipment.get('status', "not yet created")
            }
            return response, 200
        except Exception as e:
            return {"message": "Error occurred while fetching shipment", "error": str(e)}

class ShipmentsGetAll(Resource):
    def get(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            SHIPMENTS_COLLECTION = client[org_name + '_db']['shipments']
        except ValueError as e:
            abort(404, message=str(e))

        shipments = list(SHIPMENTS_COLLECTION.find())
        if not shipments:
            abort(404, message="Shipment not found")

        # Convert timestamps to Africa/Lagos time zone
        def convert_to_lagos_time(timestamp):
            if timestamp:
                # Ensure the timestamp is treated as UTC if it's naive
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                # Convert to Africa/Lagos timezone
                return timestamp.astimezone(ZoneInfo("Africa/Lagos")).strftime("%Y-%m-%d %H:%M:%S")
            return None
        # print("Before conversion:", shipments.get('created_at'))
        # print("After conversion:", convert_to_lagos_time(shipments.get('created_at')))
        shipment_list = [{
            "id": str(shipment['_id']),
            "created_at": convert_to_lagos_time(shipment.get('created_at')),
            "created_by": shipment.get('created_by', 'Unknown User'),
            "picked_by": shipment.get('picked_by', 'Not yet picked'),
            "dropoff_by": shipment.get('dropoff_by', 'Not yet received'),
            "shipment_id": shipment.get('shipment_id', 'Unknown shipment id'),
            "top": shipment.get('top', 'Unknown type of package'),
            "numb_of_packs": shipment.get("numb_of_packs", 'Unknown numb of packs'),
            "price": shipment.get("price", 'Unknown price'),
            "weight": shipment.get("weight", 'Unknown weight'),
            "vendor": shipment.get("vendor", 'Unknown vendor'),
            "pickup_loc": shipment.get("pickup_loc", 'Not yet picked'),
            "dropoff_loc": shipment.get("dropoff_loc", 'Not yet dropped'),
            "from_region": shipment.get("from_region", 'Unknown region'),
            "to_region": shipment.get("to_region", 'Unknown region'),
            "pickup_time": convert_to_lagos_time(shipment.get('pickup_time')),
            "dropoff_time": convert_to_lagos_time(shipment.get('dropoff_time')),
            "create_lat_lng": shipment.get('create_lat_lng', 'location'),
            "pickup_lat_lng": shipment.get('pickup_lat_lng', 'Not yet picked'),
            "dropoff_lat_lng": shipment.get('dropoff_lat_lng', 'Not yet received'),
            "duration": shipment.get('duration', 0),
            "description": shipment.get('description', 'No Description'),
            "status": shipment.get('status', "not yet created"),
        } for shipment in shipments]

        response = {"shipments": shipment_list}
        return response, 200

class ShipmentsDel(Resource):
    def delete(self, user_id, shipment_id):
        try:
            org_name = get_org_name(user_id)
            SHIPMENTS_COLLECTION = client[org_name+'_db']['shipments']
        except ValueError as e:
            abort(404, message=str(e))
        
        # Check the status of the shipment
        shipment = SHIPMENTS_COLLECTION.find_one({'_id': ObjectId(shipment_id)})
        if not shipment:
            abort(404, message="Shipment not found")
        if shipment.get('status') == 'delivered':
            return {"message": "Cannot delete a shipment with status 'delivered'"}, 400
        
        SHIPMENTS_COLLECTION.delete_one({'_id': ObjectId(shipment_id)})
        response = {"message": "Shipment has been deleted successfully"}
        return response, 200
     

class VendorCreate(Resource):
    def post(self, user_id):
        try:
            user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
            if not user:
                return {"message": "User does not exist, kindly contact admin"}, 400
            
            org_name = get_org_name(user_id)
            VENDOR_COLLECTION = client[org_name+'_db']['vendors']
        except ValueError as e:
            abort(404, message=str(e))
        args = shipments_parser.parse_args()
        vendor = args.get('vendor_name')
        if not vendor:
            return {"message": "Vendor name is required"}, 400
        vendor_data = {"name": vendor}
        result = VENDOR_COLLECTION.insert_one(vendor_data)
        if result.inserted_id:
            return {"message": "Vendor created successfully"}, 200
        else:
            return {"message": "Failed to create vendor, please try again."}, 500

class VendorGetAll(Resource):
    def get(self, user_id):
        try:
            org_name = get_org_name(user_id)
            VENDOR_COLLECTION = client[org_name+'_db']['vendors']
        except ValueError as e:
            abort(404, message=str(e))
        vendors = list(VENDOR_COLLECTION.find())
        if not vendors:
            abort(404, message="Vendors not found")
        vendor_list = [{
            "id": str(vendor['_id']),
            "name": vendor.get('name', 'Unknown Vendor'),
        } for vendor in vendors]

        response = {"vendors": vendor_list}
        return response, 200
