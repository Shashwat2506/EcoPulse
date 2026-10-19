/**
 * EcoPulse: Smart Sustainability Tracker
 * Frontend Controller, 3D Canvas Earth Simulation, History Chart & Dynamic Reactive State
 */

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initMobileNav();
    initAccordion();
    initPillSwitch();
    initModals();
    initMetricsForm();
    initEarthView();
    initHistoryChart();
});

/* ==========================================================================
   Global State
   ========================================================================== */
const AppState = {
    activeEntryId: null,
    historyData: [],
    benchmarks: { global_average: 4.0, us_average: 16.0 },
    pendingDeleteId: null
};

/* ==========================================================================
   Theme Management
   ========================================================================== */
function initTheme() {
    const themeToggleBtn = document.getElementById("theme-toggle");
    const savedTheme = localStorage.getItem("ecopulse_theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("ecopulse_theme", newTheme);
            // Redraw canvas charts with theme awareness
            renderHistoryChart();
        });
    }
}

function initMobileNav() {
    const toggle = document.getElementById("mobile-menu-toggle");
    const nav = document.getElementById("main-nav");
    if (toggle && nav) {
        toggle.addEventListener("click", () => {
            nav.classList.toggle("mobile-open");
        });
    }
}

/* ==========================================================================
   Accordion Controller
   ========================================================================== */
function initAccordion() {
    const items = document.querySelectorAll(".accordion-item");
    items.forEach(item => {
        const header = item.querySelector(".accordion-header");
        if (!header) return;

        header.addEventListener("click", () => {
            const isOpen = item.classList.contains("open");
            // Optional: close other accordions or toggle
            items.forEach(other => {
                if (other !== item) other.classList.remove("open");
            });
            item.classList.toggle("open", !isOpen);
        });
    });
}

/* ==========================================================================
   Pill Switcher (Manual vs Echo Recommendations)
   ========================================================================== */
function initPillSwitch() {
    const pillManual = document.getElementById("pill-manual");
    const pillEcho = document.getElementById("pill-echo");
    const manualView = document.getElementById("metrics-panel-view");
    const echoView = document.getElementById("recommendations-panel-view");

    if (!pillManual || !pillEcho || !manualView || !echoView) return;

    pillManual.addEventListener("click", () => {
        pillManual.classList.add("active");
        pillEcho.classList.remove("active");
        manualView.style.display = "block";
        echoView.style.display = "none";
    });

    pillEcho.addEventListener("click", () => {
        pillEcho.classList.add("active");
        pillManual.classList.remove("active");
        manualView.style.display = "none";
        echoView.style.display = "block";
    });
}

/* ==========================================================================
   Modals & Toast Notifications
   ========================================================================== */
function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type === "error" ? "toast-error" : ""}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === "error" ? "&#x26A0;" : "&#x2714;"}</span>
        <span class="toast-msg">${message}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(50px)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function initModals() {
    // Info Modal
    const infoTrigger = document.getElementById("info-trigger");
    const infoModal = document.getElementById("info-modal");
    const infoClose = document.getElementById("info-modal-close");
    const infoOk = document.getElementById("info-modal-ok");

    const closeInfo = () => { if (infoModal) infoModal.style.display = "none"; };

    if (infoTrigger && infoModal) {
        infoTrigger.addEventListener("click", () => { infoModal.style.display = "flex"; });
    }
    if (infoClose) infoClose.addEventListener("click", closeInfo);
    if (infoOk) infoOk.addEventListener("click", closeInfo);

    // Delete Confirmation Modal
    const confirmModal = document.getElementById("confirm-modal");
    const cancelBtn = document.getElementById("modal-cancel-btn");
    const confirmBtn = document.getElementById("modal-confirm-btn");

    if (cancelBtn && confirmModal) {
        cancelBtn.addEventListener("click", () => {
            confirmModal.style.display = "none";
            AppState.pendingDeleteId = null;
        });
    }

    if (confirmBtn && confirmModal) {
        confirmBtn.addEventListener("click", async () => {
            if (AppState.pendingDeleteId !== null) {
                await executeDeleteEntry(AppState.pendingDeleteId);
                confirmModal.style.display = "none";
                AppState.pendingDeleteId = null;
            }
        });
    }
}

