"""
STEP 4: REQUEST / RESPONSE SHAPES (SCHEMAS)
----------------------------------------------
models.py      = how data is stored in the database.
schemas.py (here) = how data looks coming IN to and going OUT of the API.

Keeping these separate means we can hide fields like hashed_password
from API responses, and validate incoming data before it touches the DB.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str


# ---------------------------------------------------------------------------
# PATIENT
# ---------------------------------------------------------------------------
class PatientRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    age: int
    gender: str
    phone: str
    address: Optional[str] = None


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


# ---------------------------------------------------------------------------
# DOCTOR
# ---------------------------------------------------------------------------
class DoctorRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    specialization: str
    working_days: str = "Mon,Tue,Wed,Thu,Fri"
    start_time: str = "09:00"
    end_time: str = "17:00"


class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    specialization: str
    working_days: str
    start_time: str
    end_time: str


class DoctorAvailabilityUpdate(BaseModel):
    working_days: str
    start_time: str
    end_time: str


# ---------------------------------------------------------------------------
# APPOINTMENT
# ---------------------------------------------------------------------------
class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_time: datetime  # e.g. "2026-06-25T10:30:00"
    reason: Optional[str] = None


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    doctor_id: int
    appointment_time: datetime
    reason: Optional[str] = None
    status: str
    reminder_sent: bool


class AppointmentStatusUpdate(BaseModel):
    status: str  # "completed" or "cancelled"


# ---------------------------------------------------------------------------
# MEDICAL RECORD
# ---------------------------------------------------------------------------
class MedicalRecordCreate(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    diagnosis: str
    prescription: Optional[str] = None
    notes: Optional[str] = None


class MedicalRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    diagnosis: str
    prescription: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
