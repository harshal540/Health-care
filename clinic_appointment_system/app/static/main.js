/* =======================================================================
   Clinic Appointment System — Dashboard Frontend Logic
   Sidebar navigation + all backend endpoint integrations
   ======================================================================= */

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------------------
// DOM References
// ---------------------------------------------------------------------------
const authView       = $("auth-view");
const dashboardView  = $("dashboard-view");
const toastContainer = $("toast-container");
const toastBox       = $("toast-box");

const loginTab       = $("tab-login");
const registerTab    = $("tab-register");
const loginForm      = $("login-form");
const registerForm   = $("register-form");

const doctorFields   = $("doctor-fields");
const patientFields  = $("patient-fields");
const registerRole   = $("register-role");

const pageTitle      = $("page-title");
const userBadge      = $("user-badge");

const doctorList     = $("doctor-list");
const appointmentList= $("appointment-list");
const recordsList    = $("records-list");
const slotSection    = $("slot-section");
const slotsContainer = $("slots-container");
const slotDateInput  = $("slot-date");

const TOKEN_KEY = "clinic-token";
const ROLE_KEY  = "clinic-role";

let selectedDoctorId = null;

// ---------------------------------------------------------------------------
// Toast notifications
// ---------------------------------------------------------------------------
function showToast(text, type = "info") {
    toastContainer.classList.remove("hidden");
    toastBox.className = "toast";
    if (type === "error")   toastBox.classList.add("error");
    if (type === "success") toastBox.classList.add("success");
    toastBox.textContent = text;
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => toastContainer.classList.add("hidden"), 5000);
}

function parseError(data) {
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
        return data.detail.map((e) => {
            const field = e.loc ? e.loc.filter(p => p !== "body").join(" > ") : "unknown";
            return `${field}: ${e.msg}`;
        }).join("\n");
    }
    return JSON.stringify(data);
}

function getRole()  { return localStorage.getItem(ROLE_KEY); }
function getToken() { return localStorage.getItem(TOKEN_KEY); }
function authHeaders() {
    const t = getToken();
    return t ? { Authorization: `Bearer ${t}`, "Content-Type": "application/json" }
             : { "Content-Type": "application/json" };
}

// ---------------------------------------------------------------------------
// Sidebar navigation
// ---------------------------------------------------------------------------
const PAGE_TITLES = {
    overview: "Overview",
    doctors: "Doctors Directory",
    appointments: "My Appointments",
    records: "Medical Records",
    schedule: "My Schedule",
};

function navigateTo(pageName) {
    // Update nav links
    document.querySelectorAll(".nav-link[data-page]").forEach(link => {
        link.classList.toggle("active", link.dataset.page === pageName);
    });
    // Update page sections
    document.querySelectorAll(".page-section").forEach(sec => {
        sec.classList.toggle("active", sec.id === `page-${pageName}`);
    });
    // Update header title
    pageTitle.textContent = PAGE_TITLES[pageName] || pageName;

    // Auto-load data when navigating
    if (pageName === "overview")     loadOverviewStats();
    if (pageName === "doctors")      loadDoctors();
    if (pageName === "appointments") loadMyAppointments();
}

document.querySelectorAll(".nav-link[data-page]").forEach(link => {
    link.addEventListener("click", () => navigateTo(link.dataset.page));
});

// ---------------------------------------------------------------------------
// Session management
// ---------------------------------------------------------------------------
function setSession(token, role) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(ROLE_KEY, role);
    authView.classList.add("hidden");
    dashboardView.classList.remove("hidden");

    userBadge.textContent = role === "doctor" ? "Doctor" : "Patient";

    // Show/hide role-specific sidebar items
    $("nav-schedule").classList.toggle("hidden", role !== "doctor");

    // Medical records page: toggle patient vs doctor areas
    $("patient-records-area").classList.toggle("hidden", role !== "patient");
    $("doctor-records-area").classList.toggle("hidden", role !== "doctor");

    navigateTo("overview");
}

