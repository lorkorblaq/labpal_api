from models import Consumption
from models import Items
from flask_restful import Resource, reqparse, abort, fields, marshal_with
from flask import jsonify


items_fields = {
    'id': fields.String,
    'item': fields.String,
    'category': fields.String,
    'in_stock': fields.Integer,
    'unit': fields.String,
    'per_unit': fields.Integer,
    'machine': fields.String,
    'bench': fields.String,
}

class ItemsResource(Resource):
    @marshal_with(items_fields)
    def get(self):
        try:
            items_list = Items.objects.all()

            if not items_list:
                abort(404, message="No Items Available")

            return {"items": items_list}, 200
        except Exception as e:
            return {"message": "Error occurred while fetching items", "error": str(e)}


api.add_resource(ItemsResource, "/api/items/get/")