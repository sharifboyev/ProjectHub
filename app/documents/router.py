import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, Response, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.db.session import get_db
from app.shared.security.dependencies import get_current_user
from app.users.models import User
from app.documents.schemas import DocumentRead, DocumentVersionRead
from app.documents.service import DocumentService

router = APIRouter(tags=["Documents"])


@router.post("/projects/{project_id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
        project_id: uuid.UUID,
        file: UploadFile = File(...),
        title: str = Form(None),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    service = DocumentService(db)
    return await service.upload_document(project_id, file, title, current_user)


@router.get("/projects/{project_id}/documents", response_model=List[DocumentRead])
async def get_project_documents(
        project_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    service = DocumentService(db)
    return await service.get_project_documents(project_id, current_user)


@router.get("/documents/{document_id}", response_model=DocumentRead)
async def get_document(
        document_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    service = DocumentService(db)
    return await service.get_document(document_id, current_user)


@router.get("/documents/{document_id}/download")
async def download_document(
        document_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    service = DocumentService(db)
    file_bytes, filename, content_type = await service.download_document(document_id, current_user)

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
        document_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
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
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    return await service.add_version(document_id, file, current_user)