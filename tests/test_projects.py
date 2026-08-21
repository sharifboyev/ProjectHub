import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_project_lifecycle(client: AsyncClient):
    # 1. Register and login
    register_payload = {
        "email": "projectuser@example.com",
        "first_name": "Project",
        "last_name": "Tester",
        "password": "StrongPassword123!",
        "repeat_password": "StrongPassword123!",
    }
    await client.post("/auth/register", json=register_payload)

    login_resp = await client.post(
        "/auth/login",
        json={
            "email": "projectuser@example.com",
            "password": "StrongPassword123!",
        },
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create project
    project_payload = {"name": "Test Project", "description": "Project description"}
    create_resp = await client.post("/projects", json=project_payload, headers=headers)
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]
    assert create_resp.json()["name"] == "Test Project"

    # 3. List projects
    list_resp = await client.get("/projects", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1
    assert any(p["id"] == project_id for p in list_resp.json())

    # 4. Update project
    update_payload = {"name": "Updated Project", "description": "Updated description"}
    update_resp = await client.put(f"/projects/{project_id}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Project"

    # 5. Add member (Register another user first)
    member_email = "member@example.com"
    await client.post(
        "/auth/register",
        json={
            "email": member_email,
            "first_name": "Member",
            "last_name": "User",
            "password": "StrongPassword123!",
            "repeat_password": "StrongPassword123!",
        },
    )

    add_member_payload = {"email": member_email, "role": "participant"}
    add_member_resp = await client.post(
        f"/projects/{project_id}/members", json=add_member_payload, headers=headers
    )
    assert add_member_resp.status_code == 201

    # 6. Delete project
    delete_resp = await client.delete(f"/projects/{project_id}", headers=headers)
    assert delete_resp.status_code == 204

    # 7. Verify deletion
    list_after_resp = await client.get("/projects", headers=headers)
    assert all(p["id"] != project_id for p in list_after_resp.json())


@pytest.mark.asyncio
async def test_rbac_forbidden_access(client: AsyncClient):
    # Владелец создает проект
    await client.post(
        "/auth/register",
        json={
            "email": "owner@example.com",
            "first_name": "Owner",
            "last_name": "User",
            "password": "StrongPassword123!",
            "repeat_password": "StrongPassword123!",
        },
    )
    login_owner = await client.post(
        "/auth/login", json={"email": "owner@example.com", "password": "StrongPassword123!"}
    )
    owner_headers = {"Authorization": f"Bearer {login_owner.json()['access_token']}"}

    create_resp = await client.post(
        "/projects",
        json={"name": "Private Project", "description": "Private Data"},
        headers=owner_headers,
    )
    project_id = create_resp.json()["id"]

    # Чужой пользователь пытаются получить доступ к документам проекта
    await client.post(
        "/auth/register",
        json={
            "email": "stranger@example.com",
            "first_name": "Stranger",
            "last_name": "User",
            "password": "StrongPassword123!",
            "repeat_password": "StrongPassword123!",
        },
    )
    login_stranger = await client.post(
        "/auth/login", json={"email": "stranger@example.com", "password": "StrongPassword123!"}
    )
    stranger_headers = {"Authorization": f"Bearer {login_stranger.json()['access_token']}"}

    # Попытка прочитать документы чужого проекта должна вернуть 403 Forbidden
    access_resp = await client.get(
        f"/projects/{project_id}/documents", headers=stranger_headers
    )
    assert access_resp.status_code == 403


@pytest.mark.asyncio
async def test_storage_quota_exceeded(client: AsyncClient):
    # Создаем пользователя и проект
    await client.post(
        "/auth/register",
        json={
            "email": "quota_user@example.com",
            "first_name": "Quota",
            "last_name": "User",
            "password": "StrongPassword123!",
            "repeat_password": "StrongPassword123!",
        },
    )
    login_resp = await client.post(
        "/auth/login", json={"email": "quota_user@example.com", "password": "StrongPassword123!"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    proj_resp = await client.post(
        "/projects", json={"name": "Quota Project"}, headers=headers
    )
    project_id = proj_resp.json()["id"]

    # Создаем файл размером больше 50 MB
    oversized_file_content = b"0" * (51 * 1024 * 1024)
    files = {"file": ("big_file.txt", oversized_file_content, "text/plain")}

    upload_resp = await client.post(
        f"/projects/{project_id}/documents", files=files, headers=headers
    )
    # Ожидаем ошибку 400 Bad Request из-за превышения квоты
    assert upload_resp.status_code == 400
    assert "лимит" in upload_resp.json()["detail"].lower() or "quota" in upload_resp.json()["detail"].lower()