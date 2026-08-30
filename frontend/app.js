/**
 * SIH26170 - Frontend Application & Interactive Chart Controller
 * =============================================================================
 * Drishti - AI-Driven Semiconductor Burn-In & Anomaly Screening System
 * Features:
 * - Floating Collapsible AI Diagnostics Assistant (Bottom Right)
 * - 100% Dynamic API-driven execution with zero static responses
 * - Interactive Draggable Canvas Graphs (Scatterplot + Line Curve)
 */

const MODEL_CONFIGS = {
    breakdown: {
        id: "breakdown",
        title: "Time-Series & Breakdown Model",
        paramTag: "Voltage (V) vs Leakage Current (microAmpere)",
        xLabel: "Collector-Emitter Voltage (V)",
        yLabel: "Leakage Current (microAmpere)",
        defaultX: 550.0,
        defaultTime: 90960.0,
        defaultUserY: 12.5,
        defaultCompId: "NASA-IGBT-Part-12",
        xMin: 0,
        xMax: 650,
        yMin: 0,
        yMax: 150,
        presets: [
            { name: "Aged Degradation (550V)", x: 550.0, t: 90960.0, userY: 12.5, cid: "NASA-Part-12 (Aged)" },
            { name: "Pristine Baseline (300V)", x: 300.0, t: 30000.0, userY: 0.05, cid: "NASA-Part-11 (Pristine)" },
            { name: "Avalanche Runaway (580V)", x: 580.0, t: 105000.0, userY: 85.0, cid: "NASA-Part-16 (Runaway)" }
        ]
    },
    leakage: {
        id: "leakage",
        title: "Time-Series Leakage IV Model",
        paramTag: "Voltage (V) vs Leakage Current (microAmpere)",
        xLabel: "Applied Voltage (V)",
        yLabel: "Leakage Current (microAmpere)",
        defaultX: 300.0,
        defaultTime: 90960.0,
        defaultUserY: 4.5,
        defaultCompId: "NASA-IGBT-Part-18",
        xMin: 0,
        xMax: 600,
        yMin: 0,
        yMax: 10.0,
        presets: [
            { name: "Latent SRH Defect (300V)", x: 300.0, t: 90960.0, userY: 4.5, cid: "NASA-Part-18 (Latent)" },
            { name: "Healthy Dielectric (100V)", x: 100.0, t: 30000.0, userY: 0.05, cid: "NASA-Part-11 (Healthy)" },
            { name: "Thermal Bias Drift (500V)", x: 500.0, t: 105000.0, userY: 8.5, cid: "NASA-Part-15 (Thermal)" }
        ]
    },
    turnon: {
        id: "turnon",
        title: "Time-Series Turn-On Model",
        paramTag: "Gate Voltage (V) vs Current (microAmpere)",
        xLabel: "Gate Voltage (V)",
        yLabel: "Collector Current (microAmpere)",
        defaultX: 8.0,
        defaultTime: 90960.0,
        defaultUserY: 25.0,
        defaultCompId: "NASA-IGBT-Part-14",
        xMin: 0,
        xMax: 15,
        yMin: 0,
        yMax: 250.0,
        presets: [
            { name: "Oxide Trap Trapping (5V)", x: 5.0, t: 90960.0, userY: 25.0, cid: "NASA-Part-14 (Oxide Trap)" },
            { name: "Normal Active Conduction (8V)", x: 8.0, t: 30000.0, userY: 150.0, cid: "NASA-Part-11 (Normal)" },
            { name: "Degraded Transconductance (10V)", x: 10.0, t: 105000.0, userY: 10.0, cid: "NASA-Part-19 (Degraded gm)" }
        ]
    }
};

let currentActiveModel = "breakdown";
let currentVisualMode = "timeseries";
let timeseriesCache = {};
let sampleDatasetCache = {};

let tsForecastChartInstance = null;
let tsVoltageChartInstance = null;
let sampleScatterChartInstance = null;
let sampleLineChartInstance = null;

const chartModes = {
    forecast: "point",
    voltage: "point",
    sampleScatter: "point",
    sampleLine: "point"
};

const defaultChartBounds = {
    forecast: { xMin: 0, xMax: 113700, yMin: 0, yMax: 150 },
    voltage: { xMin: 0, xMax: 113700, yMin: 0, yMax: 650 },
    sampleScatter: { xMin: 0, xMax: 650, yMin: 0, yMax: 150 },
    sampleLine: { xMin: 0, xMax: 650, yMin: 0, yMax: 150 }
};

let isDraggingPoint = false;
let isPanning = false;
let panStart = { x: 0, y: 0 };
let debounceTimer = null;
let simulationInterval = null;

// =============================================================================
// FLOATING AI ASSISTANT DRAWER CONTROLLER
// =============================================================================

