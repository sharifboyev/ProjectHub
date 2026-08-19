import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.users.schemas import UserRead


class DocumentVersionRead(BaseModel):
    id: uuid.UUID
    version_number: int
    file_name: str
    file_size: int
    content_type: str
    s3_key: str
    uploaded_by: UserRead | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    created_at: datetime
    versions: list[DocumentVersionRead] = []

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
