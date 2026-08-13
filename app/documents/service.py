import uuid
from typing import Sequence
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models import Document
from app.documents.repository import DocumentRepository
from app.projects.repository import ProjectRepository
from app.shared.storage import StorageService
from app.users.models import User


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DocumentRepository(db)
        self.project_repo = ProjectRepository(db)

    async def upload_document(
        self, project_id: uuid.UUID, title: str, file: UploadFile, current_user: User
    ) -> Document:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")

        # Сохраняем файл на диск/в S3
        file_path = await StorageService.save_file(file, project_id)

        # Создаем запись документа и версию v1
        document = await self.repo.create_document(project_id=project_id, title=title)
        await self.repo.add_version(
            document_id=document.id,
            version_number=1,
            file_path=file_path,
            file_name=file.filename or "file",
            file_size=file.size or 0,
            content_type=file.content_type or "application/octet-stream",
            uploaded_by_id=current_user.id,
        )

        return await self.repo.get_by_id(document.id)

    async def upload_new_version(
        self, document_id: uuid.UUID, file: UploadFile, current_user: User
    ) -> Document:
        document = await self.repo.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")

        # Рассчитываем номер следующей версии
        next_version = len(document.versions) + 1
        file_path = await StorageService.save_file(file, document.project_id)

        await self.repo.add_version(
            document_id=document.id,
            version_number=next_version,
            file_path=file_path,
            file_name=file.filename or "file",
            file_size=file.size or 0,
            content_type=file.content_type or "application/octet-stream",
            uploaded_by_id=current_user.id,
        )

        return await self.repo.get_by_id(document.id)

    async def get_project_documents(self, project_id: uuid.UUID) -> Sequence[Document]:
        return await self.repo.get_project_documents(project_id)