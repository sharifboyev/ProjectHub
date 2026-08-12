import uuid
from typing import Sequence
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.schemas import ProjectCreate, AddMemberRequest
from app.projects.models import Project, RoleEnum
from app.projects.repository import ProjectRepository
from app.users.repository import UserRepository
from app.users.models import User


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectRepository(db)
        self.user_repo = UserRepository(db)

    async def create_project(self, data: ProjectCreate, current_user: User) -> Project:
        return await self.repo.create_project(
            name=data.name,
            description=data.description,
            owner_id=current_user.id
        )

    async def get_my_projects(self, current_user: User) -> Sequence[Project]:
        return await self.repo.get_user_projects(current_user.id)

    async def add_member_by_email(self, project_id: uuid.UUID, data: AddMemberRequest, current_user: User):
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")

        if project.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Недостаточно прав для добавления участников")

        target_user = await self.user_repo.get_by_email(data.email)
        if not target_user:
            raise HTTPException(status_code=404, detail="Пользователь с таким email не найден")

        if any(m.user_id == target_user.id for m in project.members):
            raise HTTPException(status_code=400, detail="Пользователь уже является участником проекта")

        return await self.repo.add_member(project_id=project.id, user_id=target_user.id, role=data.role)