import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.documents.models import Document, DocumentVersion
from app.projects.models import ProjectMember, RoleEnum
from app.users.models import User


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        query = (
            select(Document)
            .where(Document.id == document_id)
            .options(
                selectinload(Document.versions).selectinload(DocumentVersion.uploaded_by),
                selectinload(Document.project),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_project_documents(self, project_id: uuid.UUID) -> Sequence[Document]:
        query = (
            select(Document)
            .where(Document.project_id == project_id)
            .options(selectinload(Document.versions).selectinload(DocumentVersion.uploaded_by))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_document_with_version(
        self,
        project_id: uuid.UUID,
        title: str,
        s3_key: str,
        file_name: str,
        file_size: int,
        content_type: str,
        user_id: uuid.UUID,
    ) -> Document:
        document = Document(project_id=project_id, title=title)
        self.db.add(document)
        await self.db.flush()

        version = DocumentVersion(
            document_id=document.id,
            version_number=1,
            s3_key=s3_key,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            uploaded_by_id=user_id,
        )
        self.db.add(version)
        await self.db.commit()
        created_doc = await self.get_by_id(document.id)
        if created_doc is None:
            raise RuntimeError("Failed to retrieve created document")
        return created_doc

    async def delete_document(self, document: Document) -> None:
        await self.db.delete(document)
        await self.db.commit()

    async def get_version_by_id(self, version_id: uuid.UUID) -> DocumentVersion | None:
        query = (
            select(DocumentVersion)
            .where(DocumentVersion.id == version_id)
            .options(selectinload(DocumentVersion.uploaded_by))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_version(
        self,
        document_id: uuid.UUID,
        version_number: int,
        s3_key: str,
        file_name: str,
        file_size: int,
        content_type: str,
        uploaded_by_id: uuid.UUID,
    ) -> DocumentVersion:
        version = DocumentVersion(
            document_id=document_id,
            version_number=version_number,
            s3_key=s3_key,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            uploaded_by_id=uploaded_by_id,
        )
        self.db.add(version)
        await self.db.commit()

        # Загружаем созданную версию вместе с uploaded_by
        created_version = await self.get_version_by_id(version.id)
        if created_version is None:
            raise RuntimeError("Failed to retrieve created document version")
        return created_version

    async def get_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> ProjectMember | None:
        query = select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_member(
        self, project_id: uuid.UUID, user_id: uuid.UUID, role: RoleEnum
    ) -> ProjectMember:
        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def get_user_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
