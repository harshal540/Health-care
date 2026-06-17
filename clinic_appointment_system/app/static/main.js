const authSection = document.getElementById("auth-section");
const loginTab = document.getElementById("tab-login");
const registerTab = document.getElementById("tab-register");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const dashboardSection = document.getElementById("dashboard-section");
const messageSection = document.getElementById("message-section");
const messageBox = document.getElementById("message-box");
const loginStatus = document.getElementById("login-status");

const loginButton = document.getElementById("login-button");
const registerButton = document.getElementById("register-button");
const logoutButton = document.getElementById("logout-button");
const loadDoctorsButton = document.getElementById("load-doctors-button");
const viewAppointmentsButton = document.getElementById("view-appointments-button");
const loadSlotsButton = document.getElementById("load-slots-button");

const doctorList = document.getElementById("doctor-list");
const appointmentList = document.getElementById("appointment-list");
const slotSection = document.getElementById("slot-section");
const slotsContainer = document.getElementById("slots-container");
const slotDateInput = document.getElementById("slot-date");

const tokenKey = "clinic-token";
const roleKey = "clinic-role";

function showMessage(text) {
    messageSection.classList.remove("hidden");
    messageBox.textContent = text;
}

function hideMessage() {
    messageSection.classList.add("hidden");
    messageBox.textContent = "";
}

function setSession(token, role) {
    localStorage.setItem(tokenKey, token);
    localStorage.setItem(roleKey, role);
    loginStatus.textContent = `Logged in as ${role}`;
    authSection.classList.add("hidden");
    dashboardSection.classList.remove("hidden");
}

function clearSession() {
    localStorage.removeItem(tokenKey);
    localStorage.removeItem(roleKey);
    loginStatus.textContent = "";
    authSection.classList.remove("hidden");
    dashboardSection.classList.add("hidden");
    slotSection.classList.add("hidden");
    doctorList.innerHTML = "";
    appointmentList.innerHTML = "";
    slotsContainer.innerHTML = "";
    hideMessage();
}

function getAuthHeaders() {
    const token = localStorage.getItem(tokenKey);
    return token ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
}

function setActiveTab(tabName) {
    if (tabName === "login") {
        loginTab.classList.add("active");
        registerTab.classList.remove("active");
        loginForm.classList.add("active");
        registerForm.classList.remove("active");
    } else {
        loginTab.classList.remove("active");
        registerTab.classList.add("active");
        loginForm.classList.remove("active");
        registerForm.classList.add("active");
    }
}

loginTab.addEventListener("click", () => setActiveTab("login"));
registerTab.addEventListener("click", () => setActiveTab("register"));

loginButton.addEventListener("click", async () => {
    hideMessage();
    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ username, password }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || JSON.stringify(data));
        setSession(data.access_token, data.role);
        showMessage("Login successful. Load doctors or your appointments.");
    } catch (err) {
        showMessage(`Login failed: ${err.message}`);
    }
});

registerButton.addEventListener("click", async () => {
    hideMessage();
    const role = document.getElementById("register-role").value;
    const payload = {
        username: document.getElementById("register-username").value,
        email: document.getElementById("register-email").value,
        password: document.getElementById("register-password").value,
        full_name: document.getElementById("register-full-name").value,
    };

    if (role === "doctor") {
        payload.specialization = document.getElementById("register-specialization").value;
        payload.working_days = document.getElementById("register-working-days").value;
        payload.start_time = document.getElementById("register-start-time").value || "09:00";
        payload.end_time = document.getElementById("register-end-time").value || "17:00";
    } else {
        payload.age = parseInt(document.getElementById("register-age").value, 10);
        payload.gender = document.getElementById("register-gender").value;
        payload.phone = document.getElementById("register-phone").value;
        payload.address = document.getElementById("register-address").value;
    }

    try {
        const response = await fetch(role === "doctor" ? "/auth/register/doctor" : "/auth/register/patient", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || JSON.stringify(data));
        showMessage(`${role.charAt(0).toUpperCase() + role.slice(1)} registration successful. Please login.`);
        setActiveTab("login");
    } catch (err) {
        showMessage(`Registration failed: ${err.message}`);
    }
});

logoutButton.addEventListener("click", () => {
    clearSession();
    showMessage("Logged out.");
});

