from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.requests import Request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "applications.db"

app = FastAPI(title="Credit Application Service")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


class ApplicationIn(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=18, le=100)
    gender: str = Field(..., min_length=1, max_length=20)
    salary: float = Field(..., ge=0)
    has_children: bool
    children_count: int = Field(0, ge=0, le=20)
    debts: float = Field(0, ge=0)
    has_car: bool


class ApplicationResult(BaseModel):
    accepted: bool
    message: str


@app.on_event("startup")
def startup() -> None:
    init_db()


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                salary REAL NOT NULL,
                has_children INTEGER NOT NULL,
                children_count INTEGER NOT NULL,
                debts REAL NOT NULL,
                has_car INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def evaluate_application(payload: ApplicationIn) -> tuple[bool, str]:
    """Simple rules that mimic ML decisioning."""
    if payload.age < 21:
        return False, "Заявка отклонена: минимальный возраст 21 год."

    if payload.salary < 30000:
        return False, "Заявка отклонена: недостаточный доход."

    if payload.debts > payload.salary * 0.5:
        return False, "Заявка отклонена: слишком большая долговая нагрузка."

    if payload.has_children and payload.children_count == 0:
        return False, "Заявка отклонена: укажите количество детей."

    score = 0
    score += 2 if payload.has_car else 0
    score += 2 if payload.salary >= 60000 else 1
    score += 1 if payload.debts == 0 else 0
    score += 1 if payload.age >= 25 else 0

    if score >= 4:
        return True, "Клиент принят."

    return False, "Заявка отклонена: недостаточно данных для одобрения."


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/applications", response_model=ApplicationResult)
def submit_application(payload: ApplicationIn) -> ApplicationResult:
    accepted, message = evaluate_application(payload)

    if accepted:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute(
                """
                INSERT INTO applications (
                    first_name,
                    last_name,
                    age,
                    gender,
                    salary,
                    has_children,
                    children_count,
                    debts,
                    has_car,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.first_name,
                    payload.last_name,
                    payload.age,
                    payload.gender,
                    payload.salary,
                    int(payload.has_children),
                    payload.children_count,
                    payload.debts,
                    int(payload.has_car),
                    datetime.utcnow().isoformat(),
                ),
            )
            connection.commit()

    return ApplicationResult(accepted=accepted, message=message)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

