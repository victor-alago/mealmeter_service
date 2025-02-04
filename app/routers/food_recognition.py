from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.services.food_recognition_service import recognize_food_from_image
import logging
import tempfile
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/food-recognition")
async def food_recognition(image: UploadFile = File(...)):
    logger.info(f"Received image upload: {image.filename}")
    
    if not image.content_type.startswith('image/'):
        logger.error(f"Invalid content type: {image.content_type}")
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            contents = await image.read()
            if not contents:
                logger.error("Received empty file")
                raise HTTPException(status_code=400, detail="Empty file received")
            
            temp_file.write(contents)
            temp_file_path = temp_file.name

        logger.info(f"Saved image to temporary file: {temp_file_path}")

        try:
            # Use the actual food recognition service
            result = recognize_food_from_image(temp_file_path)
            logger.info(f"Recognition result: {result}")
            
            # Format the response according to the expected structure
            response_data = {
                "calories": {
                    "total": sum(float(item.get('calories', 0)) for item in result.get('food_items', []))
                },
                "food_items": result.get('food_items', [])
            }
            
            logger.info(f"Sending response: {response_data}")
            return JSONResponse(content=response_data)

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.info("Cleaned up temporary file")

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

calorie_route = APIRouter()
calorie_route.include_router(router, prefix="/food-recognition")
