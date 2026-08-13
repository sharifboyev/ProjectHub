import uuid
from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.documents.models import Document, DocumentVersion


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(self, project_id: uuid.UUID, title: str) -> Document:
        doc = Document(project_id=project_id, title=title)
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def add_version(
        self,
        document_id: uuid.UUID,
        version_number: int,
        file_path: str,
        file_name: str,
        file_size: int,
        content_type: str,
        uploaded_by_id: uuid.UUID,
    ) -> DocumentVersion:
        version = DocumentVersion(
            document_id=document_id,
            version_number=version_number,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            uploaded_by_id=uploaded_by_id,
        )
        self.db.add(version)
        await self.db.commit()
        return version

    async def get_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        query = (
            select(Document)
            .where(Document.id == document_id)
            .options(
                selectinload(Document.versions).selectinload(DocumentVersion.uploaded_by)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_project_documents(self, project_id: uuid.UUID) -> Sequence[Document]:
        query = (
            select(Document)
            .where(Document.project_id == project_id)
            .options(
                selectinload(Document.versions).selectinload(DocumentVersion.uploaded_by)
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()