"""
STEP 8: THE APPLICATION ENTRY POINT
----------------------------------------
Run it with:   uvicorn app.main:app --reload
Then open:     http://127.0.0.1:8000/docs
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import models
from .database import engine
from .routers import appointments, auth, doctors, medical_records, patients
from .scheduler import start_scheduler, stop_scheduler

# Create all database tables if they don't already exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Clinic Appointment Management System",
    description=(
        "Patient registration, doctor scheduling, appointment booking, "
        "medical records, and automated reminders - secured with JWT."
    ),
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(medical_records.router)

# Serve static assets and templates
app.mount("/static", StaticFiles(directory=Path(__file__).resolve().parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()


@app.get("/", response_class=HTMLResponse, tags=["Root"])
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
