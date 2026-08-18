import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_document_lifecycle(client: AsyncClient):
    # 1. Регистрация и авторизация
    register_payload = {
        "email": "docuser@example.com",
        "first_name": "Doc",
        "last_name": "Owner",
        "password": "StrongPassword123!",
        "repeat_password": "StrongPassword123!",
    }
    await client.post("/auth/register", json=register_payload)

    login_resp = await client.post(
        "/auth/login",
        json={
            "email": "docuser@example.com",
            "password": "StrongPassword123!",
        },
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Создание проекта
    project_payload = {"name": "Test Project", "description": "Project for docs"}
    project_resp = await client.post(
        "/projects", json=project_payload, headers=headers
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    # 3. Загрузка первого файла в S3
    file_content = b"Hello, this is a test document content."
    files = {"file": ("test_doc.txt", io.BytesIO(file_content), "text/plain")}

    upload_resp = await client.post(
        f"/projects/{project_id}/documents", files=files, headers=headers
    )
    assert upload_resp.status_code == 201
    doc_data = upload_resp.json()

    assert doc_data["title"] == "test_doc.txt"
    doc_id = doc_data["id"]

    # 4. Проверка получения списка документов
    list_resp = await client.get(
        f"/projects/{project_id}/documents", headers=headers
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 5. Удаление документа
    delete_resp = await client.delete(f"/documents/{doc_id}", headers=headers)
    assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_document_versioning(client: AsyncClient):
    # 1. Авторизация пользователя
    register_payload = {
        "email": "versionuser@example.com",
        "first_name": "Version",
        "last_name": "Tester",
        "password": "StrongPassword123!",
        "repeat_password": "StrongPassword123!",
    }
    await client.post("/auth/register", json=register_payload)

    login_resp = await client.post(
        "/auth/login",
        json={
            "email": "versionuser@example.com",
            "password": "StrongPassword123!",
        },
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Создание проекта
    project_resp = await client.post(
        "/projects",
        json={"name": "Versioning Project", "description": "For testing versions"},
        headers=headers,
    )
    project_id = project_resp.json()["id"]

    # 3. Загрузка первой версии документа (v1)
    v1_content = b"Initial version 1.0 content"
    files_v1 = {"file": ("doc_v1.txt", io.BytesIO(v1_content), "text/plain")}

    v1_resp = await client.post(
        f"/projects/{project_id}/documents", files=files_v1, headers=headers
    )
    assert v1_resp.status_code == 201
    doc_data = v1_resp.json()
    doc_id = doc_data["id"]

    # 4. Загрузка второй версии (v2) для существующего документа
    v2_content = b"Updated version 2.0 content with changes"
    files_v2 = {"file": ("doc_v2.txt", io.BytesIO(v2_content), "text/plain")}

    v2_resp = await client.post(
        f"/documents/{doc_id}/versions", files=files_v2, headers=headers
    )
    assert v2_resp.status_code == 201
    v2_data = v2_resp.json()

    # 5. Проверка списка версий
    doc_detail_resp = await client.get(f"/documents/{doc_id}", headers=headers)
    assert doc_detail_resp.status_code == 200
    versions = doc_detail_resp.json()["versions"]

    assert len(versions) == 2
    assert versions[0]["version_number"] == 1
    assert versions[1]["version_number"] == 2
    assert versions[1]["file_name"] == "doc_v2.txt"


@pytest.mark.asyncio
async def test_document_delete_permissions(client: AsyncClient):
    # 1. Регистрация Владельца и создание проекта/документа
    await client.post("/auth/register", json={
        "email": "owner@example.com",
        "first_name": "Owner",
        "last_name": "User",
        "password": "Password123!",
        "repeat_password": "Password123!",
    })
    login_owner = await client.post("/auth/login", json={"email": "owner@example.com", "password": "Password123!"})
    owner_headers = {"Authorization": f"Bearer {login_owner.json()['access_token']}"}

    project_resp = await client.post("/projects", json={"name": "Perm Project"}, headers=owner_headers)
    project_id = project_resp.json()["id"]

    file_content = b"Content"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    upload_resp = await client.post(f"/projects/{project_id}/documents", files=files, headers=owner_headers)
    doc_id = upload_resp.json()["id"]

    # 2. Регистрация Участника и добавление его в проект
    await client.post("/auth/register", json={
        "email": "participant@example.com",
        "first_name": "Part",
        "last_name": "User",
        "password": "Password123!",
        "repeat_password": "Password123!",
    })
    login_part = await client.post("/auth/login", json={"email": "participant@example.com", "password": "Password123!"})
    part_headers = {"Authorization": f"Bearer {login_part.json()['access_token']}"}

    await client.post(f"/projects/{project_id}/members", json={"email": "participant@example.com", "role": "participant"}, headers=owner_headers)

    # 3. Попытка удаления документа участником (должно быть 403)
    delete_resp = await client.delete(f"/documents/{doc_id}", headers=part_headers)
    assert delete_resp.status_code == 403

    # 4. Удаление документа владельцем (должно быть 204)
    delete_resp_owner = await client.delete(f"/documents/{doc_id}", headers=owner_headers)
    assert delete_resp_owner.status_code == 204