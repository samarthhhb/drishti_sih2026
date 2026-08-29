/**
 * SIH26170 - Frontend Application & Interactive Chart Controller
 * =============================================================================
 */

const MODEL_CONFIGS = {
    breakdown: {
        id: "breakdown",
        title: "Breakdown Model",
        paramTag: "Voltage (V) vs Current (A)",
        xLabel: "Collector-Emitter Voltage (V)",
        yLabel: "Leakage Current (A)",
        defaultX: 550.0,
        defaultUserY: 1.25e-5,
        defaultCompId: "NASA-IGBT-Part-12",
        xMin: 0,
        xMax: 650,
        yMin: 0,
        yMax: 1.5e-4,
        presets: [
            { name: "Aged (550V)", x: 550.0, userY: 1.25e-5, cid: "NASA-Part-12 (Aged)" },
            { name: "Pristine (300V)", x: 300.0, userY: 3.85e-9, cid: "NASA-Part-11 (Pristine)" },
            { name: "Runaway (580V)", x: 580.0, userY: 8.50e-5, cid: "NASA-Part-16 (Degraded)" }
        ]
    },
    leakage: {
        id: "leakage",
        title: "Leakage IV Model",
        paramTag: "Voltage (V) vs Current (A)",
        xLabel: "Applied Voltage (V)",
        yLabel: "Leakage Current (A)",
        defaultX: 25.0,
        defaultUserY: 4.50e-5,
        defaultCompId: "NASA-IGBT-Part-18",
        xMin: 0,
        xMax: 50,
        yMin: 0,
        yMax: 6.0e-5,
        presets: [
            { name: "Latent Defect (25V)", x: 25.0, userY: 4.50e-5, cid: "NASA-Part-18 (Latent)" },
            { name: "Healthy (10V)", x: 10.0, userY: 3.85e-9, cid: "NASA-Part-11 (Healthy)" },
            { name: "Thermal Bias (40V)", x: 40.0, userY: 1.50e-5, cid: "NASA-Part-15 (Thermal)" }
        ]
    },
    turnon: {
        id: "turnon",
        title: "Turn-On Model",
        paramTag: "Voltage (V) vs Current (A)",
        xLabel: "Gate Voltage (V)",
        yLabel: "Collector Current (A)",
        defaultX: 5.0,
        defaultUserY: 0.42,
        defaultCompId: "NASA-IGBT-Part-14",
        xMin: 0,
        xMax: 15,
        yMin: 0,
        yMax: 5.0,
        presets: [
            { name: "Oxide Trap (5V)", x: 5.0, userY: 0.42, cid: "NASA-Part-14 (Oxide Trap)" },
            { name: "Normal (6V)", x: 6.0, userY: 2.30, cid: "NASA-Part-11 (Normal)" },
            { name: "Degraded gm (8V)", x: 8.0, userY: 0.15, cid: "NASA-Part-19 (Bond Wire)" }
        ]
    }
};

let currentActiveModel = "breakdown";
let scatterChartInstance = null;
let lineChartInstance = null;
let datasetPointsCache = [];

const chartModes = {
    scatter: "point",
    line: "point"
};

const defaultChartBounds = {
    scatter: { xMin: 0, xMax: 650, yMin: 0, yMax: 1.5e-4 },
    line: { xMin: 0, xMax: 650, yMin: 0, yMax: 1.5e-4 }
};

let isDraggingPoint = false;
let isPanning = false;
let panStart = { x: 0, y: 0 };
let debounceTimer = null;

// =============================================================================
// NAVIGATION & MODEL SELECTION
// =============================================================================

