from datetime import date
from enum import Enum
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from pydantic import BaseModel, root_validator
from app.services.firebase_service import verify_token
from app.services.mongodb_service import MongoDBService, get_mongodb_service


# Dependency to get the current user from the Firebase token
async def get_current_user(token: str = Depends(verify_token)):
    return token


router = APIRouter(prefix="/users", tags=["profile"])


# Enums and Models
class Gender(str, Enum):
    male = "male"
    female = "female"


class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    light = "lightly active"
    moderate = "moderately active"
    active = "very active"
    extra = "extra active"


class GoalType(str, Enum):
    loss = "weight loss"
    gain = "weight gain"
    maintenance = "weight maintenance"
    muscle = "muscle gain"


class DietaryPreference(str, Enum):
    standard = "standard"
    vegetarian = "vegetarian"
    vegan = "vegan"
    keto = "keto"
    paleo = "paleo"


class HealthMetrics(BaseModel):
    medical_conditions: List[str] = []
    medications: List[str] = []


class UserProfileCreate(BaseModel):
    gender: Gender
    birthdate: date
    height_cm: float
    weight_kg: float
    activity_level: ActivityLevel
    goal: GoalType
    target_weight: Optional[float] = None
    weekly_goal_kg: Optional[float] = None
    diet_type: Optional[DietaryPreference] = None
    food_preferences: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    health_metrics: Optional[HealthMetrics] = None

    @root_validator(skip_on_failure=True)
    def validate_goals(cls, values):
        goal = values.get("goal")
        weight_kg = values.get("weight_kg")
        target_weight = values.get("target_weight")
        weekly_goal_kg = values.get("weekly_goal_kg")

        if goal == GoalType.maintenance:
            # For maintenance, always set these values regardless of input
            values["target_weight"] = weight_kg
            values["weekly_goal_kg"] = 0.0
        else:
            # For non-maintenance goals, require both values
            if target_weight is None:
                raise ValueError("target_weight is required for non-maintenance goals")
            if weekly_goal_kg is None:
                raise ValueError("weekly_goal_kg is required for non-maintenance goals")

            # Validate target weight and weekly goal based on goal type
            if goal in [GoalType.gain, GoalType.muscle]:
                if target_weight <= weight_kg:
                    raise ValueError(
                        "target_weight must be greater than current weight for weight/muscle gain"
                    )
                if weekly_goal_kg <= 0:
                    raise ValueError(
                        "weekly_goal_kg must be positive for weight/muscle gain"
                    )
            elif goal == GoalType.loss:
                if target_weight >= weight_kg:
                    raise ValueError(
                        "target_weight must be less than current weight for weight loss"
                    )
                if weekly_goal_kg <= 0:
                    raise ValueError("weekly_goal_kg must be positive for weight loss")
        return values


class UserProfileUpdate(BaseModel):
    gender: Optional[Gender] = None
    birthdate: Optional[date] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    goal: Optional[GoalType] = None
    target_weight: Optional[float] = None
    weekly_goal_kg: Optional[float] = None
    diet_type: Optional[DietaryPreference] = None
    food_preferences: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    health_metrics: Optional[HealthMetrics] = None

    @root_validator(skip_on_failure=True)
    def validate_goals_update(cls, values):
        goal = values.get("goal")
        weight_kg = values.get("weight_kg")
        target_weight = values.get("target_weight")
        weekly_goal_kg = values.get("weekly_goal_kg")

        if goal is not None:
            if goal == GoalType.maintenance:
                # For maintenance, always set these values regardless of input
                values["target_weight"] = weight_kg
                values["weekly_goal_kg"] = 0.0
            else:
                # For non-maintenance goals, require both values
                if target_weight is None:
                    raise ValueError(
                        "target_weight is required for non-maintenance goals"
                    )
                if weekly_goal_kg is None:
                    raise ValueError(
                        "weekly_goal_kg is required for non-maintenance goals"
                    )

                # Validate target weight and weekly goal based on goal type
                if goal in [GoalType.gain, GoalType.muscle]:
                    if target_weight <= weight_kg:
                        raise ValueError(
                            "target_weight must be greater than current weight for weight/muscle gain"
                        )
                    if weekly_goal_kg <= 0:
                        raise ValueError(
                            "weekly_goal_kg must be positive for weight/muscle gain"
                        )
                elif goal == GoalType.loss:
                    if target_weight >= weight_kg:
                        raise ValueError(
                            "target_weight must be less than current weight for weight loss"
                        )
                    if weekly_goal_kg <= 0:
                        raise ValueError(
                            "weekly_goal_kg must be positive for weight loss"
                        )
        return values


# POST endpoint for creating a profile
@router.post("/profile", status_code=201)
async def create_profile(
    profile_data: UserProfileCreate,
    authorization: str = Header(None),
    mongodb_service: MongoDBService = Depends(get_mongodb_service),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    token = authorization[7:]
    current_user = verify_token(token)

    try:
        # Check if the profile already exists
        existing_profile = await mongodb_service.get_user_profile(current_user["uid"])
        if existing_profile:
            raise HTTPException(
                status_code=400,
                detail="Profile already exists. Use PUT to update.",
            )

        # Prepare the profile data
        profile_dict = profile_data.dict()
        profile_dict["birthdate"] = profile_dict["birthdate"].isoformat()

        # Create the profile
        result = await mongodb_service.create_user_profile(
            current_user["uid"], profile_dict
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create profile")

        return {
            "message": "Profile created successfully",
            "user_id": current_user["uid"],
            "profile_data": profile_data.dict(),
        }
    except Exception as e:
        print(f"Profile creation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create profile: {str(e)}",
        )


# PUT endpoint for updating a profile
@router.put("/profile")
async def update_profile(
    profile_data: UserProfileUpdate,
    authorization: str = Header(None),
    mongodb_service: MongoDBService = Depends(get_mongodb_service),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    token = authorization[7:]
    current_user = verify_token(token)

    try:
        # Check if the profile exists
        existing_profile = await mongodb_service.get_user_profile(current_user["uid"])
        if not existing_profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found. Use POST to create.",
            )

        # Prepare the profile data, filtering out None values
        profile_dict = {
            k: v.isoformat() if k == "birthdate" and v is not None else v
            for k, v in profile_data.dict(exclude_unset=True).items()
        }

        print("Profile dict for update:", profile_dict)

        result = await mongodb_service.update_user_profile(
            current_user["uid"], profile_dict
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update profile")

        # Fetch the updated profile from the database
        updated_profile = await mongodb_service.get_user_profile(current_user["uid"])

        if "_id" in updated_profile:
            updated_profile.pop("_id")

        if "user_id" in updated_profile:
            updated_profile.pop("user_id")

        ordered_profile = UserProfileCreate(**updated_profile)

        return {
            "message": "Profile updated successfully",
            "user_id": current_user["uid"],
            "profile_data": ordered_profile.dict(by_alias=True),
        }
    except Exception as e:
        print(f"Profile update error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update profile: {str(e)}",
        )