function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(ROLE_KEY);
    authView.classList.remove("hidden");
    dashboardView.classList.add("hidden");
    toastContainer.classList.add("hidden");
    doctorList.innerHTML = "";
    appointmentList.innerHTML = "";
    recordsList.innerHTML = "";
    slotsContainer.innerHTML = "";
    slotSection.classList.add("hidden");
}

// ---------------------------------------------------------------------------
// Auth tabs
// ---------------------------------------------------------------------------
function setActiveTab(tab) {
    loginTab.classList.toggle("active", tab === "login");
    registerTab.classList.toggle("active", tab === "register");
    loginForm.classList.toggle("active", tab === "login");
    registerForm.classList.toggle("active", tab === "register");
}
loginTab.addEventListener("click", () => setActiveTab("login"));
registerTab.addEventListener("click", () => setActiveTab("register"));

registerRole.addEventListener("change", () => {
    const r = registerRole.value;
    doctorFields.classList.toggle("hidden", r !== "doctor");
    patientFields.classList.toggle("hidden", r !== "patient");
});

// ---------------------------------------------------------------------------
// LOGIN
// ---------------------------------------------------------------------------
$("login-button").addEventListener("click", async () => {
    const username = $("login-username").value.trim();
    const password = $("login-password").value;
    if (!username || !password) { showToast("Please enter username and password.", "error"); return; }

    try {
        const res = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ username, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(parseError(data));
        setSession(data.access_token, data.role);
        showToast("Login successful!", "success");
    } catch (err) {
        showToast(`Login failed: ${err.message}`, "error");
    }
});

// ---------------------------------------------------------------------------
// REGISTER
// ---------------------------------------------------------------------------
$("register-button").addEventListener("click", async () => {
    const role = registerRole.value;
    const payload = {
        username:  $("register-username").value.trim(),
        email:     $("register-email").value.trim(),
        password:  $("register-password").value,
        full_name: $("register-full-name").value.trim(),
    };
    if (!payload.username || !payload.email || !payload.password || !payload.full_name) {
        showToast("Please fill in all required fields.", "error"); return;
    }

    if (role === "doctor") {
        payload.specialization = $("register-specialization").value.trim();
        payload.working_days   = $("register-working-days").value.trim() || "Mon,Tue,Wed,Thu,Fri";
        payload.start_time     = $("register-start-time").value || "09:00";
        payload.end_time       = $("register-end-time").value || "17:00";
        if (!payload.specialization) { showToast("Specialization is required.", "error"); return; }
    } else {
        payload.age     = parseInt($("register-age").value, 10);
        payload.gender  = $("register-gender").value.trim();
        payload.phone   = $("register-phone").value.trim();
        payload.address = $("register-address").value.trim() || null;
        if (!payload.gender || !payload.phone || isNaN(payload.age)) {
            showToast("Age, gender, and phone are required.", "error"); return;
        }
    }

    const url = role === "doctor" ? "/auth/register/doctor" : "/auth/register/patient";
    try {
        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(parseError(data));
        showToast(`Registered successfully! Please login.`, "success");
        setActiveTab("login");
    } catch (err) {
        showToast(`Registration failed: ${err.message}`, "error");
    }
});

// ---------------------------------------------------------------------------
// LOGOUT
// ---------------------------------------------------------------------------
$("logout-button").addEventListener("click", () => {
    clearSession();
    showToast("Logged out.", "info");
});

// ---------------------------------------------------------------------------
// OVERVIEW — load stats
// ---------------------------------------------------------------------------
async function loadOverviewStats() {
    try {
        const [docRes, apptRes] = await Promise.all([
            fetch("/doctors", { headers: authHeaders() }),
            fetch("/appointments/me", { headers: authHeaders() }),
        ]);
        const doctors = await docRes.json();
        const appts   = await apptRes.json();

        $("stat-doctors").textContent      = docRes.ok ? doctors.length : "-";
        $("stat-appointments").textContent  = apptRes.ok ? appts.length : "-";

        // Records stat depends on role
        if (getRole() === "patient") {
            const recRes = await fetch("/medical-records/me", { headers: authHeaders() });
            const recs = await recRes.json();
            $("stat-records").textContent = recRes.ok ? recs.length : "-";
        } else {
            $("stat-records").textContent = "--";
        }
    } catch {
        // silently fail — stats are best-effort
    }
}

