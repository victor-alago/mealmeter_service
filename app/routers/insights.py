from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from app.routers.profile import UserProfileCreate
from app.services.firebase_service import verify_token
from app.services.mongodb_service import MongoDBService, get_mongodb_service
from datetime import date

router = APIRouter(prefix="/insights", tags=["insights"])


# Models
class MacronutrientDistribution(BaseModel):
    tdee: float
    protein_grams: float
    carbs_grams: float
    fats_grams: float


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
        "protein": 0.325,  # Average of 30-35%
        "carbs": 0.425,  # Average of 40-45%
        "fats": 0.225,  # Average of 20-25%
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


def calculate_tdee(bmr: float, activity_level: str) -> float:
    return bmr * ACTIVITY_FACTORS[activity_level]


def adjust_for_medications(tdee: float, medications: list[str]) -> float:
    # Placeholder for medication adjustment logic
    return tdee


def calculate_calorie_adjustment(weekly_goal_kg: float) -> float:
    # 1 kg ≈ 7700 calories
    weekly_adjustment = weekly_goal_kg * 7700
    return weekly_adjustment / 7


def calculate_macros(tdee: float, goal: str) -> dict[str, float]:
    ratios = MACRO_RATIOS[goal]
    return {
        "protein_grams": (tdee * ratios["protein"]) / 4,
        "carbs_grams": (tdee * ratios["carbs"]) / 4,
        "fats_grams": (tdee * ratios["fats"]) / 9,
    }


@router.get("/nutrition", response_model=MacronutrientDistribution)
async def get_nutrition(
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
        # Get profile from MongoDB
        profile_data = await mongodb_service.get_user_profile(current_user["uid"])
        if not profile_data:
            raise HTTPException(
                status_code=404,
                detail="Profile not found. Please create a profile first.",
            )

        # Convert to UserProfileCreate model
        profile = UserProfileCreate(**profile_data)

        # Calculate age
        age = calculate_age(profile.birthdate)

        # Calculate BMR
        bmr = calculate_bmr(
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            age=age,
            gender=profile.gender,
        )

        # Calculate TDEE
        tdee = calculate_tdee(bmr, profile.activity_level)

        # Adjust for medications
        if profile.health_metrics and profile.health_metrics.medications:
            tdee = adjust_for_medications(tdee, profile.health_metrics.medications)

        # Calculate calorie adjustment based on goal
        daily_adjustment = calculate_calorie_adjustment(profile.weekly_goal_kg)

        # Apply goal-based adjustment
        if profile.goal == "weight loss":
            tdee -= daily_adjustment
        elif profile.goal in ["weight gain", "muscle gain"]:
            tdee += daily_adjustment

        # Calculate macronutrient distribution
        macros = calculate_macros(tdee, profile.goal)

        return MacronutrientDistribution(
            tdee=tdee,
            protein_grams=macros["protein_grams"],
            carbs_grams=macros["carbs_grams"],
            fats_grams=macros["fats_grams"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate nutrition plan: {str(e)}"
        )