function confirmDeleteEntry(id, title) {
    AppState.pendingDeleteId = id;
    const modal = document.getElementById("confirm-modal");
    const msg = document.getElementById("modal-message");
    if (msg) msg.textContent = `Are you sure you want to permanently delete "${title}"?`;
    if (modal) modal.style.display = "flex";
}

/* ==========================================================================
   Metrics Form & CRUD Operations
   ========================================================================== */
function initMetricsForm() {
    const form = document.getElementById("metrics-form");
    const btnNewLog = document.getElementById("btn-new-log");

    // Read initial active ID
    const entryIdInput = document.getElementById("entry-id-input");
    if (entryIdInput && entryIdInput.value) {
        AppState.activeEntryId = parseInt(entryIdInput.value, 10);
    }

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            await saveMetricsForm();
        });
    }

    // Also attach direct click handlers to all Save buttons
    const saveButtons = document.querySelectorAll(".btn-save");
    saveButtons.forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.preventDefault();
            await saveMetricsForm();
        });
    });

    if (btnNewLog) {
        btnNewLog.addEventListener("click", () => {
            createNewLog();
        });
    }
}

function getFormData() {
    return {
        vehicle_miles_per_week: parseFloat(document.getElementById("vehicle_miles_per_week")?.value) || 0,
        vehicle_mpg: parseFloat(document.getElementById("vehicle_mpg")?.value) || 30,
        vehicle_maintenance: document.getElementById("vehicle_maintenance")?.checked || false,
        transit_miles_per_week: parseFloat(document.getElementById("transit_miles_per_week")?.value) || 0,
        flights_per_year: parseFloat(document.getElementById("flights_per_year")?.value) || 0,
        electricity_kwh_per_month: parseFloat(document.getElementById("electricity_kwh_per_month")?.value) || 0,
        clean_energy_pct: parseFloat(document.getElementById("clean_energy_pct")?.value) || 0,
        heating_units_per_month: parseFloat(document.getElementById("heating_units_per_month")?.value) || 0,
        waste_bags_per_week: parseFloat(document.getElementById("waste_bags_per_week")?.value) || 0,
        recycling_habit: document.getElementById("recycling_habit")?.value || "regularly",
        composting_habit: document.getElementById("composting_habit")?.checked || false,
        diet_habit: document.getElementById("diet_habit")?.value || "average",
        shopping_habit: document.getElementById("shopping_habit")?.value || "average",
        reusable_habit: document.getElementById("reusable_habit")?.checked || false
    };
}

async function saveMetricsForm() {
    const formData = getFormData();
    const entryId = AppState.activeEntryId;
    const isUpdate = !!entryId;
    const url = isUpdate ? `/api/entries/${entryId}` : "/api/entries";
    const method = isUpdate ? "PUT" : "POST";

    const titleInput = document.getElementById("entry-title-input");
    const payload = {
        ...formData,
        title: titleInput ? titleInput.value : null
    };

    try {
        const response = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showToast(data.message || "Assessment saved successfully!");
            AppState.activeEntryId = data.entry.id;

            // Update UI elements with recalculated data
            updateDashboardView(data.entry);
            // Refresh entries sidebar and history
            await refreshEntriesList(data.entry.id);
            await fetchHistory();
        } else {
            const errDetails = data.errors ? Object.values(data.errors).join(" ") : data.message;
            showToast(errDetails || "Error saving assessment.", "error");
        }
    } catch (err) {
        showToast("Network error while saving assessment.", "error");
    }
}

async function loadEntry(id) {
    try {
        const response = await fetch(`/api/entries/${id}`);
        const data = await response.json();
        if (response.ok && data.success) {
            AppState.activeEntryId = id;
            populateForm(data.entry);
            updateDashboardView(data.entry);
            highlightActiveEntryInSidebar(id);
            showToast(`Loaded "${data.entry.title}"`);
        } else {
            showToast("Failed to load entry.", "error");
        }
    } catch (err) {
        showToast("Error loading entry.", "error");
    }
}

