import os
import uuid
from pathlib import Path
from fastapi import UploadFile

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class StorageService:
    @staticmethod
    async def save_file(file: UploadFile, project_id: uuid.UUID) -> str:
        """Сохраняет файл на диск и возвращает относительный путь."""
        project_dir = UPLOAD_DIR / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        file_extension = Path(file.filename).suffix if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = project_dir / unique_filename

        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        return str(file_path)