function navigateTo(viewId) {
    document.querySelectorAll(".view-section").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".nav-btn").forEach(el => el.classList.remove("active"));

    if (viewId === "landing") {
        document.getElementById("view-landing").classList.add("active");
        document.getElementById("nav-landing").classList.add("active");
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

function loadModelPage(modelType) {
    currentActiveModel = modelType;
    const cfg = MODEL_CONFIGS[modelType];
    if (!cfg) return;

    document.getElementById("activeModelTitle").textContent = cfg.title;
    document.getElementById("activeModelParamTag").textContent = cfg.paramTag;

    document.getElementById("labelRawX").textContent = `Input: ${cfg.xLabel}`;
    document.getElementById("labelUserY").textContent = `Measured: ${cfg.yLabel}`;
    document.getElementById("lblModelOutput").textContent = "Model Output (A)";
    document.getElementById("lblUserOutput").textContent = "Measured Output (A)";

    document.getElementById("inputRawX").value = cfg.defaultX;
    document.getElementById("inputUserY").value = cfg.defaultUserY;
    document.getElementById("inputCompId").value = cfg.defaultCompId;

    // Configure Slider X
    const sliderX = document.getElementById("sliderX");
    sliderX.min = cfg.xMin;
    sliderX.max = cfg.xMax;
    sliderX.step = (cfg.xMax - cfg.xMin) / 200;
    sliderX.value = cfg.defaultX;
    document.getElementById("sliderValX").textContent = `${cfg.defaultX.toFixed(1)} V`;

    // Configure Slider Y
    const sliderY = document.getElementById("sliderY");
    if (modelType === "turnon") {
        sliderY.min = 0;
        sliderY.max = 5.0;
        sliderY.step = 0.02;
        sliderY.value = cfg.defaultUserY;
    } else {
        sliderY.min = -9;
        sliderY.max = -3;
        sliderY.step = 0.05;
        sliderY.value = Math.log10(cfg.defaultUserY);
    }
    document.getElementById("sliderValY").textContent = formatSci(cfg.defaultUserY) + " A";

    // Populate Presets
    const presetsContainer = document.getElementById("modelPresetsContainer");
    presetsContainer.innerHTML = "";
    cfg.presets.forEach(p => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "preset-btn";
        btn.textContent = p.name;
        btn.onclick = () => {
            setTestPoint(p.x, p.userY, p.cid);
            runModelPipeline();
        };
        presetsContainer.appendChild(btn);
    });

    document.getElementById("chatMessages").innerHTML = `
        <div class="chat-item bot-item">
            <div class="bubble bot-bubble">
                <strong>Ready:</strong> Move the test point directly on the graph or adjust values to trigger failure physics explanation.
            </div>
        </div>
    `;

    document.getElementById("resultsPanel").style.display = "none";

    defaultChartBounds.scatter = { xMin: cfg.xMin, xMax: cfg.xMax, yMin: cfg.yMin, yMax: cfg.yMax };
    defaultChartBounds.line = { xMin: cfg.xMin, xMax: cfg.xMax, yMin: cfg.yMin, yMax: cfg.yMax };

    navigateTo("model");
    loadDatasetAndInitCharts(modelType);
}

// =============================================================================
// SLIDER & INPUT CONTROLS
// =============================================================================

function onSliderChangeX(val) {
    const num = parseFloat(val);
    document.getElementById("inputRawX").value = num.toFixed(2);
    document.getElementById("sliderValX").textContent = `${num.toFixed(1)} V`;
    const userY = parseFloat(document.getElementById("inputUserY").value) || 0;
    updateChartMarkersOnly(num, userY);
    debouncePipeline();
}

function onSliderChangeY(val) {
    const num = parseFloat(val);
    let realY = 0;
    if (currentActiveModel === "turnon") {
        realY = num;
    } else {
        realY = Math.pow(10, num);
    }
    document.getElementById("inputUserY").value = realY < 1e-3 ? realY.toExponential(3) : realY.toFixed(4);
    document.getElementById("sliderValY").textContent = formatSci(realY) + " A";
    const x = parseFloat(document.getElementById("inputRawX").value) || 0;
    updateChartMarkersOnly(x, realY);
    debouncePipeline();
}

