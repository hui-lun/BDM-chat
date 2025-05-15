from pymongo import MongoClient
MONGO_URI = "mongodb://admin:password@192.168.1.166:27017/admin"
client = MongoClient(MONGO_URI)