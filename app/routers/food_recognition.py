from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.food_recognition_service import recognize_food_from_image
import tempfile

router = APIRouter()

@router.post("/food-recognition")
async def food_recognition (image: UploadFile = File(...)):
    if not image.filename:
        raise HTTPException(status_code=400, detail="No image uploaded")

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(await image.read())
        temp_file_path = temp_file.name

    try:
        calories = recognize_food_from_image(temp_file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        temp_file.close()

    return {
        "calories": calories,
        "food_items": calories.get("food_items", []),
    }

from fastapi import APIRouter
from .food_recognition import router as calorie_router

calorie_route = APIRouter()

calorie_route.include_router(calorie_router, prefix="/food-recognition")
