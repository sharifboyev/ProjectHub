import uuid

from arq import ArqRedis
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.schemas import DocumentRead, DocumentVersionRead
from app.documents.service import DocumentService
from app.shared.db.session import get_db
from app.shared.security.dependencies import get_current_user
from app.shared.storage import StorageService
from app.shared.tasks import get_arq_pool
from app.users.models import User

router = APIRouter(tags=["Documents"])


@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    title: str = Form(None),
    db: AsyncSession = Depends(get_db),
    arq: ArqRedis = Depends(get_arq_pool),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    document = await service.upload_document(project_id, file, title, current_user)

    # Постановка фоновой задачи в ARQ (например, обработка текста или создание превью)
    await arq.enqueue_job("process_document_task", document_id=str(document.id))

    return document


@router.get("/projects/{project_id}/documents", response_model=list[DocumentRead])
async def get_project_documents(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    return await service.get_project_documents(project_id, current_user)


@router.get("/projects/{project_id}/storage-usage")
async def get_project_storage_usage(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
):
    """Возвращает текущую статистику использования лимита хранилища (50 MB) проекта."""
    return await StorageService.get_storage_stats(project_id)


@router.get("/documents/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    return await service.get_document(document_id, current_user)


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    file_bytes, filename, content_type = await service.download_document(document_id, current_user)

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    await service.delete_document(document_id, current_user)


@router.post(
    "/documents/{document_id}/versions",
    response_model=DocumentVersionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload new version of document",
)
async def upload_document_version(
    document_id: uuid.UUID,
    file: UploadFile = File(...),
    arq: ArqRedis = Depends(get_arq_pool),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    version = await service.add_version(document_id, file, current_user)

    # Фоновая задача при добавлении новой версии
    await arq.enqueue_job("process_document_task", document_id=str(document_id))

    return version

@router.get("/documents/{document_id}/presigned-url")
async def get_document_presigned_url(
    document_id: uuid.UUID,
    expires_in: int = 3600,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Возвращает временную Presigned URL ссылку для скачивания файла прямо из MinIO/S3."""
    service = DocumentService(db)
    download_url = await service.get_download_url(
        document_id=document_id, user=current_user, expires_in=expires_in
    )
    return {"download_url": download_url, "expires_in": expires_in}