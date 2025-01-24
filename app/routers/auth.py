from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from app.services.firebase_service import (
    verify_token,
    create_user,
    verify_email_verification_code,
    send_verification_email,
    login_user,
)
from pydantic import BaseModel
from firebase_admin import auth  # Import the `auth` module from Firebase Admin SDK

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
async def signup(request: SignupRequest):
    try:
        # Create the user or retrieve an existing one
        user = create_user(email=request.email, password=request.password)

        # Generate an email verification link
        email_verification_link = auth.generate_email_verification_link(request.email)

        # Send the verification email
        await send_verification_email(request.email, email_verification_link)

        return {
            "message": "User created successfully. Verification email sent.",
            "uid": user.uid,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify")
async def verify(id_token: str):
    try:
        decoded_token = verify_token(id_token)
        return {"message": "Token is valid", "decoded_token": decoded_token}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/verify-email")
async def verify_email(oob_code: str):
    try:
        verify_email_verification_code(oob_code)
        return {"message": "Email successfully verified"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Failed to verify email: {e}")


@router.post("/login")
async def login(request: LoginRequest):
    try:
        # Call the login_user function to verify credentials and get tokens
        login_data = login_user(email=request.email, password=request.password)
        return {
            "message": "Login successful",
            "id_token": login_data["id_token"],
            "refresh_token": login_data["refresh_token"],
            "email": login_data["email"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
