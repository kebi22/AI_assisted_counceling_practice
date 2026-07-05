"""User schemas."""

import uuid

from pydantic import EmailStr

from app.core.constants import UserRole
from app.schemas.common import ORMModel


class UserResponse(ORMModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