loadDoctorsButton.addEventListener("click", async () => {
    hideMessage();
    doctorList.innerHTML = "Loading doctors...";
    try {
        const response = await fetch("/doctors", { headers: getAuthHeaders() });
        const doctors = await response.json();
        if (!response.ok) throw new Error(doctors.detail || JSON.stringify(doctors));
        doctorList.innerHTML = "";
        doctors.forEach((doctor) => {
            const item = document.createElement("div");
            item.className = "list-item";
            item.innerHTML = `
                <strong>${doctor.full_name}</strong> — ${doctor.specialization}
                <p>Working: ${doctor.working_days} ${doctor.start_time}-${doctor.end_time}</p>
                <button data-doctor-id="${doctor.id}">Check available slots</button>
            `;
            const button = item.querySelector("button");
            button.addEventListener("click", () => loadSlotsForDoctor(doctor.id));
            doctorList.appendChild(item);
        });
        slotSection.classList.remove("hidden");
    } catch (err) {
        doctorList.innerHTML = "";
        showMessage(`Could not load doctors: ${err.message}`);
    }
});

viewAppointmentsButton.addEventListener("click", async () => {
    hideMessage();
    appointmentList.innerHTML = "Loading appointments...";
    try {
        const response = await fetch("/appointments/me", { headers: getAuthHeaders() });
        const appointments = await response.json();
        if (!response.ok) throw new Error(appointments.detail || JSON.stringify(appointments));
        appointmentList.innerHTML = "";
        if (appointments.length === 0) {
            appointmentList.innerHTML = "No appointments found.";
            return;
        }
        appointments.forEach((appointment) => {
            const item = document.createElement("div");
            item.className = "list-item";
            item.innerHTML = `
                <strong>Appointment #${appointment.id}</strong>
                <p>Doctor ID: ${appointment.doctor_id}</p>
                <p>Time: ${new Date(appointment.appointment_time).toLocaleString()}</p>
                <p>Status: ${appointment.status}</p>
                <p>Reason: ${appointment.reason || "None"}</p>
            `;
            appointmentList.appendChild(item);
        });
    } catch (err) {
        appointmentList.innerHTML = "";
        showMessage(`Could not load appointments: ${err.message}`);
    }
});

loadSlotsButton.addEventListener("click", () => {
    const selectedDoctorButton = doctorList.querySelector("button[data-doctor-id]");
    if (!selectedDoctorButton) {
        showMessage("Load doctors first, then choose a doctor to check slots.");
        return;
    }
    const doctorId = selectedDoctorButton.dataset.doctorId;
    loadSlotsForDoctor(doctorId);
});

async function loadSlotsForDoctor(doctorId) {
    hideMessage();
    const date = slotDateInput.value;
    if (!date) {
        showMessage("Please select a date to check available slots.");
        return;
    }
    slotsContainer.innerHTML = "Loading slots...";
    try {
        const response = await fetch(`/doctors/${doctorId}/available-slots?date=${date}`, { headers: getAuthHeaders() });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || JSON.stringify(data));
        slotsContainer.innerHTML = "";
        if (!data.available_slots || data.available_slots.length === 0) {
            slotsContainer.innerHTML = `<div class='list-item'>No available slots for ${date}.</div>`;
            return;
        }
        data.available_slots.forEach((slot) => {
            const item = document.createElement("div");
            item.className = "list-item";
            item.innerHTML = `
                <strong>${slot}</strong>
                <button data-slot="${slot}" data-doctor-id="${doctorId}">Book slot</button>
            `;
            item.querySelector("button").addEventListener("click", () => bookSlot(doctorId, date, slot));
            slotsContainer.appendChild(item);
        });
    } catch (err) {
        slotsContainer.innerHTML = "";
        showMessage(`Could not load available slots: ${err.message}`);
    }
}

async function bookSlot(doctorId, date, slot) {
    hideMessage();
    const appointmentTime = `${date}T${slot}:00`;
    try {
        const response = await fetch("/appointments", {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ doctor_id: Number(doctorId), appointment_time: appointmentTime, reason: "Booked from UI" }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || JSON.stringify(data));
        showMessage(`Appointment booked for ${appointmentTime}.`);
        await viewAppointmentsButton.click();
    } catch (err) {
        showMessage(`Could not book appointment: ${err.message}`);
    }
}

function init() {
    if (localStorage.getItem(tokenKey)) {
        setSession(localStorage.getItem(tokenKey), localStorage.getItem(roleKey));
    } else {
        clearSession();
    }
}

init();
