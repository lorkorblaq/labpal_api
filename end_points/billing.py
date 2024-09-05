from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse
from bson import ObjectId
from datetime import datetime
from engine import org_users_db, get_org_name, client, paystack_secret_key
import os
import requests

# Load environment variables
print(paystack_secret_key)
# Initialize Flask app and API
app = Flask(__name__)
api = Api(app)

# Constants
PAYSTACK_URL = 'https://api.paystack.co'

# MongoDB Collections
USERS_COLLECTION = org_users_db['users']
ORG_COLLECTION = org_users_db['org']
CUSTOMER_COLLECTION = org_users_db['customers']

# Request Parser Setup
billing_parser = reqparse.RequestParser()
billing_parser.add_argument("item", type=str, help="Item is required", required=True)

class Customer(Resource):
    def post(self, org_id):
        if not request.is_json:
            return jsonify({"status": False, "message": "Content-Type must be application/json"}), 400
        
        org = ORG_COLLECTION.find_one({'_id': ObjectId(org_id)}, {'org_name': 1, 'creator': 1})
        if not org:
            return {"status": False, "message": "Organization not found"}, 404
        print(org_id)

        user_id = org.get('creator')
        print(user_id)
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)}, {'email': 1, 'firstname': 1, 'lastname': 1})
        if not user:
            return {"status": False, "message": "User not found"}, 404

        customer_email = user.get('email')
        firstname = user.get('firstname')
        lastname = user.get('lastname')

        customer_response = self.create_customer(org_id, user_id, firstname, lastname, customer_email)
        return customer_response
    def create_customer(self, org_id, user_id, firstname, lastname, customer_email):
        url = f'{PAYSTACK_URL}/customer'
        headers = {
            'Authorization': f'Bearer {paystack_secret_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'email': customer_email,
            'first_name': firstname,
            'last_name': lastname
        }

        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        if response.status_code == 200 and 'data' in response_data:
            customer_code = response_data['data']['customer_code']
            subscriptions = response_data['data'].get('subscriptions', [])

            # Extract subscription_code if there are any subscriptions
            subscription_code = subscriptions[0]['subscription_code'] if subscriptions else None

            # Insert into local MongoDB collection
            customer_data = {
                'created_at': datetime.now(),
                'org_id': org_id,
                'user_id': user_id,
                'email': customer_email,
                'paystack_customer_id': customer_code,
                'subscription_code': subscription_code
            }
            CUSTOMER_COLLECTION.insert_one(customer_data)
            return response_data
        else:
            return {"status": False, "message": "Customer creation failed", "details": response_data}, response.status_code

    def get(self, org_id):
        org = ORG_COLLECTION.find_one({'_id': ObjectId(org_id)}, {'creators_email': 1})
        if not org:
            return {"status": False, "message": "Organization not found"}, 404

        customer_email = org.get('creators_email')
        print(customer_email)
        url = f'{PAYSTACK_URL}/customer/{customer_email}'
        headers = {
            'Authorization': f'Bearer {paystack_secret_key}',
            'Content-Type': 'application/json'
            }
        response = requests.get(url, headers=headers)
        return response.json()


class Subscription(Resource):
    PLAN_CODES = {
        "Basic_monthly_plan": "PLN_7r5ug8q5qbwhop9",
        # "Basic_monthly_plan": "PLN_lf80uf90ipqcv7g", test
        "Basic_annual_plan": "PLN_b46brbmrrop8sl8",
        "Premium_monthly_plan": "PLN_s9huwzlc4roam52",
        "Premium_annual_plan": "PLN_fca1zrdnjpdinc9"

    }
    def post(self, org_id, plan):
        org = ORG_COLLECTION.find_one({'_id': ObjectId(org_id)}, {'org_name': 1, 'creator': 1, 'creators_email': 1, 'subscription': 1})
        if not org:
            return {"status": False, "message": "Organization not found"}, 404
        user_id = org.get('creator')

        customer_email = org.get('creators_email')
        subscription = self.PLAN_CODES.get(plan)
        print(subscription)

        if not subscription:
            return {"status": False, "message": "Subscription plan not found"}, 404

        response = self.create_subscription(customer_email, subscription)
        return response

    def get(self, org_id):
        org = ORG_COLLECTION.find_one({'_id': ObjectId(org_id)}, {'creators_email': 1, })
        if not org:
            return {"status": False, "message": "Organization not found"}, 404

        customer_email = org.get('creators_email')
        url = f'{PAYSTACK_URL}/subscription/{customer_email}'
        headers = {
            'Authorization': f'Bearer {paystack_secret_key}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        return response

    def create_subscription(self, customer_email, subscription):
        url = f'{PAYSTACK_URL}/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {paystack_secret_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'email': customer_email,
            'amount': 500000,
            'plan': subscription,
        }
        response = requests.post(url, headers=headers, json=data)
        data = {
            'status': response.status_code == 200,

        }
        return response.json()


class TransactionSuccess(Resource):
    def get(self, org_id):
        org = ORG_COLLECTION.find_one({'_id': ObjectId(org_id)}, {'creators_email': 1, 'org_name': 1})
        if not org:
            return {"status": False, "message": "Organization not found"}, 404

        org_name = org.get('org_name')
        org_db = client[f"{org_name}_db"]
        TRANSACTION = org_db['transactions']

        transactions = list(TRANSACTION.find({'status': 'success'}, {'_id': 0}))
        return {"status": True, "transactionsSuccess": transactions}
    
class Transactions(Resource):
    def get(self, org_id):
        org = ORG_COLLECTION.find_one({'_id': ObjectId(org_id)}, {'creators_email': 1, 'org_name': 1})
        if not org:
            return {"status": False, "message": "Organization not found"}, 404

        org_name = org.get('org_name')
        org_db = client[f"{org_name}_db"]
        TRANSACTION = org_db['transactions']

        transactions = list(TRANSACTION.find({}, {'_id': 0})) 
        return {"status": True, "transactions": transactions}

    