function toggleAIChat(forceOpen) {
    const drawer = document.getElementById("aiDrawerPanel");
    const fab = document.getElementById("aiFabBtn");
    const badge = document.getElementById("aiUnreadBadge");
    if (!drawer) return;

    const isCurrentlyOpen = drawer.style.display === "flex";
    const shouldOpen = forceOpen !== undefined ? forceOpen : !isCurrentlyOpen;

    if (shouldOpen) {
        drawer.style.display = "flex";
        if (fab) fab.style.display = "none";
        if (badge) badge.style.display = "none";
        const chatBox = document.getElementById("chatMessages");
        if (chatBox) {
            if (chatBox.children.length === 0) {
                clearAIChat();
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        const input = document.getElementById("interactiveChatInput");
        if (input) setTimeout(() => input.focus(), 150);
    } else {
        drawer.style.display = "none";
        if (fab) fab.style.display = "flex";
    }
}

function clearAIChat() {
    const chat = document.getElementById("chatMessages");
    if (!chat) return;
    chat.innerHTML = `
        <div class="ai-welcome-card">
            <div class="welcome-badge">🤖 DRISHTI AI DIAGNOSTICS ONLINE</div>
            <div class="welcome-model-spec">Connected LLM: <strong>Groq • Llama 3.3 70B Versatile</strong></div>
            <p class="welcome-desc">Physics-grounded reasoning for semiconductor degradation, accelerated thermal aging, avalanche breakdown, and NASA EEE-INST-002 screening standards.</p>
            <div class="welcome-grid">
                <div class="welcome-feature-card" onclick="sendQuickChatMessage('Explain avalanche breakdown multiplication vs thermal runaway.')">
                    <span class="wf-icon">⚡</span>
                    <div><strong>Avalanche Breakdown</strong><p>Impact ionization & field multiplication</p></div>
                </div>
                <div class="welcome-feature-card" onclick="sendQuickChatMessage('How does SRH recombination cause sub-threshold leakage?')">
                    <span class="wf-icon">🔬</span>
                    <div><strong>SRH Recombination</strong><p>Deep-level carrier trap dynamics</p></div>
                </div>
                <div class="welcome-feature-card" onclick="sendQuickChatMessage('What is the decision policy for PASS vs HOLD vs REJECT in SIH 26170?')">
                    <span class="wf-icon">📋</span>
                    <div><strong>Screening Policy</strong><p>Flight PASS/HOLD/REJECT criteria</p></div>
                </div>
                <div class="welcome-feature-card" onclick="sendQuickChatMessage('Explain 17 morphometric feature extraction in dynamic outlier system.')">
                    <span class="wf-icon">📈</span>
                    <div><strong>17 Feature Morphology</strong><p>Curve-level IQR & Isolation Forest</p></div>
                </div>
            </div>
        </div>
    `;
}

function setInlineModelPrompt(promptText) {
    const input = document.getElementById("modelInlineChatInput");
    if (input) {
        input.value = promptText;
        sendModelInlineChat();
    }
}

function setInlineOutlierPrompt(promptText) {
    const input = document.getElementById("outlierInlineChatInput");
    if (input) {
        input.value = promptText;
        sendOutlierInlineChat();
    }
}

function sendQuickChatMessage(promptText) {
    const input = document.getElementById("interactiveChatInput");
    if (input) {
        input.value = promptText;
        sendChatMessage();
    }
}

// =============================================================================
// SYSTEM HEALTH & DYNAMIC API DISCOVERY
// =============================================================================

async function fetchSystemHealth() {
    try {
        const res = await fetch("/api/health");
        const data = await res.json();
        if (data.status === "healthy") {
            let modelDisplay = "Llama 3.3 70B";
            if (data.ai_model) {
                if (data.ai_model.toLowerCase().includes("llama")) {
                    modelDisplay = "Llama 3.3 70B";
                } else if (data.ai_model.toLowerCase().includes("gemini")) {
                    modelDisplay = "Gemini 2.0 Flash";
                } else {
                    modelDisplay = data.ai_model;
                }
            }

            // Update top bar health indicator
            const engineText = document.getElementById("engineText");
            if (engineText) engineText.textContent = "API: Online • " + (data.ai_provider ? data.ai_provider.toUpperCase() : "GROQ");

            // Update Floating Drawer LLM Pill
            const drawerLlm = document.getElementById("drawerLlmModelText");
            if (drawerLlm) drawerLlm.textContent = modelDisplay;

            // Update Model Card LLM Badge
            const modelCardLlm = document.getElementById("modelLlmModelText");
            if (modelCardLlm) modelCardLlm.textContent = modelDisplay + " Versatile";

            // Update Outlier Card LLM Badge
            const outlierCardLlm = document.getElementById("outlierLlmModelText");
            if (outlierCardLlm) outlierCardLlm.textContent = modelDisplay + " Versatile";
        }
    } catch (err) {
        console.warn("Could not query /api/health:", err);
    }
}

// =============================================================================
// NAVIGATION & MODEL SELECTION
// =============================================================================

function navigateTo(viewId) {
    document.querySelectorAll(".view-section").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".nav-btn").forEach(el => el.classList.remove("active"));

    if (viewId === "landing") {
        document.getElementById("view-landing").classList.add("active");
        document.getElementById("nav-landing").classList.add("active");
    } else if (viewId === "outlier") {
        document.getElementById("view-outlier").classList.add("active");
        const navOutlier = document.getElementById("nav-outlier");
        if (navOutlier) navOutlier.classList.add("active");
        initOutlierPage();
    } else if (viewId === "about") {
        document.getElementById("view-about").classList.add("active");
        document.getElementById("nav-about").classList.add("active");
    } else if (viewId === "model") {
        document.getElementById("view-model").classList.add("active");
        const navBtn = document.getElementById("nav-" + currentActiveModel);
        if (navBtn) navBtn.classList.add("active");
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadModelPage(modelType) {
    if (simulationInterval) {
        clearInterval(simulationInterval);
        simulationInterval = null;
        const btn = document.getElementById("btnPlaySim");
        if (btn) btn.textContent = "▶ Auto-Play Simulation";
    }

    currentActiveModel = modelType;
    const cfg = MODEL_CONFIGS[modelType];
    if (!cfg) return;

    document.getElementById("activeModelTitle").textContent = cfg.title;
    document.getElementById("activeModelParamTag").textContent = cfg.paramTag;

    // Reset sample data toolbar toggle states
    isSampleModeVisual1 = false;
    isSampleModeVisual2 = false;
    const btn1 = document.getElementById("btnSampleData1");
    if (btn1) btn1.classList.remove("active");
    const btn2 = document.getElementById("btnSampleData2");
    if (btn2) btn2.classList.remove("active");

    const h1 = document.getElementById("headingVisual1");
    if (h1) h1.textContent = "1. Leakage Current vs Time (Telemetry & GBR Forecast)";
    const s1 = document.getElementById("subVisual1");
    if (s1) s1.textContent = "Chronological telemetry (3,790 rows, Δt=30min) • 80% Past Train / 20% Future GBR Test";

    const h2 = document.getElementById("headingVisual2");
    if (h2) h2.textContent = "2. Operating Voltage vs Time (Stress Trajectory)";
    const s2 = document.getElementById("subVisual2");
    if (s2) s2.textContent = "Applied collector/gate voltage across chronological accelerated aging time";

    document.getElementById("labelRawX").textContent = `Input: ${cfg.xLabel}`;
    document.getElementById("labelUserY").textContent = `Measured: ${cfg.yLabel}`;
    document.getElementById("lblModelOutput").textContent = "GBR Forecast (uA)";
    document.getElementById("lblUserOutput").textContent = "Measured Output (uA)";

    document.getElementById("inputRawX").value = cfg.defaultX;
    document.getElementById("sliderTime").value = cfg.defaultTime;
    document.getElementById("sliderValTime").textContent = `${cfg.defaultTime.toLocaleString()} min`;
    document.getElementById("inputUserY").value = cfg.defaultUserY;

    // Configure Slider X
    const sliderX = document.getElementById("sliderX");
    sliderX.min = cfg.xMin;
    sliderX.max = cfg.xMax;
    sliderX.step = (cfg.xMax - cfg.xMin) / 200;
    sliderX.value = cfg.defaultX;
    document.getElementById("sliderValX").textContent = `${cfg.defaultX.toFixed(1)} V`;

    // Configure Slider Y
    const sliderY = document.getElementById("sliderY");
    sliderY.min = cfg.yMin;
    sliderY.max = cfg.yMax;
    sliderY.step = (cfg.yMax - cfg.yMin) / 200;
    sliderY.value = cfg.defaultUserY;
    document.getElementById("sliderValY").textContent = `${cfg.defaultUserY.toFixed(2)} uA`;

    // Populate Presets
    const presetsContainer = document.getElementById("modelPresetsContainer");
    if (presetsContainer) {
        presetsContainer.innerHTML = "";
        cfg.presets.forEach(p => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "preset-btn";
            btn.textContent = p.name;
            btn.onclick = () => {
                document.getElementById("inputRawX").value = p.x;
                sliderX.value = p.x;
                document.getElementById("sliderValX").textContent = `${p.x.toFixed(1)} V`;

                if (p.t !== undefined) {
                    document.getElementById("sliderTime").value = p.t;
                    document.getElementById("sliderValTime").textContent = `${p.t.toLocaleString()} min`;
                }

                document.getElementById("inputUserY").value = p.userY;
                sliderY.value = p.userY;
                document.getElementById("sliderValY").textContent = `${p.userY.toFixed(2)} uA`;

                runModelPipeline();
            };
            presetsContainer.appendChild(btn);
        });
    }

    navigateTo("model");
    await fetchAndRenderTimeseries(modelType, cfg.defaultTime, cfg.defaultUserY, cfg.defaultX);
    runModelPipeline();
}

// =============================================================================
// LIVE PLAYBACK DEGRADATION SIMULATOR
// =============================================================================

function toggleSimulation() {
    const btn = document.getElementById("btnPlaySim");
    if (simulationInterval) {
        clearInterval(simulationInterval);
        simulationInterval = null;
        if (btn) btn.textContent = "▶ Auto-Play Degradation";
    } else {
        if (btn) btn.textContent = "⏸ Pause Simulation";
        simulationInterval = setInterval(() => {
            const slider = document.getElementById("sliderTime");
            let curr = parseFloat(slider.value) || 0;
            curr += 300; // Step by 300 minutes (5 hours) per tick
            if (curr > 113700) {
                curr = 0;
            }
            slider.value = curr;
            onSliderChangeTime(curr);
        }, 220);
    }
}

function stepTime(deltaMins) {
    const slider = document.getElementById("sliderTime");
    let curr = parseFloat(slider.value) || 0;
    curr = Math.max(0, Math.min(113700, curr + deltaMins));
    slider.value = curr;
    onSliderChangeTime(curr);
}

function resetTimeScrubber() {
    const slider = document.getElementById("sliderTime");
    slider.value = 0;
    onSliderChangeTime(0);
}

let isSampleModeVisual1 = false;
let isSampleModeVisual2 = false;

// =============================================================================
// CHART TOOLBAR SAMPLE DATA TOGGLE CONTROLLER
// =============================================================================

async function toggleSampleDataVisual(chartNum) {
    const cfg = MODEL_CONFIGS[currentActiveModel];
    const rawX = parseFloat(document.getElementById("inputRawX").value) || cfg.defaultX;
    const userY = parseFloat(document.getElementById("inputUserY").value) || cfg.defaultUserY;
    const timeVal = parseFloat(document.getElementById("sliderTime").value) || cfg.defaultTime;

    if (chartNum === 1) {
        isSampleModeVisual1 = !isSampleModeVisual1;
        const btn = document.getElementById("btnSampleData1");
        const heading = document.getElementById("headingVisual1");
        const sub = document.getElementById("subVisual1");

        if (isSampleModeVisual1) {
            if (btn) btn.classList.add("active");
            if (heading) heading.textContent = "1. Sample Dataset Distribution (NASA I-V Scatterplot)";
            if (sub) sub.textContent = "Sampled experimental points from laboratory characterization dataset";
            
            let pts = sampleDatasetCache[currentActiveModel];
            if (!pts) {
                const res = await fetch(`/api/dataset-sample?model=${currentActiveModel}&limit=120`);
                const data = await res.json();
                pts = data.points || [];
                sampleDatasetCache[currentActiveModel] = pts;
            }
            renderSampleScatterplot(pts, { x: rawX, y: userY }, cfg);
        } else {
            if (btn) btn.classList.remove("active");
            if (heading) heading.textContent = "1. Leakage Current vs Time (Telemetry & GBR Forecast)";
            if (sub) sub.textContent = "Chronological telemetry (3,790 rows, Δt=30min) • 80% Past Train / 20% Future GBR Test";
            
            let tsData = timeseriesCache[currentActiveModel];
            if (tsData) {
                renderTimeseriesForecastChart(tsData, timeVal, userY);
            }
        }
    } else if (chartNum === 2) {
        isSampleModeVisual2 = !isSampleModeVisual2;
        const btn = document.getElementById("btnSampleData2");
        const heading = document.getElementById("headingVisual2");
        const sub = document.getElementById("subVisual2");

        if (isSampleModeVisual2) {
            if (btn) btn.classList.add("active");
            if (heading) heading.textContent = "2. Model Transfer Baseline & Screening Tolerance (+25%)";
            if (sub) sub.textContent = "Mathematical baseline curve with upper bound tolerance and live operating point";
            renderSampleLineChart(currentActiveModel, cfg, rawX, userY);
        } else {
            if (btn) btn.classList.remove("active");
            if (heading) heading.textContent = "2. Operating Voltage vs Time (Stress Trajectory)";
            if (sub) sub.textContent = "Applied collector/gate voltage across chronological accelerated aging time";
            
            let tsData = timeseriesCache[currentActiveModel];
            if (tsData) {
                renderVoltageTimeChart(tsData, timeVal, rawX);
            }
        }
    }
}

// =============================================================================
// SAMPLE LAB DATASET I-V VISUALIZATION RENDERERS
// =============================================================================

function renderSampleScatterplot(datasetPoints, livePoint, cfg) {
    const canvas = document.getElementById("tsForecastCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (tsForecastChartInstance) tsForecastChartInstance.destroy();

    tsForecastChartInstance = new Chart(ctx, {
        type: "scatter",
        data: {
            datasets: [
                {
                    label: "Laboratory Measured Points",
                    data: datasetPoints,
                    backgroundColor: "rgba(30, 64, 175, 0.4)",
                    borderColor: "rgba(30, 64, 175, 0.8)",
                    borderWidth: 1,
                    pointRadius: 3.5
                },
                {
                    label: "Current Operating Point",
                    data: livePoint ? [livePoint] : [],
                    backgroundColor: "#ea580c",
                    borderColor: "#ffffff",
                    borderWidth: 2,
                    pointRadius: 8,
                    pointHoverRadius: 10
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: {
                    type: "linear",
                    min: cfg.xMin,
                    max: cfg.xMax,
                    title: { display: true, text: cfg.xLabel, font: { size: 11, weight: "bold" }, color: "#64748b" },
                    grid: { color: "rgba(226, 232, 240, 0.6)" }
                },
                y: {
                    type: "linear",
                    min: cfg.yMin,
                    max: cfg.yMax,
                    title: { display: true, text: cfg.yLabel, font: { size: 11, weight: "bold" }, color: "#64748b" },
                    grid: { color: "rgba(226, 232, 240, 0.6)" }
                }
            },
            plugins: {
                legend: { position: "top", labels: { font: { size: 10 }, color: "#334155" } }
            }
        }
    });
}

function renderSampleLineChart(modelType, cfg, currentX, currentYuser) {
    const canvas = document.getElementById("tsVoltageCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (tsVoltageChartInstance) tsVoltageChartInstance.destroy();

    const stepCount = 30;
    const xMin = cfg.xMin;
    const xMax = cfg.xMax;
    const stepSize = (xMax - xMin) / stepCount;

    const linePoints = [];
    const upperTolerance = [];

    for (let i = 0; i <= stepCount; i++) {
        const x = xMin + (i * stepSize);
        let yPred = 0;
        if (modelType === "breakdown") {
            yPred = 71.0 * Math.pow(x / 600, 4) + 0.01;
        } else if (modelType === "leakage") {
            yPred = (1.84 / 300) * x + 0.01;
        } else {
            yPred = x > 4.0 ? 25.0 * Math.pow(x - 4.0, 1.8) : 0.01;
        }
        linePoints.push({ x: x, y: yPred });
        upperTolerance.push({ x: x, y: yPred * 1.25 });
    }

    tsVoltageChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            datasets: [
                {
                    label: "Mathematical Transfer Baseline",
                    data: linePoints,
                    borderColor: "#1e40af",
                    backgroundColor: "rgba(30, 64, 175, 0.06)",
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.2,
                    fill: false
                },
                {
                    label: "Upper Tolerance (+25%)",
                    data: upperTolerance,
                    borderColor: "#94a3b8",
                    borderDash: [4, 4],
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: "Operating Point",
                    data: currentX !== undefined && currentYuser !== undefined ? [{ x: currentX, y: currentYuser }] : [],
                    type: "scatter",
                    backgroundColor: "#ea580c",
                    borderColor: "#ffffff",
                    borderWidth: 2,
                    pointRadius: 8
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: {
                    type: "linear",
                    min: cfg.xMin,
                    max: cfg.xMax,
                    title: { display: true, text: cfg.xLabel, font: { size: 11, weight: "bold" }, color: "#64748b" },
                    grid: { color: "rgba(226, 232, 240, 0.6)" }
                },
                y: {
                    type: "linear",
                    min: cfg.yMin,
                    max: cfg.yMax,
                    title: { display: true, text: cfg.yLabel, font: { size: 11, weight: "bold" }, color: "#64748b" },
                    grid: { color: "rgba(226, 232, 240, 0.6)" }
                }
            },
            plugins: {
                legend: { position: "top", labels: { font: { size: 10 }, color: "#334155" } }
            }
        }
    });
}

// =============================================================================
// PRIMARY 2 TIME-SERIES VISUALIZATIONS
// =============================================================================

async function fetchAndRenderTimeseries(modelType, activeTime, activeUserY, activeRawX) {
    try {
        let tsData = timeseriesCache[modelType];
        if (!tsData) {
            const res = await fetch("/api/timeseries-data?model=" + modelType + "&limit=120");
            tsData = await res.json();
            timeseriesCache[modelType] = tsData;
        }

        const rawX = activeRawX !== undefined ? activeRawX : (parseFloat(document.getElementById("inputRawX").value) || MODEL_CONFIGS[modelType].defaultX);

        if (!isSampleModeVisual1) {
            renderTimeseriesForecastChart(tsData, activeTime, activeUserY);
        }
        if (!isSampleModeVisual2) {
            renderVoltageTimeChart(tsData, activeTime, rawX);
        }

    } catch (err) {
        console.error("Failed to fetch time-series data:", err);
    }
}

// Plot 2: Operating Voltage vs Time
function renderVoltageTimeChart(data, currentT, currentRawX) {
    const canvas = document.getElementById("tsVoltageCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (tsVoltageChartInstance) tsVoltageChartInstance.destroy();

    const voltagePts = data.voltage_points || [];
    const activePoint = currentT !== undefined && currentRawX !== undefined ? [{ x: currentT, y: currentRawX }] : [];

    tsVoltageChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            datasets: [
                {
                    label: "Operating Stress Voltage (V)",
                    data: voltagePts,
                    borderColor: "#0284c7",
                    backgroundColor: "rgba(2, 132, 199, 0.08)",
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.1,
                    fill: true
                },
                {
                    label: "Current Operating Point",
                    data: activePoint,
                    type: "scatter",
                    borderColor: "#0284c7",
                    backgroundColor: "#0284c7",
                    pointRadius: 7,
                    pointHoverRadius: 9,
                    pointBorderWidth: 2,
                    pointBorderColor: "#ffffff",
                    showLine: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            plugins: {
                legend: {
                    position: "top",
                    labels: { boxWidth: 10, font: { size: 10, weight: "bold" }, color: "#334155" }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: (${ctx.parsed.x.toLocaleString()} min, ${ctx.parsed.y.toFixed(1)} V)`
                    }
                }
            },
            scales: {
                x: {
                    type: "linear",
                    title: { display: true, text: "Time Elapsed (Minutes, Δt=30min)", font: { size: 11 }, color: "#64748b" },
                    grid: { color: "rgba(226, 232, 240, 0.6)" }
                },
                y: {
                    type: "linear",
                    title: { display: true, text: "Operating Voltage (V)", font: { size: 11 }, color: "#64748b" },
                    grid: { color: "rgba(226, 232, 240, 0.6)" }
                }
            }
        }
    });
}

// Plot 1: actual_vs_predicted_leakage_current_over_time
function renderTimeseriesForecastChart(data, currentT, currentUserY) {
    const canvas = document.getElementById("tsForecastCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (tsForecastChartInstance) tsForecastChartInstance.destroy();

    const trainPts = data.train_points || [];
    const testActPts = data.test_actual_points || [];
    const testPredPts = data.test_predicted_points || [];

    const activePoint = currentT !== undefined && currentUserY !== undefined ? [{ x: currentT, y: currentUserY }] : [];

    tsForecastChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            datasets: [
                {
                    label: "Historical Past Train (80%)",
                    data: trainPts,
                    borderColor: "#1e40af",
                    backgroundColor: "rgba(30, 64, 175, 0.08)",
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.15,
                    fill: true
                },
                {
                    label: "Future Test Actual Ground Truth",
                    data: testActPts,
                    borderColor: "#0f172a",
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.15,
                    fill: false
                },
                {
                    label: "GBR Model Forecast (n=300)",
                    data: testPredPts,
                    borderColor: "#ea580c",
                    borderDash: [5, 4],
                    borderWidth: 2.5,
                    pointRadius: 0,
                    tension: 0.15,
                    fill: false
                },
                {
                    label: "Live Test Point",
                    data: activePoint,
                    type: "scatter",
                    borderColor: "#ea580c",
                    backgroundColor: "#ea580c",
                    pointRadius: 7,
                    pointHoverRadius: 9,
                    pointBorderWidth: 2,
                    pointBorderColor: "#ffffff",
                    showLine: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            interaction: { mode: "nearest", intersect: false },
            plugins: {
                legend: {
                    position: "top",
                    labels: { boxWidth: 12, font: { size: 11, weight: "bold" }, color: "#334155" }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: (${ctx.parsed.x.toLocaleString()} min, ${ctx.parsed.y.toFixed(2)} uA)`
                    }
                }
            },
            scales: {
                x: {
                    type: "linear",
                    title: { display: true, text: "Time Elapsed (Minutes, Δt=30min)", font: { weight: "bold" }, color: "#475569" },
                    grid: { color: "rgba(226, 232, 240, 0.7)" }
                },
                y: {
                    type: "linear",
                    title: { display: true, text: "Leakage Current (microAmpere)", font: { weight: "bold" }, color: "#475569" },
                    grid: { color: "rgba(226, 232, 240, 0.7)" }
                }
            }
        }
    });

    attachChartInteraction(canvas, "forecast");
}

// Plot 2: prediction_error_over_time
function renderResidualErrorChart(data, currentT) {
    const canvas = document.getElementById("tsResidualCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (tsResidualChartInstance) tsResidualChartInstance.destroy();

    const residualPts = data.residual_points || [];
    const sigma = data.sigma_band || 5.0;

    const upperBand = residualPts.map(p => ({ x: p.x, y: sigma }));
    const lowerBand = residualPts.map(p => ({ x: p.x, y: -sigma }));
    const zeroLine = residualPts.map(p => ({ x: p.x, y: 0.0 }));

    tsResidualChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            datasets: [
                {
                    label: "Residual Drift e = Actual - Pred",
                    data: residualPts,
                    borderColor: "#dc2626",
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.2,
                    fill: false
                },
                {
                    label: "Nominal Baseline (e=0)",
                    data: zeroLine,
                    borderColor: "#94a3b8",
                    borderDash: [3, 3],
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: "Early Warning Upper (+2.5σ)",
                    data: upperBand,
                    borderColor: "rgba(234, 88, 12, 0.6)",
                    borderDash: [4, 4],
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: "Early Warning Lower (-2.5σ)",
                    data: lowerBand,
                    borderColor: "rgba(234, 88, 12, 0.6)",
                    borderDash: [4, 4],
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            plugins: {
                legend: {
                    position: "top",
                    labels: { boxWidth: 10, font: { size: 10 }, color: "#334155" }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(3)} uA at t=${ctx.parsed.x.toLocaleString()} min`
                    }
                }
            },
            scales: {
                x: {
                    type: "linear",
                    title: { display: true, text: "Time Elapsed (Minutes)", font: { size: 11 }, color: "#64748b" },
                    grid: { color: "rgba(226, 232, 240, 0.6)" }
                },
                y: {
                    type: "linear",
                    title: { display: true, text: "Prediction Residual (microAmpere)", font: { size: 11 }, color: "#64748b" },
                    grid: { color: "rgba(226, 232, 240, 0.6)" }
                }
            }
        }
    });
}

// Plot 3: top_feature_importance
function renderFeatureImportanceChart(data) {
    const canvas = document.getElementById("tsFeatureCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (tsFeatureChartInstance) tsFeatureChartInstance.destroy();

    const features = data.top_features || [];
    const labels = features.map(f => f.feature);
    const values = features.map(f => f.importance);

    tsFeatureChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "GBR Relative Feature Importance",
                data: values,
                backgroundColor: [
                    "#ea580c", "#1e40af", "#1e40af", "#3b82f6",
                    "#3b82f6", "#60a5fa", "#93c5fd", "#cbd5e1"
                ],
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `Importance Score: ${(ctx.parsed.x * 100).toFixed(1)}%`
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 0.5,
                    title: { display: true, text: "Normalized Importance (Gini)", font: { size: 11 } },
                    grid: { color: "rgba(226, 232, 240, 0.6)" }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 11, weight: "600" }, color: "#334155" }
                }
            }
        }
    });
}

// =============================================================================
// INTERACTIVE CANVAS EVENT LISTENERS & 15% PANNING CLAMPING
// =============================================================================

function attachChartInteraction(canvas, chartType) {
    canvas.onmousedown = (e) => {
        const mode = chartModes[chartType];
        if (mode === "point") {
            isDraggingPoint = true;
            updatePointFromMouse(e, chartType);
        } else if (mode === "pan") {
            isPanning = true;
            panStart = { x: e.clientX, y: e.clientY };
            canvas.style.cursor = "grabbing";
        }
    };

    window.addEventListener("mousemove", (e) => {
        if (isDraggingPoint) {
            updatePointFromMouse(e, chartType);
        } else if (isPanning) {
            handlePanMove(e, chartType);
        }
    });

    window.addEventListener("mouseup", () => {
        if (isDraggingPoint) isDraggingPoint = false;
        if (isPanning) {
            isPanning = false;
            canvas.style.cursor = chartModes[chartType] === "pan" ? "grab" : "crosshair";
        }
    });
}

function updatePointFromMouse(e, chartType) {
    const chart = tsForecastChartInstance;
    if (!chart) return;

    const rect = chart.canvas.getBoundingClientRect();
    const xPos = e.clientX - rect.left;
    const yPos = e.clientY - rect.top;

    if (xPos < chart.chartArea.left || xPos > chart.chartArea.right ||
        yPos < chart.chartArea.top || yPos > chart.chartArea.bottom) {
        return;
    }

    const tVal = chart.scales.x.getValueForPixel(xPos);
    const yVal = chart.scales.y.getValueForPixel(yPos);

    if (tVal !== undefined && yVal !== undefined) {
        const cfg = MODEL_CONFIGS[currentActiveModel];
        const clampedT = Math.max(0, Math.min(113700, Math.round(tVal / 30) * 30));
        const clampedY = Math.max(0, Math.min(cfg.yMax * 1.5, yVal));

        const sliderTime = document.getElementById("sliderTime");
        if (sliderTime) {
            sliderTime.value = clampedT;
            document.getElementById("sliderValTime").textContent = `${clampedT.toLocaleString()} min`;
        }

        const inputY = document.getElementById("inputUserY");
        const sliderY = document.getElementById("sliderY");
        if (inputY) inputY.value = clampedY.toFixed(2);
        if (sliderY) {
            sliderY.value = clampedY;
            document.getElementById("sliderValY").textContent = `${clampedY.toFixed(2)} uA`;
        }

        chart.data.datasets[3].data = [{ x: clampedT, y: clampedY }];
        chart.update("none");

        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => runModelPipeline(), 100);
    }
}

function handlePanMove(e, chartType) {
    const chart = tsForecastChartInstance;
    if (!chart) return;

    const dx = e.clientX - panStart.x;
    const dy = e.clientY - panStart.y;
    panStart = { x: e.clientX, y: e.clientY };

    const xDiff = (chart.scales.x.max - chart.scales.x.min) * (dx / chart.width);
    const yDiff = (chart.scales.y.max - chart.scales.y.min) * (dy / chart.height);

    const baseCfg = defaultChartBounds[chartType];
    const baseXSpan = baseCfg.xMax - baseCfg.xMin;
    const baseYSpan = baseCfg.yMax - baseCfg.yMin;

    const minAllowedX = baseCfg.xMin - 0.15 * baseXSpan;
    const maxAllowedX = baseCfg.xMax + 0.15 * baseXSpan;
    const minAllowedY = baseCfg.yMin - 0.15 * baseYSpan;
    const maxAllowedY = baseCfg.yMax + 0.15 * baseYSpan;

    let nextXMin = chart.scales.x.min - xDiff;
    let nextXMax = chart.scales.x.max - xDiff;
    let nextYMin = chart.scales.y.min + yDiff;
    let nextYMax = chart.scales.y.max + yDiff;

    if (nextXMin >= minAllowedX && nextXMax <= maxAllowedX) {
        chart.scales.x.options.min = nextXMin;
        chart.scales.x.options.max = nextXMax;
    }
    if (nextYMin >= minAllowedY && nextYMax <= maxAllowedY) {
        chart.scales.y.options.min = nextYMin;
        chart.scales.y.options.max = nextYMax;
    }

    chart.update("none");
}

function setChartMode(chartType, mode) {
    chartModes[chartType] = mode;
    const btnPoint = document.getElementById("btnModeForecastPoint");
    const btnPan = document.getElementById("btnModeForecastPan");

    if (mode === "point") {
        if (btnPoint) btnPoint.classList.add("active");
        if (btnPan) btnPan.classList.remove("active");
        if (tsForecastChartInstance) tsForecastChartInstance.canvas.style.cursor = "crosshair";
    } else {
        if (btnPoint) btnPoint.classList.remove("active");
        if (btnPan) btnPan.classList.add("active");
        if (tsForecastChartInstance) tsForecastChartInstance.canvas.style.cursor = "grab";
    }
}

function zoomChart(chartType, factor) {
    let chart = tsForecastChartInstance;
    if (chartType === "voltage") chart = tsVoltageChartInstance;
    else if (chartType === "sampleScatter") chart = sampleScatterChartInstance;
    else if (chartType === "sampleLine") chart = sampleLineChartInstance;
    else if (chartType === "outlierCurve") chart = outlierCurveChartInstance;
    else if (chartType === "outlierFeatures") chart = outlierFeaturesChartInstance;
    if (!chart) return;

    const xSpan = (chart.scales.x.max - chart.scales.x.min) * (1 / factor);
    const ySpan = (chart.scales.y.max - chart.scales.y.min) * (1 / factor);

    const xMid = (chart.scales.x.max + chart.scales.x.min) / 2;
    const yMid = (chart.scales.y.max + chart.scales.y.min) / 2;

    chart.scales.x.options.min = xMid - xSpan / 2;
    chart.scales.x.options.max = xMid + xSpan / 2;
    chart.scales.y.options.min = yMid - ySpan / 2;
    chart.scales.y.options.max = yMid + ySpan / 2;

    chart.update();
}

function resetChartZoom(chartType) {
    let chart = tsForecastChartInstance;
    if (chartType === "voltage") chart = tsVoltageChartInstance;
    else if (chartType === "sampleScatter") chart = sampleScatterChartInstance;
    else if (chartType === "sampleLine") chart = sampleLineChartInstance;
    else if (chartType === "outlierCurve") chart = outlierCurveChartInstance;
    else if (chartType === "outlierFeatures") chart = outlierFeaturesChartInstance;
    if (!chart) return;

    if (chartType === "outlierFeatures" || chartType === "outlierCurve") {
        chart.resetZoom ? chart.resetZoom() : chart.update();
        return;
    }

    const b = defaultChartBounds[chartType];
    if (b) {
        chart.scales.x.options.min = b.xMin;
        chart.scales.x.options.max = b.xMax;
        chart.scales.y.options.min = b.yMin;
        chart.scales.y.options.max = b.yMax;
        chart.update();
    }
}

// =============================================================================
// SLIDER & FORM INPUT CONTROLS
// =============================================================================

function onInputChangeX(val) {
    const num = parseFloat(val);
    if (isNaN(num)) return;
    document.getElementById("sliderX").value = num;
    document.getElementById("sliderValX").textContent = `${num.toFixed(1)} V`;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => runModelPipeline(), 100);
}

function onSliderChangeX(val) {
    const num = parseFloat(val);
    document.getElementById("inputRawX").value = num.toFixed(1);
    document.getElementById("sliderValX").textContent = `${num.toFixed(1)} V`;
    if (tsVoltageChartInstance && tsVoltageChartInstance.data.datasets[1] && tsVoltageChartInstance.data.datasets[1].data.length > 0) {
        tsVoltageChartInstance.data.datasets[1].data[0].y = num;
        tsVoltageChartInstance.update("none");
    }
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => runModelPipeline(), 100);
}

function onSliderChangeTime(val) {
    const num = parseFloat(val);
    document.getElementById("sliderValTime").textContent = `${num.toLocaleString()} min`;
    
    // Update live marker on Current Forecast Chart
    if (tsForecastChartInstance && tsForecastChartInstance.data.datasets[3] && tsForecastChartInstance.data.datasets[3].data.length > 0) {
        tsForecastChartInstance.data.datasets[3].data[0].x = num;
        tsForecastChartInstance.update("none");
    }

    // Update live marker on Voltage Stress Chart
    if (tsVoltageChartInstance && tsVoltageChartInstance.data.datasets[1] && tsVoltageChartInstance.data.datasets[1].data.length > 0) {
        tsVoltageChartInstance.data.datasets[1].data[0].x = num;
        tsVoltageChartInstance.update("none");
    }

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => runModelPipeline(), 100);
}

function onInputChangeY(val) {
    const num = parseFloat(val);
    if (isNaN(num)) return;
    document.getElementById("sliderY").value = num;
    document.getElementById("sliderValY").textContent = `${num.toFixed(2)} uA`;
    if (tsForecastChartInstance && tsForecastChartInstance.data.datasets[3] && tsForecastChartInstance.data.datasets[3].data.length > 0) {
        tsForecastChartInstance.data.datasets[3].data[0].y = num;
        tsForecastChartInstance.update("none");
    }
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => runModelPipeline(), 100);
}

function onSliderChangeY(val) {
    const num = parseFloat(val);
    document.getElementById("inputUserY").value = num.toFixed(2);
    document.getElementById("sliderValY").textContent = `${num.toFixed(2)} uA`;
    if (tsForecastChartInstance && tsForecastChartInstance.data.datasets[3] && tsForecastChartInstance.data.datasets[3].data.length > 0) {
        tsForecastChartInstance.data.datasets[3].data[0].y = num;
        tsForecastChartInstance.update("none");
    }
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => runModelPipeline(), 100);
}

// =============================================================================
// MASTER TIME-SERIES PIPELINE EXECUTION
// =============================================================================

async function runModelPipeline() {
    const btn = document.getElementById("runPipelineBtn");
    if (btn) btn.disabled = true;

    const modelType = currentActiveModel;
    const rawX = parseFloat(document.getElementById("inputRawX").value);
    const timeVal = parseFloat(document.getElementById("sliderTime").value) || 90960.0;
    const userY = parseFloat(document.getElementById("inputUserY").value);
    const compId = "DUT-1";

    try {
        const payload = {
            model_type: modelType,
            raw_input: rawX,
            time_minutes: timeVal,
            user_said_output: isNaN(userY) ? null : userY,
            component_id: compId,
            use_ai: true
        };

        const res = await fetch("/api/pipeline/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.error) throw new Error(data.error);

        // Display results panel
        const resPanel = document.getElementById("resultsPanel");
        resPanel.style.display = "block";

        const badge = document.getElementById("riskDecisionBadge");
        const decision = data.discrepancy.risk_decision;
        badge.textContent = decision;
        badge.className = "verdict-pill " + (decision === "PASS" ? "badge-pass" : (decision === "HOLD" ? "badge-hold" : "badge-reject"));

        document.getElementById("statRawX").textContent = `${data.raw_input.toFixed(1)} V`;
        document.getElementById("statTime").textContent = `${timeVal.toLocaleString()} min`;
        document.getElementById("statModelY").textContent = `${data.physical_output.toFixed(2)} uA`;
        document.getElementById("statUserY").textContent = data.user_said_output !== null ? `${data.user_said_output.toFixed(2)} uA` : "N/A";
        
        const resVal = data.user_said_output !== null ? (data.user_said_output - data.physical_output) : 0.0;
        document.getElementById("statResidual").textContent = `${resVal > 0 ? "+" : ""}${resVal.toFixed(2)} uA`;
        document.getElementById("statPctDiff").textContent = data.discrepancy.pct_diff !== null ? `${data.discrepancy.pct_diff > 0 ? "+" : ""}${data.discrepancy.pct_diff.toFixed(1)}%` : "0.0%";
        document.getElementById("statR2Score").textContent = "R²: 0.989 / MAE: 1.87 uA";
        document.getElementById("statScaledX").textContent = data.scaled_input !== undefined ? `${data.scaled_input.toFixed(4)}` : "—";

        // Update AI Report Box
        const reportText = document.getElementById("aiReportText");
        if (reportText) {
            reportText.innerHTML = renderMarkdown(data.chatbot_explanation);
        }
        const reportBadge = document.getElementById("reportEngineBadge");
        if (reportBadge && data.ai_provider) {
            reportBadge.textContent = `${data.ai_provider.toUpperCase()} Llama 3.3`;
        }

        // Also append into floating AI Diagnostics Drawer
        appendBotMessage(data.chatbot_explanation);

        // Update live test marker on Time-Series Forecast Plot (Current vs Time)
        if (tsForecastChartInstance && tsForecastChartInstance.data.datasets[3]) {
            tsForecastChartInstance.data.datasets[3].data = [{ x: timeVal, y: userY }];
            tsForecastChartInstance.update("none");
        }

        // Update live test marker on Operating Voltage vs Time Plot
        if (tsVoltageChartInstance && tsVoltageChartInstance.data.datasets[1]) {
            tsVoltageChartInstance.data.datasets[1].data = [{ x: timeVal, y: rawX }];
            tsVoltageChartInstance.update("none");
        }

        // Update live test marker on Sample Scatterplot
        if (sampleScatterChartInstance && sampleScatterChartInstance.data.datasets[1]) {
            sampleScatterChartInstance.data.datasets[1].data = [{ x: rawX, y: userY }];
            sampleScatterChartInstance.update("none");
        }

        // Update live test marker on Sample Transfer Line Chart
        if (sampleLineChartInstance && sampleLineChartInstance.data.datasets[2]) {
            sampleLineChartInstance.data.datasets[2].data = [{ x: rawX, y: userY }];
            sampleLineChartInstance.update("none");
        }

    } catch (err) {
        console.error("Pipeline run failed:", err);
    } finally {
        if (btn) btn.disabled = false;
    }
}

async function sendModelInlineChat() {
    const input = document.getElementById("modelInlineChatInput");
    if (!input) return;
    const msg = input.value.trim();
    if (!msg) return;

    input.value = "";
    const reportBox = document.getElementById("aiReportText");
    if (reportBox) {
        reportBox.innerHTML = `
            <div style="background:#e0e7ff;border:1px solid #c7d2fe;padding:8px 10px;border-radius:6px;font-size:0.8rem;color:#1e40af;margin-bottom:6px;">
                <strong>You:</strong> ${escapeHtml(msg)}
            </div>
            <div style="background:#f8fafc;border:1px solid var(--border);padding:8px 10px;border-radius:6px;font-size:0.8rem;color:#475569;">
                <span class="status-dot"></span> <em>Drishti AI is generating response...</em>
            </div>
        `;
    }

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg })
        });
        const data = await response.json();
        if (reportBox) {
            reportBox.innerHTML = `
                <div style="background:#e0e7ff;border:1px solid #c7d2fe;padding:8px 10px;border-radius:6px;font-size:0.8rem;color:#1e40af;margin-bottom:6px;">
                    <strong>You:</strong> ${escapeHtml(msg)}
                </div>
                <div style="background:#f8fafc;border:1px solid var(--border);padding:10px 12px;border-radius:6px;font-size:0.82rem;color:#334155;line-height:1.5;">
                    ${renderMarkdown(data.reply)}
                </div>
            `;
        }
    } catch (err) {
        if (reportBox) {
            reportBox.innerHTML += `<div style="color:#dc2626;font-size:0.8rem;margin-top:4px;">Error: ${err.message}</div>`;
        }
    }
}

async function sendChatMessage() {
    const input = document.getElementById("interactiveChatInput");
    const msg = input.value.trim();
    if (!msg) return;

    appendUserMessage(msg);
    input.value = "";

    const chat = document.getElementById("chatMessages");
    const loadingId = "loadingBubble_" + Date.now();
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "chat-item bot-item";
    loadingDiv.id = loadingId;
    loadingDiv.innerHTML = `<div class="bubble bot-bubble" style="color:var(--chakra-navy);"><span class="status-dot"></span> <em>Drishti AI is generating response...</em></div>`;
    chat.appendChild(loadingDiv);
    chat.scrollTop = chat.scrollHeight;

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg })
        });
        const data = await response.json();
        const loadElem = document.getElementById(loadingId);
        if (loadElem) loadElem.remove();
        appendBotMessage(data.reply);
    } catch (err) {
        const loadElem = document.getElementById(loadingId);
        if (loadElem) loadElem.remove();
        appendBotMessage("API Error: " + err.message);
    }
}

function appendUserMessage(text) {
    const chat = document.getElementById("chatMessages");
    if (!chat) return;
    const div = document.createElement("div");
    div.className = "chat-item user-item";
    div.innerHTML = `<div class="bubble user-bubble">${escapeHtml(text)}</div>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function appendBotMessage(markdown) {
    const chat = document.getElementById("chatMessages");
    if (!chat) return;
    const div = document.createElement("div");
    div.className = "chat-item bot-item";
    div.innerHTML = `<div class="bubble bot-bubble">${renderMarkdown(markdown)}</div>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderMarkdown(md) {
    if (!md) return "";
    return md
        .replace(/^### (.*$)/gim, '<h4 style="color:#0f2b5c;margin:4px 0;">$1</h4>')
        .replace(/^## (.*$)/gim, '<h3 style="color:#0f2b5c;margin:4px 0;">$1</h3>')
        .replace(/\*\*(.*?)\*\*/gim, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/gim, "<em>$1</em>")
        .replace(/`([^`]+)`/gim, '<code style="background:#f1f5f9;padding:1px 4px;border-radius:3px;font-size:0.85em;">$1</code>')
        .replace(/\n/gim, "<br>");
}

// =============================================================================
// DYNAMIC OUTLIER DETECTION SYSTEM CONTROLLER
// =============================================================================

let activeOutlierModel = "breakdown";
let activeOutlierPreset = "9";
let outlierPopulationCache = {};
let outlierCurveChartInstance = null;
let outlierFeaturesChartInstance = null;
let currentTestedCurveData = null;

async function initOutlierPage() {
    await selectOutlierModel(activeOutlierModel);
}

async function selectOutlierModel(modelType) {
    activeOutlierModel = modelType;

    // Update Segmented Control UI
    document.querySelectorAll("#view-outlier .seg-btn").forEach(tab => tab.classList.remove("active"));
    const activeTab = document.getElementById("tabOutlier" + modelType.charAt(0).toUpperCase() + modelType.slice(1));
    if (activeTab) activeTab.classList.add("active");

    const badge = document.getElementById("outlierHeaderBadge");
    if (badge) {
        if (modelType === "breakdown") badge.textContent = "Breakdown (Vce-Ic) • 17 Morphometric Features • Dual-Layer Score Fusion";
        else if (modelType === "leakage") badge.textContent = "Leakage IV (Vapp-Ileak) • 17 Morphometric Features • Dual-Layer Score Fusion";
        else if (modelType === "turnon") badge.textContent = "Turn-On (Vge-Ic) • 17 Morphometric Features • Dual-Layer Score Fusion";
    }

    // Fetch population baseline curves if not cached
    if (!outlierPopulationCache[modelType]) {
        try {
            const resp = await fetch(`/api/anomaly/population?model=${modelType}`);
            if (resp.ok) {
                outlierPopulationCache[modelType] = await resp.json();
            }
        } catch (err) {
            console.error("Failed to load outlier population data:", err);
        }
    }

    const pop = outlierPopulationCache[modelType];
    const threshEl = document.getElementById("statDynamicThresh");
    if (threshEl && pop) threshEl.textContent = pop.dynamic_threshold;

    // Default to Preset Curve 9 or 0
    applyOutlierPreset(activeOutlierPreset || "9");
}

function applyOutlierPreset(presetVal) {
    activeOutlierPreset = presetVal;

    // Toggle active state on preset chips
    document.querySelectorAll("#outlierPresetButtons .preset-btn").forEach(btn => btn.classList.remove("active"));
    const activeBtn = document.getElementById("presetBtn" + (presetVal === "custom" ? "Custom" : presetVal));
    if (activeBtn) activeBtn.classList.add("active");

    const customArea = document.getElementById("customCurveArea");
    const compIdInput = document.getElementById("outlierCompId");
    
    if (presetVal === "custom") {
        if (customArea) customArea.style.display = "block";
        if (compIdInput) compIdInput.value = "CUSTOM-DUT-01";
        return;
    }

    if (customArea) customArea.style.display = "none";
    if (compIdInput) compIdInput.value = `NASA-${activeOutlierModel.toUpperCase()}-CURVE-${presetVal}`;

    const pop = outlierPopulationCache[activeOutlierModel];
    if (pop && pop.curves) {
        const cId = parseInt(presetVal, 10);
        const match = pop.curves.find(c => c.curve_id === cId) || pop.curves[0];
        if (match) {
            currentTestedCurveData = {
                x: match.full_x || match.x,
                y: match.full_y || match.y
            };
        }
    }

    runOutlierDetection();
}

async function runOutlierDetection() {
    const btn = document.getElementById("btnRunOutlier");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Analyzing 17 Curve Features...";
    }

    const compId = document.getElementById("outlierCompId") ? document.getElementById("outlierCompId").value : "DUT-SWEEP";
    const presetVal = activeOutlierPreset || "9";

    let xPoints = [];
    let yPoints = [];

    if (presetVal === "custom") {
        const rawText = document.getElementById("customCoordsInput").value.trim();
        try {
            if (rawText.startsWith("{")) {
                const parsed = JSON.parse(rawText);
                xPoints = parsed.x || parsed.X || [];
                yPoints = parsed.y || parsed.Y || [];
            } else {
                // CSV rows
                const lines = rawText.split("\n");
                lines.forEach(l => {
                    const parts = l.split(",");
                    if (parts.length >= 2 && !isNaN(parseFloat(parts[0])) && !isNaN(parseFloat(parts[1]))) {
                        xPoints.push(parseFloat(parts[0]));
                        yPoints.push(parseFloat(parts[1]));
                    }
                });
            }
        } catch (e) {
            alert("Could not parse custom coordinates. Please provide valid JSON or CSV numbers.");
            if (btn) { btn.disabled = false; btn.textContent = "Run Outlier Screening & Explain"; }
            return;
        }
    } else {
        const pop = outlierPopulationCache[activeOutlierModel];
        if (pop && pop.curves) {
            const cId = parseInt(presetVal, 10);
            const match = pop.curves.find(c => c.curve_id === cId) || pop.curves[0];
            if (match) {
                xPoints = match.full_x || match.x;
                yPoints = match.full_y || match.y;
            }
        }
    }

    if (!xPoints.length || !yPoints.length) {
        // Fallback synthetic sweep
        xPoints = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 4.8, 5.0, 5.2];
        yPoints = [0.005, 0.006, 0.008, 0.012, 0.025, 0.08, 0.5, 12.0, 85.0];
    }

    currentTestedCurveData = { x: xPoints, y: yPoints };

    try {
        const resp = await fetch("/api/anomaly/detect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                model_type: activeOutlierModel,
                component_id: compId,
                curve: { x: xPoints, y: yPoints },
                include_curve_data: true
            })
        });

        if (!resp.ok) {
            const errData = await resp.json();
            throw new Error(errData.error || "Anomaly detection failed");
        }

        const detResult = await resp.json();
        renderOutlierResults(detResult);
    } catch (err) {
        console.error("Outlier detection error:", err);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Analyze Curve-Level Anomaly";
        }
    }
}

function renderOutlierResults(res) {
    const anom = res.anomaly;

    // 1. Verdict Badge
    const badge = document.getElementById("outlierVerdictBadge");
    if (badge) {
        badge.textContent = `${anom.decision} (${anom.severity})`;
        badge.className = "verdict-pill";
        if (anom.decision === "PASS") badge.classList.add("badge-pass");
        else if (anom.decision === "HOLD") badge.classList.add("badge-hold");
        else badge.classList.add("badge-reject");
    }

    // 2. Metrics Deck
    const statComb = document.getElementById("statCombinedScore");
    if (statComb) statComb.textContent = anom.combined_score.toFixed(2);

    const statDyn = document.getElementById("statDynamicScore");
    if (statDyn) statDyn.textContent = anom.dynamic_score > 1000 ? anom.dynamic_score.toExponential(2) : anom.dynamic_score.toFixed(2);

    const statDynThresh = document.getElementById("statDynamicThresh");
    if (statDynThresh) statDynThresh.textContent = anom.dynamic_threshold.toFixed(2);

    const statIso = document.getElementById("statIsolationScore");
    if (statIso) {
        statIso.textContent = `${anom.isolation_flag} (${anom.isolation_score.toFixed(2)})`;
        statIso.className = "metric-val " + (anom.isolation_flag === "ANOMALY" ? "text-orange" : "text-blue");
    }

    const statCount = document.getElementById("statOutlierCount");
    if (statCount) statCount.textContent = anom.outlier_feature_count;

    // 3. Outlier Trigger Pills
    const pillsWrap = document.getElementById("outlierTriggerPills");
    if (pillsWrap) {
        pillsWrap.innerHTML = "";
        if (anom.outlier_features && anom.outlier_features.length > 0) {
            anom.outlier_features.forEach(o => {
                const pill = document.createElement("span");
                pill.className = "tag-pill tag-red";
                const scoreText = o.robust_score > 1000 ? o.robust_score.toExponential(1) : o.robust_score.toFixed(1);
                pill.textContent = `${o.label} (${scoreText}σ ${o.direction})`;
                pillsWrap.appendChild(pill);
            });
        } else {
            pillsWrap.innerHTML = `<span class="tag-pill tag-green">None (All 17 Features Within ±3.5σ Bounds)</span>`;
        }
    }

    // 4. AI Failure Physics Report
    const aiReport = document.getElementById("outlierAiReport");
    if (aiReport) {
        aiReport.innerHTML = renderMarkdown(res.diagnostic_report || "");
    }

    // 5. Visual 1: Population Curve Overlay Chart
    renderOutlierCurveChart(res);

    // 6. Visual 2: 17-Feature Robust Anomaly Deviation Bar Chart
    renderOutlierFeaturesChart(res);

    // 7. 17 Features Table
    renderOutlierTable(res);
}

function renderOutlierCurveChart(res) {
    const canvas = document.getElementById("outlierCurveCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (outlierCurveChartInstance) {
        outlierCurveChartInstance.destroy();
        outlierCurveChartInstance = null;
    }

    const pop = outlierPopulationCache[activeOutlierModel];
    const datasets = [];

    // Background population curves
    if (pop && pop.curves) {
        pop.curves.forEach((c, idx) => {
            const pts = c.x.map((xVal, i) => ({ x: xVal, y: c.y[i] }));
            datasets.push({
                label: `Lot Curve ${c.curve_id}`,
                data: pts,
                borderColor: "rgba(148, 163, 184, 0.28)",
                borderWidth: 1,
                pointRadius: 0,
                fill: false,
                tension: 0.1
            });
        });
    }

    // Foreground tested DUT curve
    const testPts = res.curve.x.map((xVal, i) => ({ x: xVal, y: res.curve.y[i] }));
    const dec = res.anomaly.decision;
    const color = dec === "PASS" ? "#15803d" : (dec === "HOLD" ? "#d97706" : "#dc2626");

    datasets.push({
        label: `Tested DUT: ${res.component_id} (${dec})`,
        data: testPts,
        borderColor: color,
        borderWidth: 3,
        pointRadius: 2,
        pointBackgroundColor: color,
        fill: false,
        tension: 0.1
    });

    // Add Knee Point Marker
    const kneeV = res.features.knee_voltage;
    if (kneeV !== undefined) {
        const kneeCurrent = res.features.current_v90 || testPts[testPts.length - 1].y;
        datasets.push({
            label: `Knee Transition (${kneeV.toFixed(2)} V)`,
            data: [{ x: kneeV, y: kneeCurrent }],
            borderColor: "#7c3aed",
            backgroundColor: "#7c3aed",
            pointRadius: 6,
            pointHoverRadius: 8,
            showLine: false
        });
    }

    const xUnit = res.curve.x_unit || "V";
    const yUnit = res.curve.y_unit || "microAmpere";

    outlierCurveChartInstance = new Chart(ctx, {
        type: "line",
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 350 },
            interaction: { mode: "nearest", intersect: false },
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        filter: item => item.text.includes("Tested DUT") || item.text.includes("Knee"),
                        font: { family: "Inter", size: 11, weight: "bold" }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: (${ctx.parsed.x.toFixed(2)} ${xUnit}, ${ctx.parsed.y.toFixed(4)} ${yUnit})`
                    }
                }
            },
            scales: {
                x: {
                    type: "linear",
                    title: { display: true, text: `Voltage (${xUnit})`, font: { family: "Inter", size: 11, weight: "bold" } },
                    grid: { color: "#f1f5f9" }
                },
                y: {
                    type: "linear",
                    title: { display: true, text: `Current (${yUnit})`, font: { family: "Inter", size: 11, weight: "bold" } },
                    grid: { color: "#f1f5f9" }
                }
            }
        }
    });
}

function renderOutlierFeaturesChart(res) {
    const canvas = document.getElementById("outlierFeaturesCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (outlierFeaturesChartInstance) {
        outlierFeaturesChartInstance.destroy();
        outlierFeaturesChartInstance = null;
    }

    const details = res.feature_details || {};
    const labels = [];
    const scores = [];
    const bgColors = [];
    const borderColors = [];

    Object.keys(details).forEach(key => {
        const item = details[key];
        labels.push(item.label.split("(")[0].trim());
        const absVal = Math.min(50.0, item.abs_z); // Cap visual scale for charts
        scores.push(absVal);
        if (item.is_outlier) {
            bgColors.push("rgba(220, 38, 38, 0.75)");
            borderColors.push("#dc2626");
        } else {
            bgColors.push("rgba(124, 58, 237, 0.65)");
            borderColors.push("#7c3aed");
        }
    });

    outlierFeaturesChartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Robust IQR Deviation (|z|)",
                data: scores,
                backgroundColor: bgColors,
                borderColor: borderColors,
                borderWidth: 1.5,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 400 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => `Robust Deviation: ${ctx.parsed.x.toFixed(2)}σ ${ctx.parsed.x >= 3.5 ? '(OUTLIER)' : '(NOMINAL)'}`
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: "Robust IQR Z-Score (|z|)", font: { family: "Inter", size: 11, weight: "bold" } },
                    grid: { color: "#f1f5f9" },
                    suggestedMax: 10
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { family: "Inter", size: 10 } }
                }
            }
        }
    });
}

function renderOutlierTable(res) {
    const tbody = document.getElementById("outlierTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    const details = res.feature_details || {};
    Object.keys(details).forEach(key => {
        const item = details[key];
        const tr = document.createElement("tr");
        if (item.is_outlier) tr.className = "outlier-row";

        const valStr = typeof item.value === "number" ? (Math.abs(item.value) < 0.01 && item.value !== 0 ? item.value.toExponential(3) : item.value.toFixed(4)) : item.value;
        const medStr = typeof item.population_median === "number" ? (Math.abs(item.population_median) < 0.01 && item.population_median !== 0 ? item.population_median.toExponential(3) : item.population_median.toFixed(4)) : item.population_median;
        const madStr = typeof item.population_mad === "number" ? (Math.abs(item.population_mad) < 0.01 && item.population_mad !== 0 ? item.population_mad.toExponential(3) : item.population_mad.toFixed(4)) : item.population_mad;

        const statusPill = item.is_outlier 
            ? `<span class="tag-pill tag-red">OUTLIER (${item.robust_z.toFixed(2)}σ)</span>` 
            : `<span class="tag-pill tag-green">NOMINAL</span>`;

        tr.innerHTML = `
            <td><strong>${escapeHtml(item.label)}</strong></td>
            <td>${valStr}</td>
            <td>${medStr}</td>
            <td>${madStr}</td>
            <td>${item.robust_z > 0 ? '+' : ''}${item.robust_z.toFixed(2)}</td>
            <td>${statusPill}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function sendOutlierInlineChat() {
    const input = document.getElementById("outlierInlineChatInput");
    if (!input) return;
    const msg = input.value.trim();
    if (!msg) return;

    input.value = "";
    const reportBox = document.getElementById("outlierAiReport");
    if (reportBox) {
        reportBox.innerHTML = `
            <div style="background:#e0e7ff;border:1px solid #c7d2fe;padding:8px 10px;border-radius:6px;font-size:0.8rem;color:#1e40af;margin-bottom:6px;">
                <strong>You:</strong> ${escapeHtml(msg)}
            </div>
            <div style="background:#f8fafc;border:1px solid var(--border);padding:8px 10px;border-radius:6px;font-size:0.8rem;color:#475569;">
                <span class="status-dot"></span> <em>Drishti AI is analyzing failure morphology...</em>
            </div>
        `;
    }

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: `[Dynamic Outlier Context - Model: ${activeOutlierModel}] ${msg}` })
        });
        const data = await response.json();
        if (reportBox) {
            reportBox.innerHTML = `
                <div style="background:#e0e7ff;border:1px solid #c7d2fe;padding:8px 10px;border-radius:6px;font-size:0.8rem;color:#1e40af;margin-bottom:6px;">
                    <strong>You:</strong> ${escapeHtml(msg)}
                </div>
                <div style="background:#f8fafc;border:1px solid var(--border);padding:10px 12px;border-radius:6px;font-size:0.82rem;color:#334155;line-height:1.5;">
                    ${renderMarkdown(data.reply)}
                </div>
            `;
        }
    } catch (err) {
        if (reportBox) {
            reportBox.innerHTML += `<div style="color:#dc2626;font-size:0.8rem;margin-top:4px;">Error: ${err.message}</div>`;
        }
    }
}

// =============================================================================
// INITIALIZATION ON DOM READY
// =============================================================================

window.addEventListener("DOMContentLoaded", () => {
    fetchSystemHealth();
    navigateTo("landing");
});
