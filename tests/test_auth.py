import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_user(client: AsyncClient):
    # 1. Регистрация нового пользователя (передаем все обязательные поля)
    register_payload = {
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "StrongPassword123!",
        "repeat_password": "StrongPassword123!",
    }
    response = await client.post("/auth/register", json=register_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == register_payload["email"]
    assert "id" in data

    # 2. Логин и получение JWT (UserLoginRequest ожидает email и password)
    login_payload = {"email": "testuser@example.com", "password": "StrongPassword123!"}
    login_response = await client.post("/auth/login", json=login_payload)
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"
    assert "user" in tokens
