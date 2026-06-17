"""
STEP 6a: AUTH ENDPOINTS
---------------------------
Registration and login. These are the ONLY endpoints that don't
require a token - because their entire job is to GIVE you one.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/patient", response_model=schemas.PatientOut, status_code=201)
def register_patient(payload: schemas.PatientRegister, db: Session = Depends(get_db)):
    # 1. Make sure this username/email isn't already taken
    existing = db.query(models.User).filter(
        (models.User.username == payload.username) | (models.User.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # 2. Create the LOGIN record
    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="patient",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 3. Create the PROFILE record, linked to that login
    patient = models.Patient(
        user_id=user.id,
        full_name=payload.full_name,
        age=payload.age,
        gender=payload.gender,
        phone=payload.phone,
        address=payload.address,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.post("/register/doctor", response_model=schemas.DoctorOut, status_code=201)
def register_doctor(payload: schemas.DoctorRegister, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(
        (models.User.username == payload.username) | (models.User.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="doctor",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    doctor = models.Doctor(
        user_id=user.id,
        full_name=payload.full_name,
        specialization=payload.specialization,
        working_days=payload.working_days,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    NOTE: this endpoint expects standard OAuth2 form fields
    (username + password), not JSON - that's what makes the
    Swagger UI's 'Authorize' button work automatically.
    """
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token(data={"user_id": str(user.id), "role": user.role})
    return schemas.Token(access_token=token, token_type="bearer", role=user.role)
