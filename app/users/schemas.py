import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str


class UserRead(UserBase):
    id: uuid.UUID
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)