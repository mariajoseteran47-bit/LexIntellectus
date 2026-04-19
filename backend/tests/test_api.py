"""
LexIntellectus — Integration Tests for API Endpoints
Tests authentication walls, health check, and route protection.
These tests use httpx with the TestClient and mock DB.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health endpoint should return 200 with status info."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Root endpoint should return API info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "LexIntellectus" in data.get("name", "")


# ============================================================
# Authentication Wall Tests (should return 401/403 without token)
# ============================================================

@pytest.mark.asyncio
async def test_cases_requires_auth(client: AsyncClient):
    """Cases endpoint must require authentication."""
    response = await client.get("/api/v1/cases")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client: AsyncClient):
    """Dashboard stats must require authentication."""
    response = await client.get("/api/v1/dashboard/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upcoming_deadlines_requires_auth(client: AsyncClient):
    """Upcoming deadlines must require authentication."""
    response = await client.get("/api/v1/dashboard/upcoming-deadlines")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_audit_requires_auth(client: AsyncClient):
    """Audit logs must require authentication."""
    response = await client.get("/api/v1/audit/logs")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_users_requires_auth(client: AsyncClient):
    """Users endpoint must require authentication."""
    response = await client.get("/api/v1/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ai_chat_requires_auth(client: AsyncClient):
    """AI chat must require authentication."""
    response = await client.post("/api/v1/ai/chat", json={
        "message": "test",
        "mode": "consultor",
    })
    assert response.status_code == 401


# ============================================================
# Invalid Token Tests
# ============================================================

@pytest.mark.asyncio
async def test_cases_with_invalid_token(client: AsyncClient):
    """Requests with invalid JWT should be rejected."""
    response = await client.get(
        "/api/v1/cases",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_cases_with_malformed_auth(client: AsyncClient):
    """Requests with malformed Authorization header should be rejected."""
    response = await client.get(
        "/api/v1/cases",
        headers={"Authorization": "NotBearer something"}
    )
    assert response.status_code in [401, 403, 422]


# ============================================================
# Validation Tests
# ============================================================

@pytest.mark.asyncio
async def test_create_case_validation(client: AsyncClient):
    """Creating a case without auth should fail with 401."""
    response = await client.post("/api/v1/cases", json={
        "ramo": "civil",
        "resumen": "Test Case",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_case_status_change_requires_auth(client: AsyncClient):
    """Changing case status requires authentication."""
    import uuid
    fake_id = str(uuid.uuid4())
    response = await client.patch(
        f"/api/v1/cases/{fake_id}/status",
        json={"estado_id": str(uuid.uuid4())}
    )
    assert response.status_code == 401


# ============================================================
# Error Handling Tests
# ============================================================

@pytest.mark.asyncio
async def test_nonexistent_route_returns_404(client: AsyncClient):
    """Non-existent routes should return 404."""
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code in [404, 405]


@pytest.mark.asyncio
async def test_invalid_json_body(client: AsyncClient):
    """Invalid JSON body should be handled gracefully."""
    response = await client.post(
        "/api/v1/cases",
        content="this is not json",
        headers={"Content-Type": "application/json"}
    )
    # Should get 401 (auth check first) or 422 (validation)
    assert response.status_code in [401, 422]