// ---------------------------------------------------------------------------
// DOCTORS — list
// ---------------------------------------------------------------------------
$("load-doctors-button").addEventListener("click", loadDoctors);

async function loadDoctors() {
    doctorList.innerHTML = '<div class="empty-state"><span class="empty-icon">⏳</span>Loading doctors...</div>';
    try {
        const res = await fetch("/doctors", { headers: authHeaders() });
        const doctors = await res.json();
        if (!res.ok) throw new Error(parseError(doctors));

        doctorList.innerHTML = "";
        if (doctors.length === 0) {
            doctorList.innerHTML = '<div class="empty-state"><span class="empty-icon">👨‍⚕️</span>No doctors registered yet.</div>';
            return;
        }

        doctors.forEach(doc => {
            const el = document.createElement("div");
            el.className = "data-item";
            el.innerHTML = `
                <div class="data-item-header">
                    <strong>${doc.full_name}</strong>
                    <span class="badge badge-primary">${doc.specialization}</span>
                </div>
                <p class="meta">📅 ${doc.working_days} &nbsp;|&nbsp; 🕘 ${doc.start_time} – ${doc.end_time}</p>
                <div class="item-actions">
                    <button class="btn-sm" data-doc-id="${doc.id}">Check Available Slots</button>
                </div>
            `;
            el.querySelector("[data-doc-id]").addEventListener("click", () => {
                selectedDoctorId = doc.id;
                slotSection.classList.remove("hidden");
                slotsContainer.innerHTML = "";
                showToast(`Selected Dr. ${doc.full_name}. Pick a date and click "Check Slots".`, "info");
            });
            doctorList.appendChild(el);
        });
    } catch (err) {
        doctorList.innerHTML = "";
        showToast(`Could not load doctors: ${err.message}`, "error");
    }
}

// ---------------------------------------------------------------------------
// SLOTS
// ---------------------------------------------------------------------------
$("load-slots-button").addEventListener("click", () => {
    if (!selectedDoctorId) { showToast("Select a doctor first.", "error"); return; }
    loadSlots(selectedDoctorId);
});

