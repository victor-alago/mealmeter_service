from typing import Dict, Any, Optional
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import PyMongoError
from fastapi import Depends


class MongoDBService:
    def __init__(self):
        from app.config import settings

        try:
            # Add connection timeout and explicitly specify database
            self.client = MongoClient(
                settings.mongodb_uri,
                server_api=ServerApi("1"),
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
            )
            # Test connection with more detailed logging
            self.client.admin.command("ping")
            print("Successfully connected to MongoDB!")
            # Initialize database and collections
            self.db = self.client.get_database("mealmeter")
            # Create profiles collection if it doesn't exist
            if "profiles" not in self.db.list_collection_names():
                self.db.create_collection("profiles")
                print("Created profiles collection")
            self.profiles = self.db.profiles
        except Exception as e:
            print(f"MongoDB connection failed: {str(e)}")
            raise RuntimeError(f"Failed to connect to MongoDB: {str(e)}")

    async def create_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        try:
            # Check if profile already exists
            existing = await self.get_user_profile(user_id)
            if existing:
                return False

            # Add user_id to profile data
            profile_data["user_id"] = user_id

            # Insert new profile
            result = self.profiles.insert_one(profile_data)
            return result.acknowledged
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB operation failed: {str(e)}")

    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        try:
            result = self.profiles.update_one(
                {"user_id": user_id}, {"$set": profile_data}, upsert=False
            )
            return result.acknowledged
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB operation failed: {str(e)}")

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            profile = self.profiles.find_one({"user_id": user_id})
            return profile
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB operation failed: {str(e)}")


def get_mongodb_service():
    return MongoDBService()
