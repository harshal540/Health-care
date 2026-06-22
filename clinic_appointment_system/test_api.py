import requests

BASE = "http://127.0.0.1:8000"

def test_full_flow():
    # 1. Register doctor
    print("=== Register Doctor ===")
    r = requests.post(f"{BASE}/auth/register/doctor", json={
        "username": "drsmith", "email": "drsmith@test.com", "password": "pass1234",
        "full_name": "Dr. Smith", "specialization": "General Medicine",
        "working_days": "Mon,Tue,Wed,Thu,Fri,Sat,Sun", "start_time": "09:00", "end_time": "17:00"
    })
    print(r.status_code, r.json())
    assert r.status_code == 201

    # 2. Register patient
    print("\n=== Register Patient ===")
    r = requests.post(f"{BASE}/auth/register/patient", json={
        "username": "john", "email": "john@test.com", "password": "pass1234",
        "full_name": "John Doe", "age": 30, "gender": "male", "phone": "9999999999"
    })
    print(r.status_code, r.json())
    assert r.status_code == 201
    patient_id = r.json()["id"]

    # 3. Login as patient
    print("\n=== Login Patient ===")
    r = requests.post(f"{BASE}/auth/login", data={"username": "john", "password": "pass1234"})
    print(r.status_code)
    assert r.status_code == 200
    pat_token = r.json()["access_token"]
    pat_headers = {"Authorization": f"Bearer {pat_token}"}

    # 4. Get doctors
    print("\n=== List Doctors ===")
    r = requests.get(f"{BASE}/doctors", headers=pat_headers)
    print(r.status_code, r.json())
    assert r.status_code == 200
    doc_id = r.json()[0]["id"]

    # 5. Check available slots
    print("\n=== Available Slots ===")
    r = requests.get(f"{BASE}/doctors/{doc_id}/available-slots?date=2026-06-25", headers=pat_headers)
    print(r.status_code, r.json())
    assert r.status_code == 200

    # 6. Book appointment
    print("\n=== Book Appointment ===")
    r = requests.post(f"{BASE}/appointments", json={
        "doctor_id": doc_id, "appointment_time": "2026-06-25T10:00:00", "reason": "Checkup"
    }, headers=pat_headers)
    print(r.status_code, r.json())
    assert r.status_code == 201
    appt_id = r.json()["id"]

    # 7. View patient appointments
    print("\n=== Patient Appointments ===")
    r = requests.get(f"{BASE}/appointments/me", headers=pat_headers)
    print(r.status_code, r.json())
    assert r.status_code == 200

    # 8. Login as doctor
    print("\n=== Login Doctor ===")
    r = requests.post(f"{BASE}/auth/login", data={"username": "drsmith", "password": "pass1234"})
    assert r.status_code == 200
    doc_token = r.json()["access_token"]
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    # 9. Doctor views appointments
    print("\n=== Doctor Appointments ===")
    r = requests.get(f"{BASE}/appointments/me", headers=doc_headers)
    print(r.status_code, r.json())
    assert r.status_code == 200

    # 10. Doctor completes appointment
    print("\n=== Complete Appointment ===")
    r = requests.put(f"{BASE}/appointments/{appt_id}/status", json={"status": "completed"}, headers=doc_headers)
    print(r.status_code, r.json())
    assert r.status_code == 200

    # 11. Doctor creates medical record
    print("\n=== Create Medical Record ===")
    r = requests.post(f"{BASE}/medical-records", json={
        "patient_id": patient_id, "appointment_id": appt_id,
        "diagnosis": "Common cold", "prescription": "Rest + fluids", "notes": "Follow up in 1 week"
    }, headers=doc_headers)
    print(r.status_code, r.json())
    assert r.status_code == 201

    # 12. Doctor views patient records
    print("\n=== Doctor Views Patient Records ===")
    r = requests.get(f"{BASE}/medical-records/patient/{patient_id}", headers=doc_headers)
    print(r.status_code, r.json())
    assert r.status_code == 200

    # 13. Patient views own medical records
    print("\n=== Patient Views Own Records ===")
    r = requests.get(f"{BASE}/medical-records/me", headers=pat_headers)
    print(r.status_code, r.json())
    assert r.status_code == 200

    # 14. Doctor updates availability
    print("\n=== Update Availability ===")
    r = requests.put(f"{BASE}/doctors/me/availability", json={
        "working_days": "Mon,Wed,Fri", "start_time": "10:00", "end_time": "16:00"
    }, headers=doc_headers)
    print(r.status_code, r.json())
    assert r.status_code == 200

    # 15. Patient views profile
    print("\n=== Patient Profile ===")
    r = requests.get(f"{BASE}/patients/me", headers=pat_headers)
    print(r.status_code, r.json())
    assert r.status_code == 200

    # 16. Doctor lists patients
    print("\n=== Doctor Lists Patients ===")
    r = requests.get(f"{BASE}/patients", headers=doc_headers)
    print(r.status_code, r.json())
    assert r.status_code == 200

    # 17. Test double-booking protection (use a fresh slot that's still scheduled)
    print("\n=== Book 11:00 Slot ===")
    r = requests.post(f"{BASE}/appointments", json={
        "doctor_id": doc_id, "appointment_time": "2026-06-25T11:00:00", "reason": "First"
    }, headers=pat_headers)
    print(r.status_code, r.json())
    assert r.status_code == 201

    print("\n=== Double Booking Test (same slot) ===")
    r = requests.post(f"{BASE}/appointments", json={
        "doctor_id": doc_id, "appointment_time": "2026-06-25T11:00:00", "reason": "Duplicate"
    }, headers=pat_headers)
    print(r.status_code, r.json())
    assert r.status_code == 409

    # 18. Test UI page loads
    print("\n=== UI Page ===")
    r = requests.get(f"{BASE}/")
    print(r.status_code, "OK" if r.status_code == 200 else "FAIL")
    assert r.status_code == 200

    print("\n=== ALL TESTS PASSED! ===")

test_full_flow()
