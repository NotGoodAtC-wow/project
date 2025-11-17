# Smart Inventory with QR system

Мини-приложение на FastAPI для учёта оборудования с генерацией QR‑кодов и простым интерфейсом на Bootstrap 5.

## Возможности
- Добавление оборудования (название, местоположение, заметки).
- Автоматическое присвоение UUID и создание PNG QR-кода (хранится в static/qrcodes/).
- Веб-интерфейс со списком, карточкой предмета, статусами и историей действий.
- Страница /scan со сканером Html5-QRCode, который после считывания ведёт на /item/{uuid}.
- REST API для создания, получения, смены статуса и логирования действий.

## Структура проекта
`
project/
├─ app/
│  ├─ main.py       # FastAPI-маршруты и HTML-страницы
│  ├─ database.py   # Подключение SQLite и сессии SQLAlchemy
│  ├─ models.py     # Таблицы Equipment и History
│  ├─ crud.py       # Логика работы с БД и генерация QR
│  └─ schemas.py    # Pydantic-схемы
├─ static/
│  └─ qrcodes/      # PNG-файлы с QR-кодами
├─ templates/       # Jinja2 (Bootstrap 5)
├─ requirements.txt
└─ README.md
`

## Установка зависимостей
`ash
pip install -r requirements.txt
`

## Запуск
`ash
uvicorn app.main:app --reload
`

После старта открой http://127.0.0.1:8000 для формы/списка и http://127.0.0.1:8000/scan для сканера.

## API
- POST /equipment/add — JSON { "name": "...", "location": "...", "notes": "optional" }
- GET /equipment/{uuid} — детали оборудования + история
- PATCH /equipment/{uuid}/status — JSON { "status": "available|issued|lost" }
- POST /equipment/{uuid}/history — добавление действия
- GET /scan — веб-сканер
- GET / — список и форма

## Примечания
- HTML-форма тоже отправляет POST /equipment/add и получает редирект на /.
- Папка static/qrcodes создаётся автоматически; не удаляй её, чтобы файлы QR сохранялись корректно.
