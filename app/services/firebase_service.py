import firebase_admin
from firebase_admin import credentials, auth
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.config import settings
import requests

# Initialize Firebase
cred = credentials.Certificate(settings.firebase_key_file)
firebase_app = firebase_admin.initialize_app(cred)

# Configure FastAPI-Mail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_STARTTLS=True,  # Gmail requires STARTTLS
    MAIL_SSL_TLS=False,  # Set to False because we use STARTTLS
    USE_CREDENTIALS=True,  # Enable authentication
)


# Function to create a user and send an email verification
def create_user(email: str, password: str):
    try:
        # Check if the user already exists
        user = auth.get_user_by_email(email)
        print(f"User with email {email} already exists.")
        return user
    except firebase_admin.auth.UserNotFoundError:
        # If the user doesn't exist, create a new one
        user = auth.create_user(email=email, password=password)
        return user
    except Exception as e:
        raise ValueError(f"Error creating user: {e}")


# Function to send the email verification link
async def send_verification_email(email: str, link: str):
    message = MessageSchema(
        subject="Verify Your Email",
        recipients=[email],  # List of recipients
        body=f"""
        <p>Hello,</p>
        <p>Thank you for signing up. Please verify your email by clicking the link below:</p>
        <p><a href="{link}">Verify Email</a></p>
        <p>If the above link doesn't work, copy and paste this URL into your browser: {link}</p>
        """,
        subtype="html",  # Send as HTML
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"Verification email sent to {email}")
    except Exception as e:
        print(f"Error sending email to {email}: {e}")


# Function to verify Firebase ID token
def verify_token(id_token: str):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise ValueError("Invalid token") from e


# Function to verify email verification code
def verify_email_verification_code(oob_code: str):
    try:
        # Apply the email verification action code
        auth.apply_action_code(oob_code)
    except Exception as e:
        raise ValueError(f"Invalid or expired verification code: {e}")


def login_user(email: str, password: str):
    try:
        # Get the Firebase Web API Key from the environment
        api_key = settings.firebase_api_key

        # Login with email and password
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {"email": email, "password": password, "returnSecureToken": True}

        response = requests.post(url, json=payload)
        response_data = response.json()

        if response.status_code != 200:
            raise ValueError(
                response_data.get("error", {}).get("message", "Login failed")
            )

        # Retrieve user details to check email verification status
        user = auth.get_user_by_email(email)
        if not user.email_verified:
            raise ValueError(
                "Email not verified. Please verify your email before logging in."
            )

        # Return the ID token and other user information
        return {
            "id_token": response_data["idToken"],
            "refresh_token": response_data["refreshToken"],
            "email": response_data["email"],
            "local_id": response_data["localId"],
        }
    except Exception as e:
        raise ValueError(f"Error logging in user: {e}")
