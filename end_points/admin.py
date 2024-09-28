from flask_restful import Resource, Api, reqparse
from bson import ObjectId
from datetime import datetime
from engine import org_users_db, get_org_name, client, paystack_secret_key


class Health(Resource):
    def get(self):
        # Here you can add any additional checks such as database connectivity,
        # third-party API status, etc., if required
        status = {
            "status": "healthy",
            "message": "Service is running smoothly",
            "version": "1.0.0"  # Optionally, include versioning info
        }
        return status, 200