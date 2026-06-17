"""
STEP 6c: PATIENT ENDPOINTS
-------------------------------
Viewing patient profiles. Patients can see their own profile;
doctors can look up any patient (needed to write medical records
and review history).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user, require_role

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/me", response_model=schemas.PatientOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("patient")),
):
    patient = db.query(models.Patient).filter(models.Patient.user_id == current_user.id).first()
    return patient


@router.get("", response_model=list[schemas.PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_role("doctor")),
):
    """Only doctors can see the full patient list (for managing their clinic)."""
    return db.query(models.Patient).all()


@router.get("/{patient_id}", response_model=schemas.PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # A patient may only view THEIR OWN profile this way; doctors can view any patient
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own profile")

    return patient
