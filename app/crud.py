"""Database helper functions."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import qrcode
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas
from .auth import hash_password

BASE_DIR = Path(__file__).resolve().parents[1]
QR_CODES_DIR = BASE_DIR / "static" / "qrcodes"
QR_CODES_DIR.mkdir(parents=True, exist_ok=True)


def _save_qrcode(equipment_uuid: str) -> str:
    filename = f"{equipment_uuid}.png"
    file_path = QR_CODES_DIR / filename
    qr_img = qrcode.make(equipment_uuid)
    qr_img.save(str(file_path))
    return f"qrcodes/{filename}"


def create_equipment(db: Session, equipment_in: schemas.EquipmentCreate) -> models.Equipment:
    equipment_uuid = str(uuid4())
    qrcode_path = _save_qrcode(equipment_uuid)
    db_equipment = models.Equipment(
        uuid=equipment_uuid,
        name=equipment_in.name,
        location=equipment_in.location,
        notes=equipment_in.notes,
        status=schemas.EquipmentStatus.available.value,
        qrcode_path=qrcode_path,
    )
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    log_history(db, db_equipment.id, action="Создана запись")
    return db_equipment


def list_equipment(db: Session) -> List[models.Equipment]:
    return db.query(models.Equipment).order_by(models.Equipment.name.asc()).all()


def get_equipment_by_uuid(db: Session, equipment_uuid: str) -> Optional[models.Equipment]:
    return (
        db.query(models.Equipment)
        .filter(models.Equipment.uuid == equipment_uuid)
        .first()
    )


def get_equipment_detail(db: Session, equipment_uuid: str) -> Optional[models.Equipment]:
    equipment = get_equipment_by_uuid(db, equipment_uuid)
    if equipment:
        _ = equipment.histories  # trigger lazy load
    return equipment


def update_equipment_status(
    db: Session, equipment_uuid: str, status: schemas.EquipmentStatus
) -> Optional[models.Equipment]:
    equipment = get_equipment_by_uuid(db, equipment_uuid)
    if not equipment:
        return None
    equipment.status = status.value
    db.commit()
    db.refresh(equipment)
    log_history(db, equipment.id, action=f"Статус изменён на {status.value}")
    return equipment


def log_history(db: Session, equipment_id: int, action: str, user: Optional[str] = None) -> models.History:
    entry = models.History(equipment_id=equipment_id, action=action, user=user)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def add_history_entry(
    db: Session, equipment_uuid: str, history_in: schemas.HistoryCreate
) -> Optional[models.Equipment]:
    equipment = get_equipment_by_uuid(db, equipment_uuid)
    if not equipment:
        return None
    log_history(db, equipment.id, history_in.action, history_in.user)
    db.refresh(equipment)
    return equipment


def update_equipment_details(
    db: Session, equipment_uuid: str, update_in: schemas.EquipmentUpdate
) -> Optional[models.Equipment]:
    equipment = get_equipment_by_uuid(db, equipment_uuid)
    if not equipment:
        return None
    has_changes = False
    if update_in.name is not None:
        equipment.name = update_in.name
        has_changes = True
    if update_in.location is not None:
        equipment.location = update_in.location
        has_changes = True
    if update_in.notes is not None:
        equipment.notes = update_in.notes
        has_changes = True
    if not has_changes:
        return equipment
    db.commit()
    db.refresh(equipment)
    log_history(db, equipment.id, action="Данные оборудования обновлены")
    return equipment


def delete_equipment(db: Session, equipment_uuid: str) -> bool:
    equipment = get_equipment_by_uuid(db, equipment_uuid)
    if not equipment:
        return False
    db.delete(equipment)
    db.commit()
    return True


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return (
        db.query(models.User)
        .filter(func.lower(models.User.username) == func.lower(username))
        .first()
    )


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    user = models.User(
        username=user_in.username,
        role=user_in.role,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_default_admin(db: Session) -> None:
    if db.query(models.User).count():
        return
    admin = models.User(
        username="admin",
        role="admin",
        hashed_password=hash_password("admin"),
    )
    db.add(admin)
    db.commit()
