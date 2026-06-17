"""
STEP 6b: DOCTOR ENDPOINTS
-----------------------------
Browsing doctors, a doctor managing their own schedule, and the
"available slots" endpoint that lets a patient see open times
BEFORE trying to book - this is what makes double-booking rare
in the first place (the hard guarantee still happens at booking time).
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user, require_role

router = APIRouter(prefix="/doctors", tags=["Doctors"])

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SLOT_LENGTH_MINUTES = 30


@router.get("", response_model=list[schemas.DoctorOut])
def list_doctors(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Any logged-in user (patient or doctor) can browse all doctors."""
    return db.query(models.Doctor).all()


@router.get("/{doctor_id}", response_model=schemas.DoctorOut)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.put("/me/availability", response_model=schemas.DoctorOut)
def update_my_availability(
    payload: schemas.DoctorAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("doctor")),
):
    """A doctor updates their own working days / hours."""
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    doctor.working_days = payload.working_days
    doctor.start_time = payload.start_time
    doctor.end_time = payload.end_time
    db.commit()
    db.refresh(doctor)
    return doctor


@router.get("/{doctor_id}/available-slots")
def get_available_slots(
    doctor_id: int,
    date: str,  # expected format: "YYYY-MM-DD"
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Returns this doctor's free 30-minute slots on a given date,
    after removing slots that are already booked.
    """
    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    try:
        day_start = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be in YYYY-MM-DD format")

    if WEEKDAY_NAMES[day_start.weekday()] not in doctor.working_days.split(","):
        return {"date": date, "available_slots": [], "note": "Doctor does not work on this day"}

    start_hour, start_minute = map(int, doctor.start_time.split(":"))
    end_hour, end_minute = map(int, doctor.end_time.split(":"))
    window_start = day_start.replace(hour=start_hour, minute=start_minute)
    window_end = day_start.replace(hour=end_hour, minute=end_minute)

    # Build every 30-minute slot inside the doctor's working window
    all_slots = []
    slot = window_start
    while slot < window_end:
        all_slots.append(slot)
        slot += timedelta(minutes=SLOT_LENGTH_MINUTES)

    # Find appointments already booked for this doctor on this date
    day_end = day_start + timedelta(days=1)
    booked_rows = db.query(models.Appointment.appointment_time).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.status == "scheduled",
        models.Appointment.appointment_time >= day_start,
        models.Appointment.appointment_time < day_end,
    ).all()
    booked_times = {row[0] for row in booked_rows}

    free_slots = [s.strftime("%H:%M") for s in all_slots if s not in booked_times]
    return {"date": date, "available_slots": free_slots}
