from dotenv import load_dotenv
from pymongo import MongoClient
import os   
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME","md")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

users_collection = db["users"]
report_collection = db["reports"]
diagnosis_collection = db["diagnosis"]