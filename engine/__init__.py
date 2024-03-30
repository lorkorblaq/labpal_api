from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
# from dotenv import load_dotenv, find_dotenv
import os
password="518Oloko."
uri_production = "mongodb://clinicalx:Ilupeju2024@localhost:27017"
uri_development = "mongodb+srv://clinicalx:518Oloko.@clinicalx.aqtbwah.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri_development)
try:
    client.admin.command('ping')
    print("You successfully connected to Clinicalx MongoDB!")
except Exception as e:  
    print(e)

db_clinical = client.clinicalx