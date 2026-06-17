"""
STEP 3: DATABASE TABLES (MODELS)
----------------------------------
Each class below becomes one TABLE in clinic.db.
This is the "single source of truth" for what data we store.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def now_utc() -> datetime:
    """A timezone-naive 'current UTC time', used for created_at timestamps."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """
    Every person who can log in (a patient OR a doctor) gets ONE row here.
    This table only stores LOGIN information (username/email/password/role).
    Personal/profile details live in the Patient or Doctor table below.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "patient" or "doctor"

    # These let us write `some_user.patient_profile` or `some_user.doctor_profile`
    patient_profile = relationship("Patient", back_populates="user", uselist=False)
    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)


class Patient(Base):
    """A patient's profile information, linked 1-to-1 with a User."""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    phone = Column(String)
    address = Column(String)

    user = relationship("User", back_populates="patient_profile")
    appointments = relationship("Appointment", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")


class Doctor(Base):
    """A doctor's profile, including their weekly working schedule."""
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    specialization = Column(String, nullable=False)

    # A simple weekly schedule - which days they work, and daily hours
    working_days = Column(String, default="Mon,Tue,Wed,Thu,Fri")  # e.g. "Mon,Wed,Fri"
    start_time = Column(String, default="09:00")  # 24-hour format "HH:MM"
    end_time = Column(String, default="17:00")

    user = relationship("User", back_populates="doctor_profile")
    appointments = relationship("Appointment", back_populates="doctor")
    medical_records = relationship("MedicalRecord", back_populates="doctor")


class Appointment(Base):
    """One booked appointment between a patient and a doctor."""
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    reason = Column(String)
    status = Column(String, default="scheduled")  # scheduled | completed | cancelled
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now_utc)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")


class MedicalRecord(Base):
    """A doctor's diagnosis / prescription / notes for a patient."""
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    diagnosis = Column(Text, nullable=False)
    prescription = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=now_utc)

    patient = relationship("Patient", back_populates="medical_records")
    doctor = relationship("Doctor", back_populates="medical_records")
