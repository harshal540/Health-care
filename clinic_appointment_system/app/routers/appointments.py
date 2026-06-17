"""
STEP 6d: APPOINTMENT ENDPOINTS
-----------------------------------
The heart of the system. Booking, viewing, updating, and cancelling
appointments - including the check that stops two people from
booking the same doctor at the same time.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user, require_role

router = APIRouter(prefix="/appointments", tags=["Appointments"])

# If two appointments for the same doctor are within this many minutes
# of each other, we treat it as a clash. Matches the 30-minute slot grid
# used in doctors.py's available-slots endpoint.
CONFLICT_WINDOW_MINUTES = 29


@router.post("", response_model=schemas.AppointmentOut, status_code=201)
def book_appointment(
    payload: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("patient")),
):
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
    doctor = db.query(models.Doctor).filter(models.Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Treat the submitted time as plain "clinic local time" (keeps things simple)
    requested_time = payload.appointment_time.replace(tzinfo=None)

    if requested_time < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Cannot book an appointment in the past")

    # --- THE DOUBLE-BOOKING CHECK ---
    # Is there ALREADY a scheduled appointment for this doctor within
    # +/- 29 minutes of the requested time? If yes, reject the booking.
    conflict = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == payload.doctor_id,
        models.Appointment.status == "scheduled",
        models.Appointment.appointment_time >= requested_time - timedelta(minutes=CONFLICT_WINDOW_MINUTES),
        models.Appointment.appointment_time <= requested_time + timedelta(minutes=CONFLICT_WINDOW_MINUTES),
    ).first()
    if conflict:
        raise HTTPException(
            status_code=409,
            detail="This doctor already has an appointment around that time. Please pick another slot.",
        )

    appointment = models.Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_time=requested_time,
        reason=payload.reason,
        status="scheduled",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/me", response_model=list[schemas.AppointmentOut])
def my_appointments(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Patients see their own bookings; doctors see their own bookings too."""
    if current_user.role == "patient":
        patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
        return db.query(models.Appointment).filter(models.Appointment.patient_id == patient.id).all()

    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    return db.query(models.Appointment).filter(models.Appointment.doctor_id == doctor.id).all()


@router.put("/{appointment_id}/status", response_model=schemas.AppointmentOut)
def update_appointment_status(
    appointment_id: int,
    payload: schemas.AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("doctor")),
):
    """A doctor marks an appointment as completed or cancelled."""
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.doctor_id == doctor.id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if payload.status not in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail="status must be 'completed' or 'cancelled'")

    appointment.status = payload.status
    db.commit()
    db.refresh(appointment)
    return appointment


@router.delete("/{appointment_id}", response_model=schemas.AppointmentOut)
def cancel_my_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("patient")),
):
    """A patient cancels their own appointment."""
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.patient_id == patient.id,
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = "cancelled"
    db.commit()
    db.refresh(appointment)
    return appointment
