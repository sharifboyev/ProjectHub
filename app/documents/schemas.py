import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.users.schemas import UserRead


class DocumentVersionRead(BaseModel):
    id: uuid.UUID
    version_number: int
    file_name: str
    file_size: int
    content_type: str
    s3_key: str
    uploaded_by: Optional[UserRead] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    created_at: datetime
    versions: List[DocumentVersionRead] = []

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None