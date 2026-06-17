"""
STEP 7: AUTOMATED APPOINTMENT REMINDERS
--------------------------------------------
Every minute, a background job checks for appointments happening in
the next 24 hours that haven't been reminded about yet, and "sends"
a reminder.

Here, "sending" just means printing to the console - swap that line
for real email/SMS sending in production (e.g. smtplib for email,
or a service like Twilio for SMS).
"""

from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from . import models
from .database import SessionLocal

scheduler = BackgroundScheduler()


def send_appointment_reminders():
    """Find upcoming appointments and mark/print their reminders."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        window_end = now + timedelta(hours=24)

        upcoming = db.query(models.Appointment).filter(
            models.Appointment.status == "scheduled",
            models.Appointment.reminder_sent.is_(False),
            models.Appointment.appointment_time >= now,
            models.Appointment.appointment_time <= window_end,
        ).all()

        for appt in upcoming:
            patient = appt.patient
            doctor = appt.doctor
            # --- PLUG REAL EMAIL/SMS SENDING IN HERE ---
            print(
                f"[REMINDER] Hi {patient.full_name}, you have an appointment with "
                f"Dr. {doctor.full_name} on {appt.appointment_time.strftime('%Y-%m-%d %H:%M')}."
            )
            appt.reminder_sent = True

        if upcoming:
            db.commit()
    finally:
        db.close()


def start_scheduler():
    # Checks every 1 minute. In a real clinic, every 15-60 minutes is plenty.
    scheduler.add_job(send_appointment_reminders, "interval", minutes=1, id="reminder_job")
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown(wait=False)
