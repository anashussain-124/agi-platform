"""Basic API health and auth tests."""
import pytest


@pytest.mark.asyncio
async def test_root(client):
    """Root endpoint returns app info."""
    res = await client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "running"
    assert "BrainAGI" in data["name"]


@pytest.mark.asyncio
async def test_health(client):
    """Health check returns healthy."""
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_and_login(client):
    """Register a new user and then login."""
    # Register
    res = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
    })
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["email"] == "test@example.com"

    # Login
    res = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass123!",
    })
    assert res.status_code == 200
    assert "token" in res.json()


@pytest.mark.asyncio
async def test_me_unauthorized(client):
    """/me without token returns 403."""
    res = await client.get("/api/auth/me")
    assert res.status_code == 403
