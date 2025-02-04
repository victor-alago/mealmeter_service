from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, profile, insights, food_logging, food_search, chat, food_recognition
from app.routers.food_recognition import calorie_route
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS with more permissive settings for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {request.headers}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Include the routers
app.include_router(food_recognition.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(insights.router)
app.include_router(food_logging.router)
app.include_router(food_search.router)
app.include_router(chat.router)
app.include_router(calorie_route)

@app.get("/")
async def root():
    """Test endpoint to verify API is accessible"""
    return {"status": "ok", "message": "MealMeter API is running"}

@app.get("/food-recognition")
async def test_food_recognition():
    """Test endpoint to verify food recognition endpoint is accessible"""
    return {
        "status": "ok",
        "message": "Food recognition endpoint is accessible",
        "usage": "Send POST request with image file to use this endpoint"
    }
