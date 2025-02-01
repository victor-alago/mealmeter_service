from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, profile, insights, food_logging, food_search, chat, food_recognition

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allows access from your frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the routers
app.include_router(food_recognition.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(insights.router)
app.include_router(food_logging.router)
app.include_router(food_search.router)
app.include_router(chat.router)