function createNewLog() {
    AppState.activeEntryId = null;

    // Reset form inputs to friendly clean defaults
    const defaults = {
        vehicle_miles_per_week: 180,
        vehicle_mpg: 30,
        vehicle_maintenance: true,
        transit_miles_per_week: 40,
        flights_per_year: 1,
        electricity_kwh_per_month: 400,
        clean_energy_pct: 0,
        heating_units_per_month: 25,
        waste_bags_per_week: 2,
        recycling_habit: "regularly",
        composting_habit: false,
        diet_habit: "average",
        shopping_habit: "average",
        reusable_habit: true
    };

    populateForm({ inputs: defaults, title: "New Log" });

    // Dry-run calculation for instant feedback
    fetch("/api/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(defaults)
    })
    .then(r => r.json())
    .then(data => {
        if (data.calculations) {
            updateDashboardView({
                id: null,
                title: "New Log",
                calculations: data.calculations
            });
        }
    });

    highlightActiveEntryInSidebar(null);
    showToast("Prepared fresh log assessment. Adjust values and click 'Save Changes'.");
}

function populateForm(entry) {
    const inputs = entry.inputs || {};

    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val !== undefined ? val : "";
    };
    const setCheck = (id, checked) => {
        const el = document.getElementById(id);
        if (el) el.checked = !!checked;
    };

    setVal("vehicle_miles_per_week", inputs.vehicle_miles_per_week);
    setVal("vehicle_mpg", inputs.vehicle_mpg);
    setCheck("vehicle_maintenance", inputs.vehicle_maintenance);
    setVal("transit_miles_per_week", inputs.transit_miles_per_week);
    setVal("flights_per_year", inputs.flights_per_year);

    setVal("electricity_kwh_per_month", inputs.electricity_kwh_per_month);
    setVal("clean_energy_pct", inputs.clean_energy_pct);
    setVal("heating_units_per_month", inputs.heating_units_per_month);

    setVal("waste_bags_per_week", inputs.waste_bags_per_week);
    setVal("recycling_habit", inputs.recycling_habit || "regularly");
    setCheck("composting_habit", inputs.composting_habit);

    setVal("diet_habit", inputs.diet_habit || "average");
    setVal("shopping_habit", inputs.shopping_habit || "average");
    setCheck("reusable_habit", inputs.reusable_habit);

    const titleEl = document.getElementById("entry-title-input");
    if (titleEl) titleEl.value = entry.title || "Assessment";

    const idEl = document.getElementById("entry-id-input");
    if (idEl) idEl.value = entry.id || "";
}

function updateDashboardView(entry) {
    const calc = entry.calculations;
    if (!calc) return;

    // 1. Carbon Footprint Hero
    const heroTonnes = document.getElementById("display-footprint-tonnes");
    if (heroTonnes) heroTonnes.textContent = calc.primary_display_tonnes || (calc.total_tonnes).toFixed(1);

    const weeklyVal = document.getElementById("stat-weekly-val");
    if (weeklyVal) weeklyVal.textContent = `${Math.round(calc.weekly_kg)} kg`;

    const monthlyVal = document.getElementById("stat-monthly-val");
    if (monthlyVal) monthlyVal.textContent = `${calc.monthly_tonnes.toFixed(2)} t`;

    const benchmarkBadge = document.getElementById("benchmark-badge");
    if (benchmarkBadge) {
        const diff = calc.benchmarks.vs_global_diff_pct;
        benchmarkBadge.textContent = `${diff >= 0 ? "+" + diff : diff}% vs Global`;
    }

    // 2. Breakdown Bars
    const bk = calc.breakdown;
    if (bk) {
        const updateBar = (cat, pct) => {
            const bar = document.getElementById(`bar-${cat}`);
            const text = document.getElementById(`pct-${cat}`);
            if (bar) bar.style.width = `${pct}%`;
            if (text) text.textContent = `${pct}%`;
        };
        updateBar("transportation", bk.transportation.percentage);
        updateBar("energy", bk.energy.percentage);
        updateBar("waste", bk.waste.percentage);
        updateBar("other", bk.other.percentage);

        const totalKgEl = document.getElementById("breakdown-total-kg");
        if (totalKgEl) totalKgEl.textContent = `${Math.round(calc.total_kg)} kg CO2e`;
    }

    // 3. Active Title Tag
    const tag = document.getElementById("active-log-tag");
    if (tag) tag.textContent = entry.title || "Assessment";

    // 4. Echo Recommendations
    renderRecommendations(calc.recommendations);
}

