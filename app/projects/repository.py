import uuid
from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.projects.models import Project, ProjectMember, RoleEnum


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(self, name: str, description: Optional[str], owner_id: uuid.UUID) -> Project:
        project = Project(name=name, description=description, owner_id=owner_id)
        self.db.add(project)
        await self.db.flush()

        # Создатель автоматический OWNER
        owner_member = ProjectMember(project_id=project.id, user_id=owner_id, role=RoleEnum.OWNER)
        self.db.add(owner_member)

        await self.db.commit()
        return await self.get_by_id(project.id)

    async def get_by_id(self, project_id: uuid.UUID) -> Optional[Project]:
        query = (
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.members).selectinload(ProjectMember.user)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_projects(self, user_id: uuid.UUID) -> Sequence[Project]:
        query = (
            select(Project)
            .join(ProjectMember)
            .where(ProjectMember.user_id == user_id)
            .options(
                selectinload(Project.members).selectinload(ProjectMember.user)
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def add_member(self, project_id: uuid.UUID, user_id: uuid.UUID, role: RoleEnum) -> ProjectMember:
        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def update(self, project: Project, update_data: dict) -> Project:
        """Обновляет поля модели из полученного словаря."""
        for key, value in update_data.items():
            setattr(project, key, value)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        """Удаляет объект проекта из базы данных."""
        await self.db.delete(project)
        await self.db.commit()