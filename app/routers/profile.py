from datetime import date
from enum import Enum
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from pydantic import BaseModel, root_validator
from app.services.firebase_service import verify_token
from app.services.mongodb_service import MongoDBService, get_mongodb_service
from app.services.nutrition_service import calculate_nutrition_for_user


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
    medical_conditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None

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
    medical_conditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None

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


@router.get("/profile")
async def get_profile(
    authorization: str = Header(None),
    mongodb_service: MongoDBService = Depends(get_mongodb_service),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )

    token = authorization[7:]  # Extract the token part past "Bearer "
    try:
        current_user = verify_token(token)
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid token: {str(e)}")

    profile = await mongodb_service.get_user_profile(current_user["uid"])
    if profile:
        return {"message": "Profile retrieved successfully", "profile_data": profile}
    else:
        raise HTTPException(status_code=404, detail="Profile not found")


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

    # Retrieve the existing profile, preliminary or otherwise
    existing_profile = await mongodb_service.get_user_profile(current_user["uid"])

    if existing_profile:
        if not existing_profile.get("is_setup"):
            # Update preliminary profile with new data and mark as setup
            profile_data_dict = profile_data.dict()
            profile_data_dict["is_setup"] = True  # Ensure setup is marked complete
            profile_data_dict["birthdate"] = profile_data_dict["birthdate"].isoformat()
            success = await mongodb_service.update_user_profile(
                current_user["uid"], profile_data_dict
            )
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update existing preliminary profile",
                )
            # Calculate and store insights
            await calculate_nutrition_for_user(current_user["uid"], mongodb_service)
            return {
                "message": "Profile updated successfully",
                "profile_data": profile_data.dict(),
            }
        else:
            raise HTTPException(
                status_code=400, detail="Profile already exists. Use PUT to update."
            )
    else:
        # If there's no profile at all, create one
        profile_data_dict = profile_data.dict()
        profile_data_dict["birthdate"] = profile_data_dict["birthdate"].isoformat()
        profile_data_dict["is_setup"] = True  # Mark setup as complete upon creation
        success = await mongodb_service.create_user_profile(
            current_user["uid"], profile_data_dict
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create profile")
        # Calculate and store insights
        await calculate_nutrition_for_user(current_user["uid"], mongodb_service)
        return {
            "message": "Profile created successfully",
            "profile_data": profile_data.dict(),
        }


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

    existing_profile = await mongodb_service.get_user_profile(current_user["uid"])
    if not existing_profile:
        raise HTTPException(
            status_code=404, detail="Profile not found. Use POST to create."
        )

    # Allow updates to preliminary profiles
    if existing_profile.get("is_setup") is False:
        profile_data_dict = profile_data.dict(exclude_unset=True)
        profile_data_dict["is_setup"] = True  # Mark as fully setup after update
        success = await mongodb_service.update_user_profile(
            current_user["uid"], profile_data_dict
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update profile")

        # Calculate and store insights
        await calculate_nutrition_for_user(current_user["uid"], mongodb_service)
        return {"message": "Profile updated successfully"}
    else:
        # Normal update process for already fully setup profiles
        profile_dict = {
            k: v.isoformat() if k == "birthdate" and v is not None else v
            for k, v in profile_data.dict(exclude_unset=True).items()
        }
        result = await mongodb_service.update_user_profile(
            current_user["uid"], profile_dict
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update profile")

        # Calculate and store insights
        await calculate_nutrition_for_user(current_user["uid"], mongodb_service)
        return {"message": "Profile updated successfully"}
