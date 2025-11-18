"""Pydantic schemas for requests and responses."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class EquipmentStatus(str, Enum):
    available = "available"
    issued = "issued"
    lost = "lost"


class EquipmentBase(BaseModel):
    name: str = Field(..., max_length=255)
    location: str = Field(..., max_length=255)
    notes: Optional[str] = Field(default=None, max_length=2000)


class EquipmentCreate(EquipmentBase):
    pass


class HistoryBase(BaseModel):
    action: str = Field(..., max_length=255)
    user: Optional[str] = Field(default=None, max_length=255)


class HistoryOut(HistoryBase):
    timestamp: datetime

    class Config:
        orm_mode = True


class EquipmentOut(EquipmentBase):
    uuid: str
    status: EquipmentStatus
    qrcode_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    issued_at: Optional[datetime]
    returned_at: Optional[datetime]

    class Config:
        orm_mode = True


class EquipmentDetail(EquipmentOut):
    histories: List[HistoryOut] = Field(default_factory=list)


class StatusUpdate(BaseModel):
    status: EquipmentStatus


class HistoryCreate(HistoryBase):
    pass


class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    location: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = Field(default=None, max_length=2000)


class UserCreate(BaseModel):
    username: str = Field(..., max_length=255)
    password: str = Field(..., min_length=4)
    # Роль для публичной регистрации не принимаем, всегда "user". Поле оставлено для совместимости.
    role: str = Field(default="user")

    @validator("role", pre=True, always=True)
    def force_user_role(cls, v):  # noqa: N805
        # Защита: игнорируем любое входящее значение и проставляем "user"
        return "user"


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True


class RoleUpdate(BaseModel):
    role: str = Field(..., regex=r"^(user|admin)$")
