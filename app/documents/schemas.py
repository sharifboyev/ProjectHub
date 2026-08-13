import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.users.schemas import UserRead


class DocumentVersionRead(BaseModel):
    id: uuid.UUID
    version_number: int
    file_name: str
    file_size: int
    content_type: str
    uploaded_by: Optional[UserRead]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    created_at: datetime
    latest_version: Optional[DocumentVersionRead] = None
    versions: List[DocumentVersionRead] = []

    model_config = ConfigDict(from_attributes=True)