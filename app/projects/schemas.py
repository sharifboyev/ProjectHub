import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr
from app.projects.models import RoleEnum
from app.users.schemas import UserRead


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectMemberRead(BaseModel):
    user: UserRead
    role: RoleEnum
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectRead(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    members: List[ProjectMemberRead] = []

    model_config = ConfigDict(from_attributes=True)


class AddMemberRequest(BaseModel):
    email: EmailStr
    role: RoleEnum = RoleEnum.PARTICIPANT

class ProjectInviteRequest(BaseModel):
    email: EmailStr
    role: RoleEnum = RoleEnum.PARTICIPANT


class ProjectMemberRead(BaseModel):
    user_id: uuid.UUID
    email: str
    role: RoleEnum
    joined_at: datetime

    class Config:
        from_attributes = True