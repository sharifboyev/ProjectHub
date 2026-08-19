import uuid
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.shared.storage import MAX_PROJECT_STORAGE_BYTES, StorageService


@pytest.mark.asyncio
async def test_upload_file_within_limit(mocker):
    # Мокаем S3 и Redis
    mocker.patch("app.shared.s3.client.s3_client.get_project_total_size", return_value=0)
    mocker.patch(
        "app.shared.s3.client.s3_client.upload_file", return_value="projects/test/file.txt"
    )

    mock_redis = mocker.AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.exists.return_value = False
    mocker.patch("app.shared.storage.get_redis", return_value=mock_redis)

    project_id = uuid.uuid4()
    dummy_file = UploadFile(filename="test.txt", file=BytesIO(b"Hello World"))
    dummy_file.size = len(b"Hello World")

    path = await StorageService.save_file(dummy_file, project_id)
    assert path == "projects/test/file.txt"


@pytest.mark.asyncio
async def test_upload_file_exceeds_limit(mocker):
    # Устанавливаем текущий размер в 49.9 MB
    almost_full_size = MAX_PROJECT_STORAGE_BYTES - 100
    mocker.patch(
        "app.shared.s3.client.s3_client.get_project_total_size", return_value=almost_full_size
    )

    mock_redis = mocker.AsyncMock()
    mock_redis.get.return_value = str(almost_full_size)
    mocker.patch("app.shared.storage.get_redis", return_value=mock_redis)

    project_id = uuid.uuid4()

    # Файл размером больше оставшегося лимита
    large_content = b"X" * 1024  # 1 KB
    dummy_file = UploadFile(filename="large.txt", file=BytesIO(large_content))
    dummy_file.size = len(large_content)

    with pytest.raises(HTTPException) as exc_info:
        await StorageService.save_file(dummy_file, project_id)

    assert exc_info.value.status_code == 400
    assert "Превышен лимит хранилища" in exc_info.value.detail
