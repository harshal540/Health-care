"""
STEP 6e: MEDICAL RECORD ENDPOINTS
--------------------------------------
Doctors write medical records (diagnosis, prescription, notes) for a
patient, usually right after an appointment. Patients can read their
own records; doctors can read any patient's full history.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import require_role

router = APIRouter(prefix="/medical-records", tags=["Medical Records"])


@router.post("", response_model=schemas.MedicalRecordOut, status_code=201)
def create_medical_record(
    payload: schemas.MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("doctor")),
):
    doctor = db.query(models.Doctor).filter(models.Doctor.user_id == current_user.id).first()
    patient = db.query(models.Patient).filter(models.Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    record = models.MedicalRecord(
        patient_id=payload.patient_id,
        doctor_id=doctor.id,
        appointment_id=payload.appointment_id,
        diagnosis=payload.diagnosis,
        prescription=payload.prescription,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/me", response_model=list[schemas.MedicalRecordOut])
def my_medical_records(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("patient")),
):
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
    return db.query(models.MedicalRecord).filter(models.MedicalRecord.patient_id == patient.id).all()


@router.get("/patient/{patient_id}", response_model=list[schemas.MedicalRecordOut])
def patient_medical_records(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("doctor")),
):
    """A doctor reviews the full medical history of any patient."""
    return db.query(models.MedicalRecord).filter(models.MedicalRecord.patient_id == patient_id).all()