function renderRecommendations(recs) {
    const container = document.getElementById("recommendations-container");
    if (!container || !recs) return;

    container.innerHTML = "";
    recs.forEach(rec => {
        const badgeClass = (rec.badge || "").toLowerCase().replace(/\s+/g, "-");
        const item = document.createElement("div");
        item.className = "rec-item";
        item.innerHTML = `
            <div class="rec-top">
                <span class="rec-badge ${badgeClass}">${rec.badge}</span>
                <span class="rec-cat">${rec.category}</span>
            </div>
            <h4 class="rec-title">${rec.title}</h4>
            <p class="rec-text">${rec.description}</p>
        `;
        container.appendChild(item);
    });
}

async function executeDeleteEntry(id) {
    try {
        const response = await fetch(`/api/entries/${id}`, { method: "DELETE" });
        const data = await response.json();
        if (response.ok && data.success) {
            showToast("Assessment log deleted.");
            // If active entry was deleted, switch to new log or another entry
            await refreshEntriesList();
            await fetchHistory();

            const firstRow = document.querySelector(".entry-row");
            if (firstRow && firstRow.dataset.entryId) {
                await loadEntry(parseInt(firstRow.dataset.entryId, 10));
            } else {
                createNewLog();
            }
        } else {
            showToast(data.message || "Failed to delete log.", "error");
        }
    } catch (err) {
        showToast("Error deleting log.", "error");
    }
}

async function refreshEntriesList(selectId = null) {
    const listEl = document.getElementById("entries-list");
    if (!listEl) return;

    try {
        const response = await fetch("/api/entries");
        const data = await response.json();
        if (response.ok && data.entries) {
            listEl.innerHTML = "";
            if (data.entries.length === 0) {
                listEl.innerHTML = `
                    <div class="entry-row active" id="entry-row-fresh">
                        <button type="button" class="entry-select-btn">
                            <span class="entry-name">Log #1</span>
                        </button>
                    </div>
                `;
            } else {
                data.entries.forEach(entry => {
                    const row = document.createElement("div");
                    const isActive = selectId ? entry.id === selectId : entry.id === AppState.activeEntryId;
                    row.className = `entry-row ${isActive ? "active" : ""}`;
                    row.id = `entry-row-${entry.id}`;
                    row.dataset.entryId = entry.id;

                    row.innerHTML = `
                        <button type="button" class="entry-select-btn" onclick="loadEntry(${entry.id})" aria-label="Load ${entry.title}">
                            <span class="entry-name">${entry.title}</span>
                        </button>
                        <button type="button" class="entry-delete-btn" onclick="confirmDeleteEntry(${entry.id}, '${entry.title}')" title="Delete ${entry.title}" aria-label="Delete ${entry.title}">&times;</button>
                    `;
                    listEl.appendChild(row);
                });
            }
        }
    } catch (err) {
        console.error("Failed to refresh entries list:", err);
    }
}

function highlightActiveEntryInSidebar(id) {
    const rows = document.querySelectorAll(".entry-row");
    rows.forEach(r => {
        if (id && r.dataset.entryId == id) {
            r.classList.add("active");
        } else {
            r.classList.remove("active");
        }
    });
}

/* ==========================================================================
   History Chart (HTML5 Canvas Engine)
   ========================================================================== */
async function initHistoryChart() {
    window.addEventListener("resize", renderHistoryChart);
    await fetchHistory();
}

async function fetchHistory() {
    try {
        const response = await fetch("/api/history");
        const data = await response.json();
        if (response.ok && data.history) {
            AppState.historyData = data.history;
            if (data.benchmarks) AppState.benchmarks = data.benchmarks;
            renderHistoryChart();
        }
    } catch (err) {
        console.error("Failed to fetch history:", err);
    }
}

