import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.models import ProjectMember, RoleEnum
from app.shared.db.session import get_db
from app.shared.security.dependencies import get_current_user
from app.users.models import User


class RequireProjectRole:
    """Зависимость для проверки минимально требуемой роли пользователя в проекте."""

    def __init__(self, allowed_roles: list[RoleEnum]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        project_id: uuid.UUID,
        db: Annotated[AsyncSession, Depends(get_db)],
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> ProjectMember:
        query = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member or member.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас недостаточно прав для выполнения этой операции в проекте",
            )
        return member


# Удобные алиасы
require_owner = RequireProjectRole([RoleEnum.OWNER])
require_participant = RequireProjectRole([RoleEnum.OWNER, RoleEnum.PARTICIPANT])