import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")

client = MongoClient(mongo_uri)
print(client)
db = client["glacier_gorillas"]

# Collections
trails_collection = db.trails
users_collection = db.users