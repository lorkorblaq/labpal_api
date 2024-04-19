from flask import jsonify
from flask_restful import Resource, reqparse, abort
from datetime import datetime, timedelta
from engine import db_clinical
from bson import ObjectId


ITEMS_COLLECTION = db_clinical['items']
LOT_EXP_COLLECTION = db_clinical['lot Exp']
USERS_COLLECTION = db_clinical['users']

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
lot_exp_parser.add_argument("quantity", type=int, help="Quantity is required", required=False)

class Lot_exp_Push(Resource):
    def post(self, user_id):
        utc_now = datetime.utcnow()
        wat_time = utc_now + timedelta(hours=1)
        args = lot_exp_parser.parse_args()
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        lot_exp = {
                "user":  user.get('name'),
                "item": args["item"], 
                "lot_numb": args["lot_numb"],
                "expiration": args["expiration"],
                "quantity": args["quantity"],
                "created at": wat_time,
            }
        item = ITEMS_COLLECTION.find_one({'item': args['item']})
        if not item:
            return {"message": "Item does not exist, kindly contact Lorkorblaq"}, 400
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
    def get(self):    
        results = list(LOT_EXP_COLLECTION.find())
        # print(results)
        if not results:
            abort(404, message="No Item Available")
        lotexp_list=[]
        # Convert ObjectId to string for JSON serialization
        
        for result in results:
            result["_id"] = str(result["_id"])
            result["expiration"] = result["expiration"].strftime("%Y-%m-%d")
            result["created at"] = result["created at"].strftime("%Y-%m-%d")
            lotexp_list.append(result)
        response_data = {"lotexp": lotexp_list}
        # Create a Flask response with JSON data
        # print((response))
        return response_data, 200