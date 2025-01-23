from fastapi import FastAPI
from app.routers import auth

app = FastAPI()

# Include the authentication router
app.include_router(auth.router)
