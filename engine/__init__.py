from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv, find_dotenv
from bson.objectid import ObjectId
import os
load_dotenv(find_dotenv())

uri_development = os.getenv('URI_DEVELOPMENT')
uri_production = os.getenv('URI_PRODUCTION')

client = MongoClient(uri_production)
try:    
    client.admin.command('ping')
    print("You successfully connected to Clinicalx MongoDB!")
except Exception as e:  
    print(e)

db_clinical = client.clinicalx
org_users_db = client.org_users

def get_org_name(user_id):
    user = org_users_db['users'].find_one({'_id': ObjectId(user_id)})
    if not user:
        raise ValueError(f"No user found with user_id: {user_id}")
    
    org = org_users_db['org'].find_one({'_id': ObjectId(user.get('org_id'))})
    if not org:
        raise ValueError(f"No organisation found with org_id: {user.get('org_id')}")
    
    orgName = org['org_name']
    return orgName