function renderHistoryChart() {
    const canvas = document.getElementById("historyChart");
    const emptyState = document.getElementById("history-empty-state");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;

    ctx.clearRect(0, 0, w, h);

    const history = AppState.historyData;
    if (!history || history.length === 0) {
        if (emptyState) emptyState.style.display = "flex";
        return;
    } else {
        if (emptyState) emptyState.style.display = "none";
    }

    const padLeft = 45;
    const padRight = 75;
    const padTop = 25;
    const padBottom = 30;

    const chartW = w - padLeft - padRight;
    const chartH = h - padTop - padBottom;

    // Y Axis Range: benchmark US is 16, global is 4
    const maxVal = Math.max(22, ...history.map(d => d.total_tonnes));
    const minVal = 0;

    const getY = (val) => padTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
    const getX = (idx, total) => total <= 1 ? padLeft + chartW / 2 : padLeft + (idx / (total - 1)) * chartW;

    // Draw Subtle Grid & Benchmark Horizontal Dashed Lines
    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    const gridColor = isDark ? "rgba(255, 255, 255, 0.06)" : "rgba(0, 0, 0, 0.06)";
    const labelColor = isDark ? "#64748b" : "#94a3b8";

    ctx.lineWidth = 1;
    ctx.strokeStyle = gridColor;

    // Baseline 0
    ctx.beginPath();
    ctx.moveTo(padLeft, getY(0));
    ctx.lineTo(w - padRight, getY(0));
    ctx.stroke();

    // Benchmark Lines: Global (4.0 t) and US (16.0 t)
    const drawBenchmark = (val, label) => {
        const y = getY(val);
        ctx.save();
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = isDark ? "rgba(255, 255, 255, 0.25)" : "rgba(0, 0, 0, 0.25)";
        ctx.beginPath();
        ctx.moveTo(padLeft, y);
        ctx.lineTo(w - padRight, y);
        ctx.stroke();

        // Label Tag
        ctx.setLineDash([]);
        ctx.fillStyle = isDark ? "#171a1f" : "#e2e8f0";
        ctx.fillRect(w - padRight + 6, y - 9, 62, 18);
        ctx.strokeStyle = isDark ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.15)";
        ctx.strokeRect(w - padRight + 6, y - 9, 62, 18);

        ctx.fillStyle = labelColor;
        ctx.font = "10px sans-serif";
        ctx.fillText(label, w - padRight + 10, y + 4);
        ctx.restore();
    };

    drawBenchmark(AppState.benchmarks.global_average || 4.0, "Global 4.0");
    drawBenchmark(AppState.benchmarks.us_average || 16.0, "US 16.0");

    // Plot Points and Draw Gradient Area
    const points = history.map((entry, idx) => ({
        x: getX(idx, history.length),
        y: getY(entry.total_tonnes),
        val: entry.total_tonnes,
        title: entry.title
    }));

    if (points.length > 0) {
        // Area Gradient
        const grad = ctx.createLinearGradient(0, padTop, 0, padTop + chartH);
        grad.addColorStop(0, "rgba(16, 185, 129, 0.35)");
        grad.addColorStop(1, "rgba(16, 185, 129, 0.0)");

        ctx.beginPath();
        ctx.moveTo(points[0].x, getY(0));
        points.forEach((pt, i) => {
            if (i === 0) ctx.lineTo(pt.x, pt.y);
            else ctx.lineTo(pt.x, pt.y);
        });
        ctx.lineTo(points[points.length - 1].x, getY(0));
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();

        // Glowing Line
        ctx.save();
        ctx.beginPath();
        ctx.strokeStyle = "#10b981";
        ctx.lineWidth = 2.5;
        ctx.shadowColor = "rgba(16, 185, 129, 0.6)";
        ctx.shadowBlur = 10;
        points.forEach((pt, i) => {
            if (i === 0) ctx.moveTo(pt.x, pt.y);
            else ctx.lineTo(pt.x, pt.y);
        });
        ctx.stroke();
        ctx.restore();

        // Data Point Dots
        points.forEach((pt, idx) => {
            ctx.save();
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
            ctx.fillStyle = "#10b981";
            ctx.fill();
            ctx.lineWidth = 2;
            ctx.strokeStyle = isDark ? "#0c0e12" : "#ffffff";
            ctx.stroke();

            // X-Axis Label
            ctx.fillStyle = labelColor;
            ctx.font = "10px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText(pt.title.replace("Log #", "#"), pt.x, h - 10);
            ctx.restore();
        });

        // Current Highlight Tag on the Last Point
        const lastPt = points[points.length - 1];
        ctx.save();
        ctx.fillStyle = "#10b981";
        ctx.fillRect(w - padRight + 6, lastPt.y - 10, 48, 20);
        ctx.fillStyle = "#0c0e12";
        ctx.font = "bold 11px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(lastPt.val.toFixed(2), w - padRight + 30, lastPt.y + 4);
        ctx.restore();
    }
}

