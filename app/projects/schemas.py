import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.projects.models import RoleEnum
from app.users.schemas import UserRead


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectMemberRead(BaseModel):
    user: UserRead
    role: RoleEnum
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    members: list[ProjectMemberRead] = []

    model_config = ConfigDict(from_attributes=True)


class AddMemberRequest(BaseModel):
    email: EmailStr
    role: RoleEnum = RoleEnum.PARTICIPANT


class ProjectInviteRequest(BaseModel):
    email: EmailStr
    role: RoleEnum = RoleEnum.PARTICIPANT


class ProjectMemberInfo(BaseModel):
    user_id: uuid.UUID
    email: str
    role: RoleEnum
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
