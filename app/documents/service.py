import json
import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models import Document
from app.documents.repository import DocumentRepository
from app.documents.schemas import DocumentRead
from app.projects.repository import ProjectRepository
from app.shared.redis.client import get_redis
from app.shared.s3.client import s3_client
from app.shared.storage import StorageService
from app.users.models import User

MAX_PROJECT_STORAGE_BYTES = 50 * 1024 * 1024  # 50 MB

class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.project_repo = ProjectRepository(db)

    async def _check_project_access(self, project_id: uuid.UUID, user_id: uuid.UUID):
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Проект не найден")

        is_owner = project.owner_id == user_id
        is_member = any(m.user_id == user_id for m in project.members)

        if not is_owner and not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет доступа к этому проекту"
            )
        return project, is_owner

    async def _invalidate_project_cache(self, project_id: uuid.UUID) -> None:
        """Вспомогательный метод для сброса кэша списка документов"""
        redis = await get_redis()
        cache_key = f"project:{project_id}:documents"
        await redis.delete(cache_key)

    async def upload_document(
        self, project_id: uuid.UUID, file: UploadFile, title: str | None, current_user: User
    ) -> Document:
        await self._check_project_access(project_id, current_user.id)

        # 1. Проверяем текущий объём диска проекта
        current_stats = await StorageService.get_storage_stats(project_id)
        current_size = current_stats.get("total_bytes", 0)

        file_size = file.size if file.size is not None else 0
        if file_size == 0:
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)

        if current_size + file_size > MAX_PROJECT_STORAGE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Превышен лимит хранилища проекта (максимум 50 MB)",
            )

        file_name = file.filename or "unnamed"
        file_ext = file_name.split(".")[-1] if "." in file_name else ""
        s3_key = f"projects/{project_id}/{uuid.uuid4()}.{file_ext}"

        await s3_client.upload_file(file, s3_key)

        doc = await self.doc_repo.create_document_with_version(
            project_id=project_id,
            title=title or file_name,
            s3_key=s3_key,
            file_name=file_name,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            user_id=current_user.id,
        )

        # Инвалидируем кэш списка документов проекта
        await self._invalidate_project_cache(project_id)
        return doc

    async def add_version(self, document_id: uuid.UUID, file: UploadFile, current_user: User):
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

        await self._check_project_access(document.project_id, current_user.id)

        # Проверяем текущий объём диска проекта
        current_stats = await StorageService.get_storage_stats(document.project_id)
        current_size = current_stats.get("total_bytes", 0)

        file_size = file.size if file.size is not None else 0
        if file_size == 0:
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)

        if current_size + file_size > MAX_PROJECT_STORAGE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Превышен лимит хранилища проекта (максимум 50 MB)",
            )

        file_name = file.filename or "unnamed"
        file_ext = file_name.split(".")[-1] if "." in file_name else ""
        s3_key = f"projects/{document.project_id}/{uuid.uuid4()}.{file_ext}"

        await s3_client.upload_file(file, s3_key)

        # Подсчитываем порядковый номер следующей версии
        next_version_number = len(document.versions) + 1 if document.versions else 1

        version = await self.doc_repo.create_version(
            document_id=document_id,
            version_number=next_version_number,
            s3_key=s3_key,
            file_name=file_name,
            file_size=file_size,
            content_type=file.content_type or "application/octet-stream",
            uploaded_by_id=current_user.id,
        )

        await self._invalidate_project_cache(document.project_id)
        return version

    async def download_document(self, document_id: uuid.UUID, current_user: User):
        document = await self.doc_repo.get_by_id(document_id)
        if not document or not document.versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Документ или версии не найдены"
            )

        await self._check_project_access(document.project_id, current_user.id)

        # Берем последнюю версию
        latest_version = sorted(document.versions, key=lambda v: v.version_number)[-1]
        file_bytes = await s3_client.download_file(latest_version.s3_key)

        return file_bytes, latest_version.file_name, latest_version.content_type

    async def get_project_documents(self, project_id: uuid.UUID, current_user: User):
        await self._check_project_access(project_id, current_user.id)

        redis = await get_redis()
        cache_key = f"project:{project_id}:documents"

        # 1. Чтение из кэша
        cached_data = await redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        # 2. Чтение из БД
        documents = await self.doc_repo.get_project_documents(project_id)

        # 3. Сериализация и запись в Redis на 60 секунд
        docs_data = [DocumentRead.model_validate(doc).model_dump(mode="json") for doc in documents]
        await redis.set(cache_key, json.dumps(docs_data), ex=60)

        return docs_data

    async def delete_document(self, document_id: uuid.UUID, current_user: User) -> None:
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

        _, is_owner = await self._check_project_access(document.project_id, current_user.id)
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только владелец проекта может удалять документы",
            )

        for version in document.versions:
            await s3_client.delete_file(version.s3_key)

        project_id = document.project_id
        await self.doc_repo.delete_document(document)

        # Инвалидируем кэш
        await self._invalidate_project_cache(project_id)

    async def get_document(self, document_id: uuid.UUID, current_user: User) -> Document:
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Документ не найден")

        await self._check_project_access(document.project_id, current_user.id)
        return document

    async def get_download_url(
            self, document_id: uuid.UUID, user: User, expires_in: int = 3600
    ) -> str:
        document = await self.get_document(document_id, user)

        if not document.versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Версии документа не найдены"
            )

        # Берем последнюю версию
        latest_version = sorted(document.versions, key=lambda v: v.version_number)[-1]

        # Генерируем Presigned URL через S3 клиент
        download_url = await s3_client.generate_presigned_url(
            file_key=latest_version.s3_key,
            expires_in=expires_in,
        )
        return download_url