/* ==========================================================================
   3D Earth Simulation Engine (Self-Contained Low-Poly Faceted Canvas 3D)
   Recreates the exact low-poly green & charcoal Earth with orbiting space debris!
   ========================================================================== */
function initEarthView() {
    const canvas = document.getElementById("earthCanvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let rotX = 0.25;
    let rotY = 0.0;
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let velX = 0;
    let velY = 0.005;

    // Mouse & Touch Drag Controls
    canvas.addEventListener("mousedown", (e) => {
        isDragging = true;
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
    });

    window.addEventListener("mouseup", () => {
        isDragging = false;
    });

    canvas.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        const dx = e.clientX - prevMouseX;
        const dy = e.clientY - prevMouseY;
        velY = dx * 0.005;
        velX = dy * 0.005;
        rotY += velY;
        rotX += velX;
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
    });

    // Touch controls
    canvas.addEventListener("touchstart", (e) => {
        if (e.touches.length === 1) {
            isDragging = true;
            prevMouseX = e.touches[0].clientX;
            prevMouseY = e.touches[0].clientY;
        }
    }, { passive: true });

    window.addEventListener("touchend", () => { isDragging = false; });

    canvas.addEventListener("touchmove", (e) => {
        if (!isDragging || e.touches.length !== 1) return;
        const dx = e.touches[0].clientX - prevMouseX;
        const dy = e.touches[0].clientY - prevMouseY;
        rotY += dx * 0.005;
        rotX += dy * 0.005;
        prevMouseX = e.touches[0].clientX;
        prevMouseY = e.touches[0].clientY;
    }, { passive: true });

    // Generate Low-Poly Faceted Geodesic Sphere
    const { vertices, faces } = createGeodesicGlobe(130, 2);

    // Generate Orbiting Low-Poly Rocks/Debris
    const rocks = createOrbitalRocks(12);

    function animate() {
        if (!isDragging) {
            rotY += 0.006;
            velX *= 0.95;
            rotX += velX;
            rotX = Math.max(-0.8, Math.min(0.8, rotX)); // limit vertical pitch
        }

        renderGlobe(ctx, canvas, vertices, faces, rocks, rotX, rotY);
        requestAnimationFrame(animate);
    }

    animate();
}

/**
 * Builds an icosahedron-subdivided sphere with landmass heuristics
 */
function createGeodesicGlobe(radius, subdivisions) {
    const t = (1.0 + Math.sqrt(5.0)) / 2.0;

    let verts = [
        [-1,  t,  0], [ 1,  t,  0], [-1, -t,  0], [ 1, -t,  0],
        [ 0, -1,  t], [ 0,  1,  t], [ 0, -1, -t], [ 0,  1, -t],
        [ t,  0, -1], [ t,  0,  1], [-t,  0, -1], [-t,  0,  1]
    ];

    // Normalize initial vertices to radius
    verts = verts.map(v => normalizeVec(v, radius));

    let fList = [
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
    ];

    // Subdivide
    for (let s = 0; s < subdivisions; s++) {
        const newFaces = [];
        const midCache = {};

        function getMidPoint(p1, p2) {
            const key = p1 < p2 ? `${p1}_${p2}` : `${p2}_${p1}`;
            if (midCache[key] !== undefined) return midCache[key];
            const v1 = verts[p1];
            const v2 = verts[p2];
            const mid = [
                (v1[0] + v2[0]) / 2,
                (v1[1] + v2[1]) / 2,
                (v1[2] + v2[2]) / 2
            ];
            const normMid = normalizeVec(mid, radius);
            const idx = verts.length;
            verts.push(normMid);
            midCache[key] = idx;
            return idx;
        }

        fList.forEach(([a, b, c]) => {
            const ab = getMidPoint(a, b);
            const bc = getMidPoint(b, c);
            const ca = getMidPoint(c, a);
            newFaces.push([a, ab, ca]);
            newFaces.push([b, bc, ab]);
            newFaces.push([c, ca, bc]);
            newFaces.push([ab, bc, ca]);
        });
        fList = newFaces;
    }

    // Determine Landmass vs Ocean based on spherical coordinates (Americas, Eurasia, Africa)
    const facesWithTerrain = fList.map(face => {
        const vA = verts[face[0]];
        const vB = verts[face[1]];
        const vC = verts[face[2]];
        const cx = (vA[0] + vB[0] + vC[0]) / 3;
        const cy = (vA[1] + vB[1] + vC[1]) / 3;
        const cz = (vA[2] + vB[2] + vC[2]) / 3;

        const len = Math.sqrt(cx * cx + cy * cy + cz * cz);
        const lat = Math.asin(cy / len) * (180 / Math.PI);
        const lon = Math.atan2(cx, cz) * (180 / Math.PI);

        // Approximate continent bounding regions
        const isNorthAmerica = (lat >= 10 && lat <= 70 && lon >= -160 && lon <= -50);
        const isSouthAmerica = (lat >= -55 && lat <= 12 && lon >= -80 && lon <= -35);
        const isEuropeAfrica = (lat >= -35 && lat <= 65 && lon >= -18 && lon <= 50);
        const isAsia = (lat >= 8 && lat <= 75 && lon >= 50 && lon <= 150);
        const isAustralia = (lat >= -45 && lat <= -10 && lon >= 110 && lon <= 155);

        const isLand = isNorthAmerica || isSouthAmerica || isEuropeAfrica || isAsia || isAustralia;

        return {
            indices: face,
            isLand: isLand
        };
    });

    return { vertices: verts, faces: facesWithTerrain };
}

