from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from bson import ObjectId
from datetime import datetime
from engine import org_users_db, client, paystack_secret_key
import os
import requests
from dotenv import load_dotenv, find_dotenv
import hashlib
import hmac
import logging

# Load environment variables
load_dotenv(find_dotenv())

# Initialize Flask app and API
app = Flask(__name__)
api = Api(app)

# Constants
PAYSTACK_URL = 'https://api.paystack.co'

# MongoDB Collections
USERS_COLLECTION = org_users_db['users']
ORG_COLLECTION = org_users_db['org']
CUSTOMER_COLLECTION = org_users_db['customers']
# TRANSACTIONS_COLLECTION = org_users_db['transactions']


# Configure logging
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler("webhook.log"),  # Log to a file
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

class Webhook(Resource):
    def post(self):
        payload = request.get_json()
        # print(payload['data'])
        signature = request.headers.get('x-paystack-signature')

        if not self.verify_signature(payload, signature):
            logger.error('Invalid signature')
            return {'status':'error', 'message':'Invalid signature'}, 400

        event = payload.get('event')
        logger.info(f'Received event: {event}')
        try:
            if event == 'subscription.create':
                self.handle_subscription_create(payload['data'])
            elif event == 'charge.success':
                self.handle_charge_success(payload['data'])
            elif event == 'subscription.not_renew':
                self.handle_subscription_not_renew(payload['data'])
            # Handle other events as needed
        except Exception as e:
            logger.error(f'Error handling event {event}: {str(e)}')
            return {'status':'error', 'message':'Error processing event'}, 500
        return {'status':'success'}, 200

    def verify_signature(self, payload, signature):
        secret_key = paystack_secret_key
        computed_signature = hmac.new(
            secret_key.encode('utf-8'),
            msg=request.data,
            digestmod=hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(computed_signature, signature)

    def handle_subscription_create(self, data):
        subscription_code = data['subscription_code']
        customer_email = data['customer']['email']
        logger.info(f'Subscription created: {subscription_code} for {customer_email}')
        # Add your logic here to handle the subscription creation

    def handle_charge_success(self, data):
        print(data)
        transaction_reference = data['reference'] 
        status = data['status']
        amount = data['amount']
        paid_at = data['paid_at']
        created_at = data['created_at']
        plan = data['plan']['name']
        customer_email = data['customer']['email']
        customer_code = data['customer']['customer_code']
        authorization_code = data['authorization']['authorization_code']
        last4 = data['authorization']['last4']
        bank = data['authorization']['bank']
        card_type = data['authorization']['card_type']
        plan = data['plan']['name']
        next_payment_date, subscription_code = self.get_payment_date_and_sub(customer_email)
        interval = data['plan']['interval']
        customer_data = {
            'email': customer_email,
            'amount': amount,
            'plan': plan,
            'paid_at': paid_at,
            'authorization_code': authorization_code,
            'subscription_code': subscription_code,
            'next_payment_date': next_payment_date
        }
        data={
            'status': status,
            'transaction ref': transaction_reference,
            'email': customer_email, 
            'customer_code': customer_code,
            'amount': amount,
            'plan': plan,
            'paid_at': paid_at,
            'created_at': created_at,
            'authorization_code': authorization_code,
            'next_payment_date': next_payment_date,
            'last4': last4,
            'card_type': card_type,
            'bank': bank,
            }
        # print(data, customer_data)
        org_name = ORG_COLLECTION.find_one({'creators_email': customer_email})['org_name']
        org_db = client[f"{org_name}_db"]
        # print(org_db)
        TRANSACTIONS_COLLECTION = org_db['transactions']
        TRANSACTIONS_COLLECTION.insert_one(data)
        ORG_COLLECTION.update_one({'creators_email': customer_email}, 
                                  {'$set': {'subscription': plan}})
        CUSTOMER_COLLECTION.update_one(
            {'email': customer_email},
            {'$set': customer_data},
            upsert=True)
        logger.info(data)
        # Add your logic here to handle successful charge

    def handle_subscription_not_renew(self, data):
        subscription_code = data['subscription_code']
        amount = data['amount']
        plan = data['plan']['name']
        customer_email = data['customer']['email']
        logger.info(f'Subscription not renewed: {subscription_code} for {customer_email}')
        # Add your logic here to handle the subscription not renewed


    def get_payment_date_and_sub(self, customer_email):
        url = f'{PAYSTACK_URL}/customer/{customer_email}'
        headers = {
            'Authorization': f'Bearer {paystack_secret_key}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        response_data = response.json()
        
        if 'data' in response_data and 'subscriptions' in response_data['data']:
            subscriptions = response_data['data']['subscriptions']
            if subscriptions:
                next_payment_date = subscriptions[0].get('next_payment_date')
                subscription_code = subscriptions[0].get('subscription_code')
            else:
                next_payment_date = None
                subscription_code = None
        else:
            next_payment_date = None
            subscription_code = None

        return next_payment_date, subscription_code