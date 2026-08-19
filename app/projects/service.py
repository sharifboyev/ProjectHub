import uuid
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.models import Project
from app.projects.repository import ProjectRepository
from app.projects.schemas import AddMemberRequest, ProjectCreate, ProjectUpdate
from app.users.models import User
from app.users.repository import UserRepository


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectRepository(db)
        self.user_repo = UserRepository(db)

    async def create_project(self, data: ProjectCreate, current_user: User) -> Project:
        return await self.repo.create_project(
            name=data.name, description=data.description, owner_id=current_user.id
        )

    async def get_my_projects(self, current_user: User) -> Sequence[Project]:
        return await self.repo.get_user_projects(current_user.id)

    async def add_member_by_email(
        self, project_id: uuid.UUID, data: AddMemberRequest, current_user: User
    ):
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")

        if project.owner_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Недостаточно прав для добавления участников"
            )

        target_user = await self.user_repo.get_by_email(data.email)
        if not target_user:
            raise HTTPException(status_code=404, detail="Пользователь с таким email не найден")

        if any(m.user_id == target_user.id for m in project.members):
            raise HTTPException(
                status_code=400, detail="Пользователь уже является участником проекта"
            )

        return await self.repo.add_member(
            project_id=project.id, user_id=target_user.id, role=data.role
        )

    async def update_project(
        self, project_id: uuid.UUID, project_in: ProjectUpdate, current_user: User
    ) -> Project:
        project = await self.repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Проект не найден")
        is_owner = project.owner_id == current_user.id
        is_participant = any(member.user_id == current_user.id for member in project.members)

        if not is_owner and not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="У вас нет доступа к этому проекту"
            )

        update_data = project_in.model_dump(exclude_unset=True)
        return await self.repo.update(project, update_data)

    async def delete_project(self, project_id: uuid.UUID, current_user: User) -> None:
        project = await self.repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Проект не найден")

        if project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Удалить проект может только его владелец",
            )

        await self.repo.delete(project)
