from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from app.services.firebase_service import verify_token
from app.services.mongodb_service import MongoDBService, get_mongodb_service
from app.services.nutrition_service import calculate_nutrition_for_user

router = APIRouter(prefix="/insights", tags=["insights"])

# Models
class MacronutrientDistribution(BaseModel):
    tdee: float
    protein_grams: float
    carbs_grams: float
    fats_grams: float

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
        tdee, macros = await calculate_nutrition_for_user(current_user["uid"], mongodb_service)

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