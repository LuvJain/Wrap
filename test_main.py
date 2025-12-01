from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_user_success():
    """Test successful user registration"""
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "Password123"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data

def test_register_duplicate_email():
    """Test registration with duplicate email"""
    # Register first user
    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "duplicateuser1",
            "password": "Password123"
        },
    )
    assert response.status_code == 201

    # Try registering second user with same email
    response = client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "duplicateuser2",
            "password": "Password123"
        },
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_password_complexity():
    """Test password complexity validation"""
    # Test short password
    response = client.post(
        "/auth/register",
        json={
            "email": "short@example.com",
            "username": "shortpass",
            "password": "Short1"
        },
    )
    assert response.status_code == 422

    # Test password without uppercase
    response = client.post(
        "/auth/register",
        json={
            "email": "nouppercase@example.com",
            "username": "nouppercase",
            "password": "password123"
        },
    )
    assert response.status_code == 422

    # Test password without number
    response = client.post(
        "/auth/register",
        json={
            "email": "nonumber@example.com",
            "username": "nonumber",
            "password": "Password"
        },
    )
    assert response.status_code == 422

def test_invalid_email():
    """Test invalid email format"""
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid-email",
            "username": "invalidemail",
            "password": "Password123"
        },
    )
    assert response.status_code == 422

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "up"
    assert "timestamp" in data
    assert isinstance(data["timestamp"], int)

def test_ping():
    """Test ping endpoint"""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.text == '"pong"'  # FastAPI serializes the string to JSON