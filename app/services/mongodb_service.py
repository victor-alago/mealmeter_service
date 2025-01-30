from typing import Dict, Any, List, Optional
from datetime import date, datetime
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

            # Create food_logs collection if it doesn't exist
            if "food_logs" not in self.db.list_collection_names():
                self.db.create_collection("food_logs")
                print("Created food_logs collection")
            self.food_logs = self.db.food_logs

            # Create insights collection if it doesn't exist
            if "user_insights" not in self.db.list_collection_names():
                self.db.create_collection("user_insights")
                print("Created insights collection")
            self.user_insights = self.db.user_insights

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

    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any], is_new: bool = False):
        try:
            # Add user_id to profile data
            profile_data["user_id"] = user_id
            
            # Update or insert the profile
            result = self.profiles.update_one(
                {"user_id": user_id},
                {"$set": profile_data},
                upsert=True  # This creates a new document if it doesn't exist
            )
            
            return result.acknowledged
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB operation failed: {str(e)}")

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            profile = self.profiles.find_one({"user_id": user_id})
            if profile:
                profile["_id"] = str(profile["_id"])  # Convert ObjectId to string
            return profile
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB operation failed: {str(e)}")

    async def add_food_entry(self, user_id: str, entry_data: Dict[str, Any]):
        try:
            date_str = entry_data["date"]
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Get user's TDEE from insights
            user_insights = self.user_insights.find_one({"user_id": user_id})
            target_calories = user_insights["tdee"] if user_insights else 2000  # Default if no insights
            
            new_calories = entry_data["calories"]
            new_entry = {
                "food_name": entry_data["food_name"],
                "calories": new_calories,
                "serving_size": entry_data.get("serving_size"),
                "time_logged": current_time
            }
            
            daily_log = self.food_logs.find_one({
                "user_id": user_id,
                "date": date_str
            })
            
            if not daily_log:
                initial_log = {
                    "user_id": user_id,
                    "date": date_str,
                    "total_calories": new_calories,
                    "target_calories": target_calories,  # Use TDEE from insights
                    "remaining_calories": target_calories - new_calories,
                    "meals": {
                        "breakfast": [],
                        "lunch": [],
                        "dinner": [],
                        "snacks": [],
                        "drinks": []
                    }
                }
                
                meal_type = entry_data["meal_type"].lower()
                initial_log["meals"][meal_type].append(new_entry)
                
                # Insert the new document
                result = self.food_logs.insert_one(initial_log)
                return result.acknowledged
            else:
                # Update existing daily log
                current_total = daily_log.get("total_calories", 0)
                new_total = current_total + new_calories
                remaining = target_calories - new_total  # Use TDEE from insights
                
                meal_type = entry_data["meal_type"].lower()
                
                # Update the existing document
                result = self.food_logs.update_one(
                    {"user_id": user_id, "date": date_str},
                    {
                        "$push": {f"meals.{meal_type}": new_entry},
                        "$set": {
                            "total_calories": new_total,
                            "remaining_calories": remaining,
                            "target_calories": target_calories  # Update target calories
                        }
                    }
                )
                return result.acknowledged
                
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB operation failed: {str(e)}")

    async def get_daily_food_log(
        self, user_id: str, date_param: date
    ) -> Optional[Dict[str, Any]]:
        try:
            date_str = date_param.isoformat()

            # Find the daily log
            daily_log = self.food_logs.find_one({"user_id": user_id, "date": date_str})

            if not daily_log:
                # Return empty daily log structure
                return {
                    "date": date_str,
                    "total_calories": 0,
                    "target_calories": 2000,
                    "remaining_calories": 2000,
                    "meals": {
                        "breakfast": [],
                        "lunch": [],
                        "dinner": [],
                        "snacks": [],
                        "drinks": [],
                    },
                }

            # Remove MongoDB-specific fields
            if "_id" in daily_log:
                daily_log.pop("_id")

            # Convert number types to float/int
            daily_log["total_calories"] = float(daily_log["total_calories"])
            daily_log["target_calories"] = int(daily_log["target_calories"])
            daily_log["remaining_calories"] = float(daily_log["remaining_calories"])

            # Convert nested number types in meals
            for meal_type in daily_log["meals"]:
                for entry in daily_log["meals"][meal_type]:
                    if "calories" in entry:
                        entry["calories"] = float(entry["calories"])

            return daily_log
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB operation failed: {str(e)}")

    async def get_all_user_food_logs(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            # Find all logs for the user
            logs = self.food_logs.find({"user_id": user_id})

            # Convert cursor to list and process each log
            all_logs = []
            for log in logs:
                # Remove MongoDB-specific fields
                if "_id" in log:
                    log.pop("_id")

                # Convert number types to float/int
                log["total_calories"] = float(log["total_calories"])
                log["target_calories"] = int(log["target_calories"])
                log["remaining_calories"] = float(log["remaining_calories"])

                # Convert nested number types in meals
                for meal_type in log["meals"]:
                    for entry in log["meals"][meal_type]:
                        if "calories" in entry:
                            entry["calories"] = float(entry["calories"])

                all_logs.append(log)

            # Sort by date (most recent first)
            all_logs.sort(key=lambda x: x["date"], reverse=True)

            return all_logs
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB operation failed: {str(e)}")

    async def update_user_insights(self, user_id: str, insights_data: Dict[str, Any]):
        try:
            result = self.user_insights.update_one(
                {"user_id": user_id},
                {"$set": insights_data},
                upsert=True
            )
            return result.acknowledged
        except PyMongoError as e:
            raise RuntimeError(f"MongoDB operation failed: {str(e)}")


def get_mongodb_service():
    return MongoDBService()