function normalizeVec(v, targetRadius) {
    const len = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
    return [
        (v[0] / len) * targetRadius,
        (v[1] / len) * targetRadius,
        (v[2] / len) * targetRadius
    ];
}

function createOrbitalRocks(count) {
    const rocks = [];
    for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2;
        const distance = 165 + (i % 3) * 20;
        const yOffset = (Math.sin(i * 1.5) * 50);
        const size = 5 + (i % 4) * 3;
        rocks.push({
            angle: angle,
            distance: distance,
            yOffset: yOffset,
            speed: 0.008 + (i % 3) * 0.004,
            size: size
        });
    }
    return rocks;
}

function renderGlobe(ctx, canvas, vertices, faces, rocks, rotX, rotY) {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const centerX = w / 2;
    const centerY = h / 2;
    const fov = 400;

    // Directional light vector (coming from top-left)
    const lx = -0.5, ly = -0.6, lz = 0.6;
    const lightLen = Math.sqrt(lx * lx + ly * ly + lz * lz);
    const light = [lx / lightLen, ly / lightLen, lz / lightLen];

    // Atmospheric Glow Halo
    const atmosphereGrad = ctx.createRadialGradient(centerX, centerY, 100, centerX, centerY, 175);
    atmosphereGrad.addColorStop(0, "rgba(16, 185, 129, 0.0)");
    atmosphereGrad.addColorStop(0.7, "rgba(16, 185, 129, 0.08)");
    atmosphereGrad.addColorStop(1, "rgba(16, 185, 129, 0.0)");
    ctx.fillStyle = atmosphereGrad;
    ctx.beginPath();
    ctx.arc(centerX, centerY, 175, 0, Math.PI * 2);
    ctx.fill();

    // Transform Vertices: Rotate around X then Y
    const cosY = Math.cos(rotY), sinY = Math.sin(rotY);
    const cosX = Math.cos(rotX), sinX = Math.sin(rotX);

    const transformed = vertices.map(([x, y, z]) => {
        // Rot Y
        const x1 = x * cosY + z * sinY;
        const y1 = y;
        const z1 = -x * sinY + z * cosY;

        // Rot X
        const x2 = x1;
        const y2 = y1 * cosX - z1 * sinX;
        const z2 = y1 * sinX + z1 * cosX;

        // 3D Perspective Projection
        const scale = fov / (fov + z2);
        return {
            x: centerX + x2 * scale,
            y: centerY + y2 * scale,
            z: z2
        };
    });

    // Prepare faces with normal and average Z for painter's algorithm
    const renderList = [];

    faces.forEach(({ indices, isLand }) => {
        const p0 = transformed[indices[0]];
        const p1 = transformed[indices[1]];
        const p2 = transformed[indices[2]];

        // Cross product for backface culling & flat shading
        const vAx = p1.x - p0.x, vAy = p1.y - p0.y;
        const vBx = p2.x - p0.x, vBy = p2.y - p0.y;
        const crossZ = vAx * vBy - vAy * vBx;

        // If crossZ > 0, triangle is facing the camera
        if (crossZ > 0) {
            const avgZ = (p0.z + p1.z + p2.z) / 3;

            // Compute 3D surface normal for realistic lighting
            const u = [vertices[indices[1]][0] - vertices[indices[0]][0], vertices[indices[1]][1] - vertices[indices[0]][1], vertices[indices[1]][2] - vertices[indices[0]][2]];
            const v = [vertices[indices[2]][0] - vertices[indices[0]][0], vertices[indices[2]][1] - vertices[indices[0]][1], vertices[indices[2]][2] - vertices[indices[0]][2]];
            const nx = u[1] * v[2] - u[2] * v[1];
            const ny = u[2] * v[0] - u[0] * v[2];
            const nz = u[0] * v[1] - u[1] * v[0];
            const nLen = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;

            // Rotate normal
            const nX1 = (nx / nLen) * cosY + (nz / nLen) * sinY;
            const nY1 = (ny / nLen);
            const nZ1 = -(nx / nLen) * sinY + (nz / nLen) * cosY;
            const nY2 = nY1 * cosX - nZ1 * sinX;
            const nZ2 = nY1 * sinX + nZ1 * cosX;

            const dot = Math.max(0, -(nX1 * light[0] + nY2 * light[1] + nZ2 * light[2]));
            const intensity = 0.25 + 0.75 * dot;

            renderList.push({
                type: "globe-face",
                pts: [p0, p1, p2],
                z: avgZ,
                isLand: isLand,
                intensity: intensity
            });
        }
    });

    // Update & Project Orbiting Space Debris / Satellites
    rocks.forEach(rock => {
        rock.angle += rock.speed;
        const rx = Math.cos(rock.angle) * rock.distance;
        const rz = Math.sin(rock.angle) * rock.distance;
        const ry = rock.yOffset;

        // Apply same rotation
        const rx1 = rx * cosY + rz * sinY;
        const ry1 = ry;
        const rz1 = -rx * sinY + rz * cosY;

        const rx2 = rx1;
        const ry2 = ry1 * cosX - rz1 * sinX;
        const rz2 = ry1 * sinX + rz1 * cosX;

        const scale = fov / (fov + rz2);
        const px = centerX + rx2 * scale;
        const py = centerY + ry2 * scale;

        renderList.push({
            type: "rock",
            x: px,
            y: py,
            z: rz2,
            size: rock.size * scale
        });
    });

    // Sort by depth (farthest first)
    renderList.sort((a, b) => b.z - a.z);

    // Draw Elements
    renderList.forEach(item => {
        if (item.type === "globe-face") {
            ctx.beginPath();
            ctx.moveTo(item.pts[0].x, item.pts[0].y);
            ctx.lineTo(item.pts[1].x, item.pts[1].y);
            ctx.lineTo(item.pts[2].x, item.pts[2].y);
            ctx.closePath();

            if (item.isLand) {
                // Emerald Green Land
                const r = Math.round(16 * item.intensity);
                const g = Math.round(185 * item.intensity);
                const b = Math.round(129 * item.intensity);
                ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
                ctx.strokeStyle = `rgba(5, 150, 105, 0.4)`;
            } else {
                // Charcoal Gray Ocean
                const v = Math.round(36 * item.intensity);
                ctx.fillStyle = `rgb(${v}, ${v + 4}, ${v + 8})`;
                ctx.strokeStyle = `rgba(255, 255, 255, 0.05)`;
            }

            ctx.lineWidth = 0.5;
            ctx.fill();
            ctx.stroke();
        } else if (item.type === "rock") {
            // Draw Faceted Orbiting Space Rock / Asteroid
            ctx.save();
            ctx.translate(item.x, item.y);
            ctx.fillStyle = "#8a94a2";
            ctx.strokeStyle = "#4b5563";
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            const s = item.size;
            ctx.moveTo(-s, 0);
            ctx.lineTo(-s * 0.4, -s * 0.9);
            ctx.lineTo(s * 0.6, -s * 0.8);
            ctx.lineTo(s, 0);
            ctx.lineTo(s * 0.5, s * 0.9);
            ctx.lineTo(-s * 0.5, s * 0.7);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            ctx.restore();
        }
    });
}

// Expose functions globally for inline HTML event handlers
window.loadEntry = loadEntry;
window.confirmDeleteEntry = confirmDeleteEntry;
window.createNewLog = createNewLog;
window.saveMetricsForm = saveMetricsForm;

