"""FastAPI entry point for the Smart Inventory project."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Inventory with QR system")

BASE_DIR = Path(__file__).resolve().parents[1]
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

STATUS_LABELS: Dict[str, str] = {
    schemas.EquipmentStatus.available.value: "В наличии",
    schemas.EquipmentStatus.issued.value: "Выдано",
    schemas.EquipmentStatus.lost.value: "Потеряно",
}
STATUS_BADGES: Dict[str, str] = {
    schemas.EquipmentStatus.available.value: "success",
    schemas.EquipmentStatus.issued.value: "warning",
    schemas.EquipmentStatus.lost.value: "danger",
}


@app.get("/", response_class=HTMLResponse)
def list_equipment(request: Request, db: Session = Depends(get_db)):
    equipment = crud.list_equipment(db)
    context = {
        "request": request,
        "equipment": equipment,
        "status_labels": STATUS_LABELS,
        "status_badges": STATUS_BADGES,
    }
    return templates.TemplateResponse("add_equipment.html", context)


@app.get("/scan", response_class=HTMLResponse)
def scan_page(request: Request):
    return templates.TemplateResponse(
        "scan.html", {"request": request}
    )


@app.get("/item/{equipment_uuid}", response_class=HTMLResponse)
def item_detail(
    equipment_uuid: str, request: Request, db: Session = Depends(get_db)
):
    equipment = crud.get_equipment_detail(db, equipment_uuid)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    context = {
        "request": request,
        "equipment": equipment,
        "status_labels": STATUS_LABELS,
        "status_badges": STATUS_BADGES,
    }
    return templates.TemplateResponse("item.html", context)


@app.post("/equipment/add")
async def add_equipment(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
        equipment_in = schemas.EquipmentCreate(**payload)
        equipment = crud.create_equipment(db, equipment_in)
        return equipment

    form = await request.form()
    name = form.get("name")
    location = form.get("location")
    notes = form.get("notes")
    if not name or not location:
        raise HTTPException(status_code=400, detail="Name and location are required")
    equipment_in = schemas.EquipmentCreate(name=name, location=location, notes=notes)
    crud.create_equipment(db, equipment_in)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get(
    "/equipment/{equipment_uuid}", response_model=schemas.EquipmentDetail
)
def get_equipment(equipment_uuid: str, db: Session = Depends(get_db)):
    equipment = crud.get_equipment_detail(db, equipment_uuid)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


@app.patch(
    "/equipment/{equipment_uuid}/status", response_model=schemas.EquipmentOut
)
def update_status(
    equipment_uuid: str,
    status_update: schemas.StatusUpdate,
    db: Session = Depends(get_db),
):
    equipment = crud.update_equipment_status(db, equipment_uuid, status_update.status)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


@app.post(
    "/equipment/{equipment_uuid}/history", response_model=schemas.EquipmentDetail
)
def add_history_entry(
    equipment_uuid: str,
    history_in: schemas.HistoryCreate,
    db: Session = Depends(get_db),
):
    equipment = crud.add_history_entry(db, equipment_uuid, history_in)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return crud.get_equipment_detail(db, equipment_uuid)
