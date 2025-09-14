from pymongo import MongoClient
from bson import ObjectId
import gridfs
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            database_name = os.getenv('DATABASE_NAME', 'avto_bot_db')
            
            self.client = MongoClient(mongodb_uri)
            self.db = self.client[database_name]
            self.fs = gridfs.GridFS(self.db)
            self.records = self.db.records
            print("✅ Connected to MongoDB successfully!")
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            self.client = None
            self.memory_storage = []
    
    def save_record(self, file_data, text_data):
        if self.client:
            # Store image in GridFS
            filename = f"{text_data}_{ObjectId()}.jpg"
            file_id = self.fs.put(file_data, filename=filename)
            
            # Store metadata
            document = {
                'file_id': file_id,
                'text_data': text_data,
                'filename': filename
            }
            
            result = self.records.insert_one(document)
            return True
        else:
            # Fallback to memory storage
            document = {
                'file_data': file_data,
                'text_data': text_data
            }
            self.memory_storage.append(document)
            return True
    
    def search_record(self, search_text):
        if self.client:
            # Search for exact match
            result = self.records.find_one({'text_data': search_text})
            return result
        else:
            # Memory search
            for doc in self.memory_storage:
                if doc['text_data'] == search_text:
                    return doc
            return None
    
    def get_image_file(self, file_id):
        if self.client:
            return self.fs.get(file_id)
        else:
            # For memory storage, we don't have file_id, so return the first match
            return None
    
    def close(self):
        if self.client:
            self.client.close()