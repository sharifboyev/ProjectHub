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
    await client.post("/auth/register", json={
        "email": member_email,
        "first_name": "Member",
        "last_name": "User",
        "password": "StrongPassword123!",
        "repeat_password": "StrongPassword123!",
    })
    
    add_member_payload = {"email": member_email, "role": "participant"}
    add_member_resp = await client.post(f"/projects/{project_id}/members", json=add_member_payload, headers=headers)
    assert add_member_resp.status_code == 201

    # 6. Delete project
    delete_resp = await client.delete(f"/projects/{project_id}", headers=headers)
    assert delete_resp.status_code == 204

    # 7. Verify deletion
    list_after_resp = await client.get("/projects", headers=headers)
    assert all(p["id"] != project_id for p in list_after_resp.json())