async function loadSlots(docId) {
    const date = slotDateInput.value;
    if (!date) { showToast("Please select a date.", "error"); return; }
    slotsContainer.innerHTML = '<div class="empty-state">Loading...</div>';

    try {
        const res = await fetch(`/doctors/${docId}/available-slots?date=${date}`, { headers: authHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(parseError(data));

        slotsContainer.innerHTML = "";
        if (!data.available_slots || data.available_slots.length === 0) {
            slotsContainer.innerHTML = `<div class="empty-state" style="grid-column:1/-1;">${data.note || "No available slots."}</div>`;
            return;
        }

        data.available_slots.forEach(slot => {
            const chip = document.createElement("div");
            chip.className = "slot-chip";
            chip.innerHTML = `
                <span>${slot}</span>
                ${getRole() === "patient" ? `<button>Book</button>` : ""}
            `;
            const bookBtn = chip.querySelector("button");
            if (bookBtn) bookBtn.addEventListener("click", () => bookSlot(docId, date, slot));
            slotsContainer.appendChild(chip);
        });
    } catch (err) {
        slotsContainer.innerHTML = "";
        showToast(`Could not load slots: ${err.message}`, "error");
    }
}

// ---------------------------------------------------------------------------
// BOOK APPOINTMENT
// ---------------------------------------------------------------------------
async function bookSlot(docId, date, slot) {
    try {
        const res = await fetch("/appointments", {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ doctor_id: Number(docId), appointment_time: `${date}T${slot}:00`, reason: "Booked from UI" }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(parseError(data));
        showToast(`Appointment booked for ${date} at ${slot}.`, "success");
        loadSlots(docId);
        loadMyAppointments();
    } catch (err) {
        showToast(`Could not book: ${err.message}`, "error");
    }
}

// ---------------------------------------------------------------------------
// APPOINTMENTS — view mine
// ---------------------------------------------------------------------------
$("view-appointments-button").addEventListener("click", loadMyAppointments);

async function loadMyAppointments() {
    appointmentList.innerHTML = '<div class="empty-state"><span class="empty-icon">⏳</span>Loading...</div>';
    try {
        const res = await fetch("/appointments/me", { headers: authHeaders() });
        const appts = await res.json();
        if (!res.ok) throw new Error(parseError(appts));

        appointmentList.innerHTML = "";
        if (appts.length === 0) {
            appointmentList.innerHTML = '<div class="empty-state"><span class="empty-icon">📅</span>No appointments yet.</div>';
            return;
        }

        const role = getRole();
        appts.forEach(appt => {
            const el = document.createElement("div");
            el.className = "data-item";
            const time = new Date(appt.appointment_time).toLocaleString();
            el.innerHTML = `
                <div class="data-item-header">
                    <strong>Appointment #${appt.id}</strong>
                    <span class="badge badge-${appt.status}">${appt.status}</span>
                </div>
                <p class="meta">🩺 Doctor ID: ${appt.doctor_id} &nbsp;|&nbsp; 🧑 Patient ID: ${appt.patient_id}</p>
                <p class="meta">🕐 ${time}</p>
                <p class="meta">📝 ${appt.reason || "No reason given"}</p>
                <div class="item-actions" id="appt-act-${appt.id}"></div>
            `;

            const actions = el.querySelector(`#appt-act-${appt.id}`);
            if (appt.status === "scheduled") {
                if (role === "patient") {
                    const btn = document.createElement("button");
                    btn.className = "btn-danger";
                    btn.textContent = "Cancel";
                    btn.addEventListener("click", () => cancelAppointment(appt.id));
                    actions.appendChild(btn);
                }
                if (role === "doctor") {
                    const cBtn = document.createElement("button");
                    cBtn.className = "btn-success";
                    cBtn.textContent = "Complete";
                    cBtn.addEventListener("click", () => updateStatus(appt.id, "completed"));
                    actions.appendChild(cBtn);

                    const xBtn = document.createElement("button");
                    xBtn.className = "btn-danger";
                    xBtn.textContent = "Cancel";
                    xBtn.addEventListener("click", () => updateStatus(appt.id, "cancelled"));
                    actions.appendChild(xBtn);
                }
            }
            if (role === "doctor" && appt.status === "completed") {
                const rBtn = document.createElement("button");
                rBtn.className = "btn-outline";
                rBtn.textContent = "Write Record";
                rBtn.addEventListener("click", () => {
                    navigateTo("records");
                    $("record-patient-id").value = appt.patient_id;
                    $("record-appointment-id").value = appt.id;
                });
                actions.appendChild(rBtn);
            }

            appointmentList.appendChild(el);
        });
    } catch (err) {
        appointmentList.innerHTML = "";
        showToast(`Could not load appointments: ${err.message}`, "error");
    }
}

// ---------------------------------------------------------------------------
// CANCEL APPOINTMENT (patient)
// ---------------------------------------------------------------------------
async function cancelAppointment(id) {
    try {
        const res = await fetch(`/appointments/${id}`, { method: "DELETE", headers: authHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(parseError(data));
        showToast(`Appointment #${id} cancelled.`, "success");
        loadMyAppointments();
    } catch (err) {
        showToast(`Could not cancel: ${err.message}`, "error");
    }
}

// ---------------------------------------------------------------------------
// UPDATE STATUS (doctor)
// ---------------------------------------------------------------------------
async function updateStatus(id, status) {
    try {
        const res = await fetch(`/appointments/${id}/status`, {
            method: "PUT", headers: authHeaders(),
            body: JSON.stringify({ status }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(parseError(data));
        showToast(`Appointment #${id} marked as ${status}.`, "success");
        loadMyAppointments();
    } catch (err) {
        showToast(`Could not update: ${err.message}`, "error");
    }
}

// ---------------------------------------------------------------------------
// MEDICAL RECORDS — patient views theirs
// ---------------------------------------------------------------------------
$("view-my-records-button").addEventListener("click", loadMyRecords);

async function loadMyRecords() {
    recordsList.innerHTML = '<div class="empty-state"><span class="empty-icon">⏳</span>Loading...</div>';
    try {
        const res = await fetch("/medical-records/me", { headers: authHeaders() });
        const recs = await res.json();
        if (!res.ok) throw new Error(parseError(recs));

        recordsList.innerHTML = "";
        if (recs.length === 0) {
            recordsList.innerHTML = '<div class="empty-state"><span class="empty-icon">📋</span>No medical records yet.</div>';
            return;
        }

        recs.forEach(rec => {
            const el = document.createElement("div");
            el.className = "data-item";
            el.innerHTML = `
                <div class="data-item-header">
                    <strong>Record #${rec.id}</strong>
                    <span class="badge badge-primary">Doctor #${rec.doctor_id}</span>
                </div>
                ${rec.appointment_id ? `<p class="meta">Appointment #${rec.appointment_id}</p>` : ""}
                <p class="meta"><b>Diagnosis:</b> ${rec.diagnosis}</p>
                ${rec.prescription ? `<p class="meta"><b>Prescription:</b> ${rec.prescription}</p>` : ""}
                ${rec.notes ? `<p class="meta"><b>Notes:</b> ${rec.notes}</p>` : ""}
                <p class="meta" style="color:var(--text-muted);font-size:.78rem;">Created: ${new Date(rec.created_at).toLocaleString()}</p>
            `;
            recordsList.appendChild(el);
        });
    } catch (err) {
        recordsList.innerHTML = "";
        showToast(`Could not load records: ${err.message}`, "error");
    }
}

// ---------------------------------------------------------------------------
// MEDICAL RECORDS — doctor creates one
// ---------------------------------------------------------------------------
$("submit-record-button").addEventListener("click", async () => {
    const patientId     = parseInt($("record-patient-id").value, 10);
    const appointmentId = $("record-appointment-id").value ? parseInt($("record-appointment-id").value, 10) : null;
    const diagnosis     = $("record-diagnosis").value.trim();
    const prescription  = $("record-prescription").value.trim() || null;
    const notes         = $("record-notes").value.trim() || null;

    if (isNaN(patientId) || !diagnosis) {
        showToast("Patient ID and Diagnosis are required.", "error"); return;
    }

    try {
        const res = await fetch("/medical-records", {
            method: "POST", headers: authHeaders(),
            body: JSON.stringify({ patient_id: patientId, appointment_id: appointmentId, diagnosis, prescription, notes }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(parseError(data));
        showToast("Medical record saved.", "success");
        $("record-diagnosis").value = "";
        $("record-prescription").value = "";
        $("record-notes").value = "";
    } catch (err) {
        showToast(`Could not save record: ${err.message}`, "error");
    }
});

// ---------------------------------------------------------------------------
// DOCTOR — update availability
// ---------------------------------------------------------------------------
$("save-availability-button").addEventListener("click", async () => {
    const working_days = $("avail-working-days").value.trim();
    const start_time   = $("avail-start-time").value;
    const end_time     = $("avail-end-time").value;
    if (!working_days || !start_time || !end_time) {
        showToast("Please fill in all schedule fields.", "error"); return;
    }
    try {
        const res = await fetch("/doctors/me/availability", {
            method: "PUT", headers: authHeaders(),
            body: JSON.stringify({ working_days, start_time, end_time }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(parseError(data));
        showToast("Schedule updated.", "success");
    } catch (err) {
        showToast(`Could not update schedule: ${err.message}`, "error");
    }
});

// ---------------------------------------------------------------------------
// INIT
// ---------------------------------------------------------------------------
function init() {
    const token = getToken();
    const role  = getRole();
    if (token && role) {
        setSession(token, role);
    } else {
        clearSession();
    }
}

init();
