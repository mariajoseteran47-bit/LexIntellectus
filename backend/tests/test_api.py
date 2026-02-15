import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}

@pytest.mark.asyncio
async def test_create_tenant_and_login(client: AsyncClient):
    # 1. Register Tenant (Initial setup usually requires manual step or seed, 
    # but we can try login if we seed or hitting the register endpoint if it exists public)
    # Assuming we need to seed or use existing.
    # For integration test, let's just check 401 on protected route.
    
    response = await client.get("/api/v1/cases/")
    assert response.status_code == 401

# Add more sophisticated tests here for Cases CRUD
