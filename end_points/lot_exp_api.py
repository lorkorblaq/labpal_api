from flask import jsonify
from flask_restful import Resource, reqparse, abort
from datetime import datetime, timedelta
from engine import db_clinical, client, org_users_db, get_org_name
from bson import ObjectId


USERS_COLLECTION = org_users_db['users']

lot_exp_parser = reqparse.RequestParser()
def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Not a valid date: '{0}'.".format(s))
lot_exp_parser.add_argument("item", type=str, help="Item is required", 
required=False)
lot_exp_parser.add_argument("lot_numb", type=str, help="Lot is required", 
required=False)
lot_exp_parser.add_argument("expiration", type=valid_date, help="expiration is required", required=False)

class Lot_exp_Push(Resource):
    def post(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            ITEMS_COLLECTION = client[org_name + '_db'][lab_name + '_items']
            LOT_EXP_COLLECTION = client[org_name + '_db'][lab_name + '_lot_exp']
        except ValueError as e:
            abort(404, message=str(e))

        utc_now = datetime.now()
        args = lot_exp_parser.parse_args()
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        lot_exp = {
                "item": args["item"], 
                "lot_numb": args["lot_numb"],
                "expiration": args["expiration"],
                "quantity": 0,
                "created at": utc_now,
            }
        item = ITEMS_COLLECTION.find_one({'item': args['item']})
        if not item:
            return {"message": "Item does not exist, kindly contact Lorkorblaq"}, 400
        elif LOT_EXP_COLLECTION.find_one({'lot_numb': args['lot_numb']}):
            return {"message": "Lot number already exists"}, 400
        else:
            try:
                inserted_id = LOT_EXP_COLLECTION.insert_one(lot_exp).inserted_id
                inserted_id = str(inserted_id)
                response = {
                    "message": "lot exp created successfully",
                    "lot_exp_id": inserted_id
                    }
                return response, 200
            except Exception as e:
                return {"message": "Error occured while pushing item", "error": str(e)}
            
class Lot_exp_Get(Resource):
    def get(self, user_id, lab_name):
        try:
            org_name = get_org_name(user_id)
            ITEMS_COLLECTION = client[org_name + '_db'][lab_name + '_items']
            LOT_EXP_COLLECTION = client[org_name + '_db'][lab_name + '_lot_exp']
        except ValueError as e:
            abort(404, message=str(e))    
        lot_exps = list(LOT_EXP_COLLECTION.find())
        # print(results)
        if not lot_exps:
            abort(404, message="No Item Available")
        lotexp_list=[]
        # Convert ObjectId to string for JSON serialization
        
        for lot_exp in lot_exps:
            lot_exp["_id"] = str(lot_exp["_id"])
            lot_exp["item"] = str(lot_exp["item"])
            lot_exp["quantity"] = lot_exp["quantity"]
            lot_exp["expiration"] = lot_exp["expiration"].strftime("%Y-%m-%d")
            lot_exp["created at"] = lot_exp["created at"].strftime("%Y-%m-%d")
            lotexp_list.append(lot_exp)
        response_data = {"lotexp": lotexp_list}
        # Create a Flask response with JSON data
        # print((response))
        return response_data, 200