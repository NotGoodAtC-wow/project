"""Pydantic schemas for requests and responses."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


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

    class Config:
        orm_mode = True


class EquipmentDetail(EquipmentOut):
    histories: List[HistoryOut] = []


class StatusUpdate(BaseModel):
    status: EquipmentStatus


class HistoryCreate(HistoryBase):
    pass
