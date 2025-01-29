from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
from app.services.firebase_service import verify_token
from openai import OpenAI
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    message: str


SYSTEM_MESSAGE = """You are a helpful assistant for the MealMeter application, a food and calorie tracking app.
You can help users with:
- Meal planning and food logging
- Calorie calculations and nutritional advice
- Understanding their daily food logs
- Suggesting healthy alternatives
- General nutrition and diet questions
- Using the app's features

Please keep responses focused on nutrition, health, and app usage.
If users ask about medical conditions, remind them to consult healthcare professionals.
Be encouraging and supportive of users' health goals while maintaining a professional tone."""


@router.post("/message")
async def send_message(
    chat_message: ChatMessage,
    authorization: str = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )

    token = authorization[7:]  # Remove 'Bearer ' prefix
    verify_token(token)  # Just verify the token without assignment

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.openai_api_key)

        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": chat_message.message}
            ],
            max_tokens=500,
            temperature=0.7,
        )

        # Extract and return the AI's response
        ai_response = response.choices[0].message.content

        return {
            "response": ai_response
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat response: {str(e)}"
        )