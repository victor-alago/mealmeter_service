import pytest
from fastapi.testclient import TestClient
from firebase_admin import auth
from app.main import app

client = TestClient(app)

# Load test email and password
TEST_EMAIL = "mealmeter.tester@gmail.com"
TEST_PASSWORD = "securepassword123"


@pytest.fixture(scope="function", autouse=True)
def cleanup_user():
    """Clean up the test user from Firebase after each test."""
    yield
    try:
        user = auth.get_user_by_email(TEST_EMAIL)
        auth.delete_user(user.uid)
    except auth.UserNotFoundError:
        pass  # User doesn't exist


def test_signup():
    """Test user signup."""
    response = client.post(
        "/auth/signup",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User created successfully. Verification email sent."
    assert "uid" in data


def test_login():
    """Test user login."""
    # Ensure the user exists
    user = auth.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
    auth.update_user(user.uid, email_verified=True)

    response = client.post(
        "/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert "id_token" in data
    assert "refresh_token" in data
