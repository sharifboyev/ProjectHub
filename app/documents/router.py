import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.schemas import DocumentRead
from app.documents.service import DocumentService
from app.shared.security.dependencies import get_current_user
from app.shared.db.session import get_db
from app.users.models import User

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: uuid.UUID = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Загрузить новый документ (версия 1)."""
    service = DocumentService(db)
    return await service.upload_document(project_id, title, file, current_user)


@router.post("/{document_id}/versions", response_model=DocumentRead)
async def upload_new_version(
    document_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Загрузить новую версию существующего документа (v2, v3 и т.д.)."""
    service = DocumentService(db)
    return await service.upload_new_version(document_id, file, current_user)


@router.get("/project/{project_id}", response_model=List[DocumentRead])
async def get_project_documents(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить список всех документов проекта с их версиями."""
    service = DocumentService(db)
    return await service.get_project_documents(project_id)