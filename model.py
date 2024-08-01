from pymongo import MongoClient
from datetime import datetime

class MongoDBHandler:
    def __init__(self, connection_string, db_name, collection_name):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_url(self, url, timestamp):
        document = {
            "url": url,
            "timestamp": timestamp
        }
        self.collection.insert_one(document)