function onInputChangeX(val) {
    const num = parseFloat(val) || 0;
    document.getElementById("sliderX").value = num;
    document.getElementById("sliderValX").textContent = `${num.toFixed(1)} V`;
    const userY = parseFloat(document.getElementById("inputUserY").value) || 0;
    updateChartMarkersOnly(num, userY);
    debouncePipeline();
}

function onInputChangeY(val) {
    const num = parseFloat(val) || 0;
    if (currentActiveModel === "turnon") {
        document.getElementById("sliderY").value = num;
    } else if (num > 0) {
        document.getElementById("sliderY").value = Math.log10(num);
    }
    document.getElementById("sliderValY").textContent = formatSci(num) + " A";
    const x = parseFloat(document.getElementById("inputRawX").value) || 0;
    updateChartMarkersOnly(x, num);
    debouncePipeline();
}

function setTestPoint(x, y, cid) {
    document.getElementById("inputRawX").value = x;
    document.getElementById("sliderX").value = x;
    document.getElementById("sliderValX").textContent = `${x.toFixed(1)} V`;

    document.getElementById("inputUserY").value = y < 1e-3 ? y.toExponential(3) : y.toFixed(4);
    if (currentActiveModel === "turnon") {
        document.getElementById("sliderY").value = y;
    } else if (y > 0) {
        document.getElementById("sliderY").value = Math.log10(y);
    }
    document.getElementById("sliderValY").textContent = formatSci(y) + " A";

    if (cid) document.getElementById("inputCompId").value = cid;
    updateChartMarkersOnly(x, y);
}

function debouncePipeline() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        runModelPipeline();
    }, 450);
}

// =============================================================================
// CHART RENDERING & GESTURES
// =============================================================================

async function loadDatasetAndInitCharts(modelType) {
    try {
        const res = await fetch(`/api/dataset-sample?model=${modelType}&limit=120`);
        const data = await res.json();
        datasetPointsCache = data.points || [];

        const cfg = MODEL_CONFIGS[modelType];
        const initialX = parseFloat(document.getElementById("inputRawX").value) || cfg.defaultX;
        const initialUserY = parseFloat(document.getElementById("inputUserY").value) || cfg.defaultUserY;

        renderScatterplot(datasetPointsCache, { x: initialX, y: initialUserY }, cfg);
        renderLineChart(modelType, cfg, initialX, initialUserY);

        attachChartInteraction("scatterplotCanvas", "scatter");
        attachChartInteraction("lineChartCanvas", "line");
    } catch (err) {
        console.error("Failed to load dataset points:", err);
    }
}

