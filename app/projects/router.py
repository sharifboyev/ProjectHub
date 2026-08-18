import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.schemas import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    AddMemberRequest
)
from app.projects.service import ProjectService
from app.shared.security.dependencies import get_current_user
from app.shared.db.session import get_db
from app.users.models import User

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать новый проект (текущий пользователь становится Owner)."""
    service = ProjectService(db)
    return await service.create_project(data, current_user)


@router.get("", response_model=List[ProjectRead])
async def get_my_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить список проектов текущего пользователя."""
    service = ProjectService(db)
    return await service.get_my_projects(current_user)


@router.post("/{project_id}/members", status_code=status.HTTP_201_CREATED)
async def add_project_member(
    project_id: uuid.UUID,
    data: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Добавить участника в проект по Email."""
    service = ProjectService(db)
    return await service.add_member_by_email(project_id, data, current_user)


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Обновить имя/описание проекта."""
    service = ProjectService(db)
    return await service.update_project(project_id, project_in, current_user)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить проект (доступно ТОЛЬКО владельцу)."""
    service = ProjectService(db)
    await service.delete_project(project_id, current_user)
    return None