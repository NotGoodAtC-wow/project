"""FastAPI entry point for the Smart Inventory project."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from . import crud, models, schemas
from .auth import verify_password
from .database import Base, SessionLocal, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Inventory with QR system")
app.add_middleware(SessionMiddleware, secret_key="smart-inventory-demo-secret")

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


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> Optional[models.User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return crud.get_user(db, int(user_id))


def require_admin(user: Optional[models.User] = Depends(get_current_user)) -> models.User:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


@app.on_event("startup")
def ensure_default_admin():
    db = SessionLocal()
    try:
        crud.ensure_default_admin(db)
    finally:
        db.close()


@app.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request, current_user: Optional[models.User] = Depends(get_current_user)
):
    if current_user:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": None, "current_user": None}
    )


@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    user = crud.get_user_by_username(db, username or "") if username else None
    if not user or not password or not verify_password(password, user.hashed_password):
        context = {
            "request": request,
            "error": "Неверный логин или пароль",
            "current_user": None,
        }
        return templates.TemplateResponse("login.html", context, status_code=400)
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/logout")
def logout(
    request: Request,
    current_user: Optional[models.User] = Depends(get_current_user),
):
    if current_user:
        request.session.clear()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/", response_class=HTMLResponse)
def list_equipment(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    equipment = crud.list_equipment(db)
    context = {
        "request": request,
        "equipment": equipment,
        "status_labels": STATUS_LABELS,
        "status_badges": STATUS_BADGES,
        "current_user": current_user,
    }
    return templates.TemplateResponse("add_equipment.html", context)


@app.get("/scan", response_class=HTMLResponse)
def scan_page(
    request: Request,
    current_user: Optional[models.User] = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "scan.html", {"request": request, "current_user": current_user}
    )


@app.get("/item/{equipment_uuid}", response_class=HTMLResponse)
def item_detail(
    equipment_uuid: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    equipment = crud.get_equipment_detail(db, equipment_uuid)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    context = {
        "request": request,
        "equipment": equipment,
        "status_labels": STATUS_LABELS,
        "status_badges": STATUS_BADGES,
        "current_user": current_user,
    }
    return templates.TemplateResponse("item.html", context)


@app.post("/equipment/add")
async def add_equipment(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    content_type = request.headers.get("content-type", "")
    expects_html = "application/json" not in content_type

    if not current_user:
        if expects_html:
            return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
        raise HTTPException(status_code=401, detail="Authentication required")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")

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
    user: models.User = Depends(require_admin),
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
    user: models.User = Depends(require_admin),
):
    equipment = crud.add_history_entry(db, equipment_uuid, history_in)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return crud.get_equipment_detail(db, equipment_uuid)


@app.patch(
    "/equipment/{equipment_uuid}", response_model=schemas.EquipmentDetail
)
def update_equipment_details_api(
    equipment_uuid: str,
    update_in: schemas.EquipmentUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_admin),
):
    equipment = crud.update_equipment_details(db, equipment_uuid, update_in)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return crud.get_equipment_detail(db, equipment_uuid)


@app.delete("/equipment/{equipment_uuid}")
def delete_equipment_api(
    equipment_uuid: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_admin),
):
    deleted = crud.delete_equipment(db, equipment_uuid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"status": "deleted"}


@app.post("/equipment/{equipment_uuid}/edit")
async def edit_equipment_form(
    equipment_uuid: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    form = await request.form()
    update_in = schemas.EquipmentUpdate(
        name=form.get("name") or None,
        location=form.get("location") or None,
        notes=form.get("notes") or None,
    )
    crud.update_equipment_details(db, equipment_uuid, update_in)
    return RedirectResponse(
        url=f"/item/{equipment_uuid}", status_code=status.HTTP_303_SEE_OTHER
    )


@app.post("/equipment/{equipment_uuid}/delete")
def delete_equipment_form(
    equipment_uuid: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    crud.delete_equipment(db, equipment_uuid)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
