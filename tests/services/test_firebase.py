import pytest
from firebase_admin import auth
from app.services.firebase_service import create_user, verify_token, login_user
from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)

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
        pass


def test_create_user():
    """Test creating a user."""
    user = create_user(TEST_EMAIL, TEST_PASSWORD)
    assert user.email == TEST_EMAIL
    assert user.uid is not None


def test_login_user():
    """Test user login."""
    create_user(TEST_EMAIL, TEST_PASSWORD)

    # Verify email for the user
    user = auth.get_user_by_email(TEST_EMAIL)
    auth.update_user(user.uid, email_verified=True)

    login_data = login_user(TEST_EMAIL, TEST_PASSWORD)
    assert login_data["email"] == TEST_EMAIL
    assert "id_token" in login_data
    assert "refresh_token" in login_data
