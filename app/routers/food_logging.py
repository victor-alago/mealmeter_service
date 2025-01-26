from datetime import date
from enum import Enum
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional, Dict
from pydantic import BaseModel
from app.services.firebase_service import verify_token
from app.services.mongodb_service import MongoDBService, get_mongodb_service

# Dependency to get the current user from the Firebase token
async def get_current_user(token: str = Depends(verify_token)):
    return token

router = APIRouter(prefix="/food-log", tags=["food-logging"])

class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snacks"
    DRINK = "drinks"

class FoodEntry(BaseModel):
    food_name: str
    meal_type: MealType
    calories: float
    serving_size: Optional[str] = None
    date: date

class MealEntries(BaseModel):
    food_name: str
    calories: float
    serving_size: Optional[str] = None

class DailyFoodLog(BaseModel):
    date: date
    total_calories: float
    target_calories: float = 2000
    remaining_calories: float
    meals: Dict[str, List[MealEntries]]

@router.post("/entry", status_code=201)
async def log_food_entry(
    entry: FoodEntry,
    authorization: str = Header(None),
    mongodb_service: MongoDBService = Depends(get_mongodb_service),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization[7:]
    current_user = verify_token(token)

    try:
        # Convert entry to dict and add user_id
        entry_dict = entry.dict()
        entry_dict["date"] = entry_dict["date"].isoformat()
        
        result = await mongodb_service.add_food_entry(current_user["uid"], entry_dict)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to log food entry")

        return {"message": "Food entry logged successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log food entry: {str(e)}")
    

@router.get("/daily/{date}", response_model=DailyFoodLog)
async def get_daily_log(
    date: date,
    authorization: str = Header(None),
    mongodb_service: MongoDBService = Depends(get_mongodb_service),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization[7:]
    current_user = verify_token(token)

    try:
        daily_log = await mongodb_service.get_daily_food_log(current_user["uid"], date)
        if not daily_log:
            return DailyFoodLog(
                date=date,
                total_calories=0,
                target_calories=2000,
                remaining_calories=2000,
                entries=[]
            )
        return daily_log
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily log: {str(e)}")
    

@router.get("/all", response_model=List[DailyFoodLog])
async def get_all_food_logs(
    authorization: str = Header(None),
    mongodb_service: MongoDBService = Depends(get_mongodb_service),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization[7:]
    current_user = verify_token(token)

    try:
        all_logs = await mongodb_service.get_all_user_food_logs(current_user["uid"])
        return all_logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get food logs: {str(e)}")