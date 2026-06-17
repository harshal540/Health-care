# Clinic Appointment Management System

A FastAPI app, secured with JWT, that solves the classic small-clinic
problem: manual scheduling that leads to double bookings, missed
appointments, and messy patient records.

## What it does

- **Patient registration & login** (JWT-secured)
- **Doctor registration**, with a weekly working schedule (days + hours)
- **Appointment booking** that **blocks double-booking** automatically
- **"Available slots" lookup** so patients see open times before booking
- **Medical records** doctors can attach to a patient's history
- **Automated reminders** - a background job that "notifies" patients
  about appointments in the next 24 hours

## Project structure

```
clinic_appointment_system/
├── requirements.txt
└── app/
    ├── main.py            <- start here: wires everything together
    ├── database.py        <- SQLite connection
    ├── models.py           <- database tables
    ├── schemas.py          <- API input/output shapes
    ├── security.py          <- password hashing + JWT
    ├── scheduler.py          <- automated reminders
    └── routers/
        ├── auth.py            <- register / login
        ├── patients.py         <- patient profiles
        ├── doctors.py           <- doctor list, schedule, open slots
        ├── appointments.py       <- booking, viewing, cancelling
        └── medical_records.py     <- diagnosis / prescriptions / notes
```

Each file has comments explaining what it does and why - read them in
the order listed above and the whole system will make sense step by step.

## 1. Setup (one-time)

```bash
cd clinic_appointment_system

# Create an isolated environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Run it

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** - this gives you an interactive
page where you can try every endpoint without writing any code. A
file called `clinic.db` (SQLite database) will appear automatically;
that's where all your data lives.

## 3. Try the full flow (in the `/docs` page)

1. **POST `/auth/register/doctor`** - create a doctor, e.g.
   ```json
   {
     "username": "drsmith",
     "email": "drsmith@example.com",
     "password": "pass1234",
     "full_name": "Dr. Smith",
     "specialization": "General Medicine",
     "working_days": "Mon,Tue,Wed,Thu,Fri",
     "start_time": "09:00",
     "end_time": "17:00"
   }
   ```
2. **POST `/auth/register/patient`** - create a patient, e.g.
   ```json
   {
     "username": "john",
     "email": "john@example.com",
     "password": "pass1234",
     "full_name": "John Doe",
     "age": 30,
     "gender": "male",
     "phone": "9999999999"
   }
   ```
3. **POST `/auth/login`** as `john` - copy the `access_token` you get back.
4. Click the green **"Authorize"** button at the top of `/docs`, paste
   the token in, and click Authorize. Now every request you make is
   sent as John.
5. **GET `/doctors/1/available-slots?date=2026-06-20`** - see open times.
6. **POST `/appointments`** - book one:
   ```json
   { "doctor_id": 1, "appointment_time": "2026-06-20T10:00:00", "reason": "Checkup" }
   ```
7. Try booking the **same doctor + same time again** with a different
   patient account - you'll get a `409 Conflict` error instead of a
   silent double-booking.
8. Log in as the doctor instead, and try:
   - **PUT `/appointments/1/status`** with `{"status": "completed"}`
   - **POST `/medical-records`** to add a diagnosis for that patient

While the server runs, check your terminal once a minute - any
appointment within 24 hours will print a `[REMINDER]` line. That's the
background job from `scheduler.py` working automatically.

## How double-booking is actually prevented

Two layers, both inside `app/routers/`:

1. `doctors.py` → `/doctors/{id}/available-slots` shows only the slots
   that aren't already taken, so most patients never even try a
   conflicting time.
2. `appointments.py` → `book_appointment()` re-checks the database at
   the moment of booking (within a +/-29 minute window for that doctor)
   and rejects the request with a `409` error if a clash is found. This
   second check is the real guarantee - it protects against two people
   submitting requests at almost the same instant.

## Notes for turning this into a real production app

- **Secret key**: `SECRET_KEY` in `security.py` is hardcoded for
  learning purposes. In production, load it from an environment
  variable and never commit it to source control.
- **Real reminders**: replace the `print(...)` line in `scheduler.py`
  with actual email (e.g. `smtplib`, SendGrid) or SMS (e.g. Twilio) code.
- **Bigger database**: change `DATABASE_URL` in `database.py` to a
  PostgreSQL/MySQL connection string when you outgrow SQLite - no other
  file needs to change.
- **Time zones**: this project treats all appointment times as plain
  "clinic local time" to keep things simple. A multi-location clinic
  would want to store and convert time zones explicitly.
- **Password reset, refresh tokens, rate limiting** are common next
  additions once the core flow above feels solid.
