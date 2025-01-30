from datetime import date
from fastapi import HTTPException
from app.services.mongodb_service import MongoDBService
from typing import Dict, Tuple

# Activity level multipliers
ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "lightly active": 1.375,
    "moderately active": 1.55,
    "very active": 1.725,
    "extra active": 1.9,
}

# Macronutrient ratios by goal type
MACRO_RATIOS = {
    "weight loss": {
        "protein": 0.325,
        "carbs": 0.425,
        "fats": 0.225,
    },
    "weight maintenance": {"protein": 0.275, "carbs": 0.475, "fats": 0.225},
    "muscle gain": {"protein": 0.325, "carbs": 0.475, "fats": 0.175},
    "weight gain": {"protein": 0.275, "carbs": 0.525, "fats": 0.225},
}

def calculate_age(birthdate: date) -> int:
    today = date.today()
    age = today.year - birthdate.year
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1
    return age

def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    if gender == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def calculate_tdee(bmr: float, activity_level: str) -> int:
    return int(bmr * ACTIVITY_FACTORS[activity_level])

def calculate_calorie_adjustment(weekly_goal_kg: float) -> float:
    weekly_adjustment = weekly_goal_kg * 7700
    return weekly_adjustment / 7

def calculate_macros(tdee: float, goal: str) -> Dict[str, int]:
    ratios = MACRO_RATIOS[goal]
    return {
        "protein_grams": int((tdee * ratios["protein"]) / 4),
        "carbs_grams": int((tdee * ratios["carbs"]) / 4),
        "fats_grams": int((tdee * ratios["fats"]) / 9),
    }

async def calculate_nutrition_for_user(user_id: str, mongodb_service: MongoDBService) -> Tuple[float, Dict[str, float]]:
    try:
        # Get profile from MongoDB
        profile_data = await mongodb_service.get_user_profile(user_id)
        if not profile_data:
            raise HTTPException(
                status_code=404,
                detail="Profile not found. Please create a profile first.",
            )

        # Calculate age
        birthdate = date.fromisoformat(profile_data["birthdate"])
        age = calculate_age(birthdate)

        # Calculate BMR
        bmr = calculate_bmr(
            weight_kg=profile_data["weight_kg"],
            height_cm=profile_data["height_cm"],
            age=age,
            gender=profile_data["gender"],
        )

        # Calculate TDEE
        tdee = calculate_tdee(bmr, profile_data["activity_level"])

        # Calculate calorie adjustment based on goal
        daily_adjustment = calculate_calorie_adjustment(profile_data["weekly_goal_kg"])

        # Apply goal-based adjustment
        if profile_data["goal"] == "weight loss":
            tdee -= daily_adjustment
        elif profile_data["goal"] in ["weight gain", "muscle gain"]:
            tdee += daily_adjustment

        # Calculate macronutrient distribution
        macros = calculate_macros(tdee, profile_data["goal"])

        # Store the insights
        await mongodb_service.update_user_insights(user_id, {
            "tdee": tdee,
            "protein_grams": macros["protein_grams"],
            "carbs_grams": macros["carbs_grams"],
            "fats_grams": macros["fats_grams"]
        })

        return tdee, macros
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate nutrition plan: {str(e)}"
        )