function renderScatterplot(datasetPoints, livePoint, cfg) {
    const ctx = document.getElementById("scatterplotCanvas").getContext("2d");
    if (scatterChartInstance) scatterChartInstance.destroy();

    scatterChartInstance = new Chart(ctx, {
        type: "scatter",
        data: {
            datasets: [
                {
                    label: "NASA Lab Dataset",
                    data: datasetPoints,
                    backgroundColor: "rgba(30, 64, 175, 0.35)",
                    borderColor: "rgba(30, 64, 175, 0.7)",
                    borderWidth: 1,
                    pointRadius: 3
                },
                {
                    label: "Test Point",
                    data: livePoint ? [livePoint] : [],
                    backgroundColor: "#ea580c",
                    borderColor: "#ffffff",
                    borderWidth: 2.5,
                    pointRadius: 8.5,
                    pointHoverRadius: 10.5
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
                    title: { display: true, text: cfg.xLabel, color: "#334155", font: { size: 10, weight: "bold" } },
                    grid: { color: "#f1f5f9" },
                    ticks: { color: "#64748b", font: { size: 9 } }
                },
                y: {
                    type: "linear",
                    min: cfg.yMin,
                    max: cfg.yMax,
                    title: { display: true, text: cfg.yLabel, color: "#334155", font: { size: 10, weight: "bold" } },
                    grid: { color: "#f1f5f9" },
                    ticks: {
                        color: "#64748b",
                        font: { size: 9 },
                        callback: (v) => (Math.abs(v) < 1e-3 && v !== 0 ? v.toExponential(1) : v)
                    }
                }
            },
            plugins: {
                legend: { labels: { color: "#334155", font: { size: 10 } } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: (${ctx.parsed.x.toFixed(1)} V, ${formatSci(ctx.parsed.y)} A)`
                    }
                }
            }
        }
    });
}

function renderLineChart(modelType, cfg, currentX, currentYuser) {
    const ctx = document.getElementById("lineChartCanvas").getContext("2d");
    if (lineChartInstance) lineChartInstance.destroy();

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
            yPred = 7.1e-5 * Math.pow(x / 600, 4) + 1e-8;
        } else if (modelType === "leakage") {
            yPred = (1.84e-6 / 300) * x + 1e-9;
        } else {
            yPred = x > 4.0 ? 0.5 * Math.pow(x - 4.0, 1.8) : 1e-6;
        }
        linePoints.push({ x: x, y: yPred });
        upperTolerance.push({ x: x, y: yPred * 1.25 });
    }

    const testMarker = currentX && currentYuser !== undefined ? [{ x: currentX, y: currentYuser }] : [];

    lineChartInstance = new Chart(ctx, {
        type: "line",
        data: {
            datasets: [
                {
                    label: "Model Baseline",
                    data: linePoints,
                    borderColor: "#1e40af",
                    backgroundColor: "rgba(30, 64, 175, 0.05)",
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.25,
                    fill: false
                },
                {
                    label: "Limit (+25%)",
                    data: upperTolerance,
                    borderColor: "#cbd5e1",
                    borderDash: [4, 4],
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: "Measured Point",
                    data: testMarker,
                    type: "scatter",
                    backgroundColor: "#ea580c",
                    borderColor: "#ffffff",
                    borderWidth: 2.5,
                    pointRadius: 8.5,
                    pointHoverRadius: 10.5
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
                    title: { display: true, text: cfg.xLabel, color: "#334155", font: { size: 10, weight: "bold" } },
                    grid: { color: "#f1f5f9" },
                    ticks: { color: "#64748b", font: { size: 9 } }
                },
                y: {
                    type: "linear",
                    min: cfg.yMin,
                    max: cfg.yMax,
                    title: { display: true, text: cfg.yLabel, color: "#334155", font: { size: 10, weight: "bold" } },
                    grid: { color: "#f1f5f9" },
                    ticks: {
                        color: "#64748b",
                        font: { size: 9 },
                        callback: (v) => (Math.abs(v) < 1e-3 && v !== 0 ? v.toExponential(1) : v)
                    }
                }
            },
            plugins: {
                legend: { labels: { color: "#334155", font: { size: 10 } } }
            }
        }
    });
}

function attachChartInteraction(canvasId, chartKey) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    function getChart() {
        return chartKey === "scatter" ? scatterChartInstance : lineChartInstance;
    }

    function getCanvasCoordinates(e) {
        const rect = canvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        return {
            xPx: clientX - rect.left,
            yPx: clientY - rect.top
        };
    }

    function dataFromPixel(xPx, yPx) {
        const chart = getChart();
        if (!chart) return null;
        const xVal = chart.scales.x.getValueForPixel(xPx);
        const yVal = chart.scales.y.getValueForPixel(yPx);
        return { x: xVal, y: yVal };
    }

    function onPointerDown(e) {
        const chart = getChart();
        if (!chart) return;

        const coords = getCanvasCoordinates(e);
        panStart = coords;

        if (chartModes[chartKey] === "point") {
            isDraggingPoint = true;
            const dataPoint = dataFromPixel(coords.xPx, coords.yPx);
            if (dataPoint) {
                const clampedX = Math.max(chart.scales.x.min, Math.min(chart.scales.x.max, dataPoint.x));
                const clampedY = Math.max(0, Math.min(chart.scales.y.max, dataPoint.y));
                setTestPoint(clampedX, clampedY);
            }
        } else {
            isPanning = true;
        }
    }

    function onPointerMove(e) {
        const chart = getChart();
        if (!chart) return;

        const coords = getCanvasCoordinates(e);

        if (isDraggingPoint && chartModes[chartKey] === "point") {
            const dataPoint = dataFromPixel(coords.xPx, coords.yPx);
            if (dataPoint) {
                const clampedX = Math.max(chart.scales.x.min, Math.min(chart.scales.x.max, dataPoint.x));
                const clampedY = Math.max(0, Math.min(chart.scales.y.max, dataPoint.y));
                setTestPoint(clampedX, clampedY);
            }
        } else if (isPanning && chartModes[chartKey] === "pan") {
            const dxPx = coords.xPx - panStart.xPx;
            const dyPx = coords.yPx - panStart.yPx;
            panStart = coords;

            const xRange = chart.scales.x.max - chart.scales.x.min;
            const dxVal = (dxPx / chart.width) * xRange;
            chart.scales.x.options.min = chart.scales.x.min - dxVal;
            chart.scales.x.options.max = chart.scales.x.max - dxVal;

            const yRange = chart.scales.y.max - chart.scales.y.min;
            const dyVal = (dyPx / chart.height) * yRange;
            chart.scales.y.options.min = Math.max(0, chart.scales.y.min + dyVal);
            chart.scales.y.options.max = chart.scales.y.max + dyVal;

            chart.update("none");
        }
    }

    function onPointerUp(e) {
        if (isDraggingPoint) {
            isDraggingPoint = false;
            runModelPipeline();
        }
        isPanning = false;
    }

    function onWheel(e) {
        e.preventDefault();
        const chart = getChart();
        if (!chart) return;
        const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
        zoomChart(chartKey, zoomFactor);
    }

    canvas.onmousedown = onPointerDown;
    canvas.onmousemove = onPointerMove;
    canvas.onmouseup = onPointerUp;
    canvas.onmouseleave = onPointerUp;
    canvas.onwheel = onWheel;

    canvas.ontouchstart = onPointerDown;
    canvas.ontouchmove = onPointerMove;
    canvas.ontouchend = onPointerUp;
}

function setChartMode(chartKey, mode) {
    chartModes[chartKey] = mode;
    const btnPoint = document.getElementById(`btnMode${chartKey === "scatter" ? "Scatter" : "Line"}Point`);
    const btnPan = document.getElementById(`btnMode${chartKey === "scatter" ? "Scatter" : "Line"}Pan`);
    const box = document.getElementById(chartKey === "scatter" ? "scatterBox" : "lineBox");

    if (mode === "point") {
        btnPoint.classList.add("active");
        btnPan.classList.remove("active");
        box.classList.remove("pan-mode");
    } else {
        btnPoint.classList.remove("active");
        btnPan.classList.add("active");
        box.classList.add("pan-mode");
    }
}

function zoomChart(chartKey, factor) {
    const chart = chartKey === "scatter" ? scatterChartInstance : lineChartInstance;
    if (!chart) return;

    const xMin = chart.scales.x.min;
    const xMax = chart.scales.x.max;
    const xCenter = (xMin + xMax) / 2;
    const xRange = (xMax - xMin) / factor;

    chart.scales.x.options.min = xCenter - (xRange / 2);
    chart.scales.x.options.max = xCenter + (xRange / 2);

    const yMin = chart.scales.y.min;
    const yMax = chart.scales.y.max;
    const yRange = (yMax - yMin) / factor;
    chart.scales.y.options.min = Math.max(0, yMin);
    chart.scales.y.options.max = yMin + yRange;

    chart.update();
}

function resetChartZoom(chartKey) {
    const chart = chartKey === "scatter" ? scatterChartInstance : lineChartInstance;
    if (!chart) return;

    const bounds = defaultChartBounds[chartKey];
    chart.scales.x.options.min = bounds.xMin;
    chart.scales.x.options.max = bounds.xMax;
    chart.scales.y.options.min = bounds.yMin;
    chart.scales.y.options.max = bounds.yMax;
    chart.update();
}

function updateChartMarkersOnly(x, y) {
    const livePoint = { x: x, y: y };
    if (scatterChartInstance && scatterChartInstance.data.datasets.length > 1) {
        scatterChartInstance.data.datasets[1].data = [livePoint];
        scatterChartInstance.update("none");
    }
    if (lineChartInstance && lineChartInstance.data.datasets.length > 2) {
        lineChartInstance.data.datasets[2].data = [livePoint];
        lineChartInstance.update("none");
    }
}

// =============================================================================
// PIPELINE & CHATBOT EXECUTION
// =============================================================================

async function runModelPipeline() {
    const rawX = parseFloat(document.getElementById("inputRawX").value);
    const userYVal = document.getElementById("inputUserY").value.trim();
    const userY = userYVal !== "" ? parseFloat(userYVal) : null;
    const cid = document.getElementById("inputCompId").value.trim() || "DUT-01";

    const btn = document.getElementById("runPipelineBtn");
    btn.innerHTML = "Screening...";
    btn.disabled = true;

    try {
        const response = await fetch("/api/pipeline/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                model_type: currentActiveModel,
                raw_input: rawX,
                user_said_output: userY,
                component_id: cid,
                use_ai: true
            })
        });

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        const resPanel = document.getElementById("resultsPanel");
        resPanel.style.display = "block";

        const badge = document.getElementById("riskDecisionBadge");
        const decision = data.discrepancy.risk_decision;
        badge.textContent = decision;
        badge.className = "verdict-pill " + (decision === "PASS" ? "badge-pass" : (decision === "HOLD" ? "badge-hold" : "badge-reject"));

        document.getElementById("statRawX").textContent = `${data.raw_input.toFixed(1)} V`;
        document.getElementById("statScaledX").textContent = `${data.scaled_input > 0 ? "+" : ""}${data.scaled_input.toFixed(1)} σ`;
        document.getElementById("statModelY").textContent = formatSci(data.physical_output) + " " + data.output_unit.replace(" (Amperes)", " A").replace(" (Volts)", " V");
        document.getElementById("statUserY").textContent = data.user_said_output !== null ? (formatSci(data.user_said_output) + " " + data.output_unit.replace(" (Amperes)", " A").replace(" (Volts)", " V")) : "N/A";
        document.getElementById("statPctDiff").textContent = data.discrepancy.pct_diff !== null ? `${data.discrepancy.pct_diff > 0 ? "+" : ""}${data.discrepancy.pct_diff.toFixed(1)}%` : "0.0%";
        document.getElementById("statRatio").textContent = data.discrepancy.ratio !== null ? `${data.discrepancy.ratio.toFixed(2)}x` : "1.00x";

        appendBotMessage(data.chatbot_explanation);
        updateChartMarkersOnly(rawX, userY !== null ? userY : data.physical_output);

    } catch (err) {
        alert("Error: " + err.message);
    } finally {
        btn.innerHTML = "Run Screening & Explain";
        btn.disabled = false;
    }
}

async function sendChatMessage() {
    const input = document.getElementById("interactiveChatInput");
    const msg = input.value.trim();
    if (!msg) return;

    appendUserMessage(msg);
    input.value = "";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg })
        });
        const data = await response.json();
        appendBotMessage(data.reply);
    } catch (err) {
        appendBotMessage("Error: " + err.message);
    }
}

function appendUserMessage(text) {
    const chat = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "chat-item user-item";
    div.innerHTML = `<div class="bubble user-bubble">${escapeHtml(text)}</div>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function appendBotMessage(markdown) {
    const chat = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "chat-item bot-item";
    div.innerHTML = `<div class="bubble bot-bubble">${renderMarkdown(markdown)}</div>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function formatSci(val) {
    if (val === 0 || val === null || val === undefined) return "0.00";
    if (Math.abs(val) < 1e-3 || Math.abs(val) >= 1e5) return val.toExponential(2);
    return val.toFixed(3);
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

window.addEventListener("DOMContentLoaded", () => {
    navigateTo("landing");
});
