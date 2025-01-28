from fastapi import APIRouter, HTTPException, Depends, Header, status
from fastapi.responses import HTMLResponse
from app.services.firebase_service import (
    verify_token,
    create_user,
    verify_email_verification_code,
    send_verification_email,
    login_user,
    send_password_reset_email,
)
from pydantic import BaseModel, Field
from firebase_admin import auth  # Import the `auth` module from Firebase Admin SDK
from app.services.mongodb_service import MongoDBService, get_mongodb_service

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ResetPasswordRequest(BaseModel):
    email: str


class UpdatePasswordRequest(BaseModel):
    old_password: str = Field(..., description="The user's current password")
    new_password: str = Field(
        ..., min_length=6, description="The new password for the user"
    )


@router.post("/signup")
async def signup(
    request: SignupRequest,
    mongodb_service: MongoDBService = Depends(get_mongodb_service),
):
    try:
        # Create the user in Firebase
        user = create_user(email=request.email, password=request.password)

        # Generate an email verification link
        email_verification_link = auth.generate_email_verification_link(request.email)

        # Send the verification email
        await send_verification_email(request.email, email_verification_link)

        # Create a preliminary MongoDB profile
        profile_data = {"user_id": user.uid, "is_setup": False}
        created = await mongodb_service.create_user_profile(user.uid, profile_data)
        if not created:
            raise HTTPException(
                status_code=500,
                detail="Failed to create initial user profile in MongoDB",
            )

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


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    try:
        # Generate password reset link
        reset_link = auth.generate_password_reset_link(request.email)

        # Send the link via email using the service function
        await send_password_reset_email(request.email, reset_link)

        return {
            "message": "Password reset email sent successfully to the user's email address."
        }
    except auth.FirebaseError as e:
        raise HTTPException(status_code=400, detail=f"Firebase error: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/update-password")
async def update_password(
    request: UpdatePasswordRequest, authorization: str = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing or invalid.",
        )
    id_token = authorization.split(" ")[1]  # Extract the token past "Bearer"
    try:
        # Decode the ID token and verify the old password
        decoded_token = auth.verify_id_token(id_token)
        user_email = decoded_token["email"]
        user = auth.get_user_by_email(user_email)

        # Verify old password by re-authenticating the user
        login_user(email=user_email, password=request.old_password)

        # Update the password in Firebase
        auth.update_user(user.uid, password=request.new_password)
        return {"message": "Password updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
