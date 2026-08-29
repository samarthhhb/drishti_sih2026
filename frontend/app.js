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
        paramTag: "Voltage (V) vs Current (microAmpere)",
        xLabel: "Collector-Emitter Voltage (V)",
        yLabel: "Leakage Current (microAmpere)",
        defaultX: 550.0,
        defaultUserY: 12.5,
        defaultCompId: "NASA-IGBT-Part-12",
        xMin: 0,
        xMax: 650,
        yMin: 0,
        yMax: 150,
        presets: [
            { name: "Aged (550V)", x: 550.0, userY: 12.5, cid: "NASA-Part-12 (Aged)" },
            { name: "Pristine (300V)", x: 300.0, userY: 0.05, cid: "NASA-Part-11 (Pristine)" },
            { name: "Runaway (580V)", x: 580.0, userY: 85.0, cid: "NASA-Part-16 (Degraded)" }
        ]
    },
    leakage: {
        id: "leakage",
        title: "Leakage IV Model",
        paramTag: "Voltage (V) vs Current (microAmpere)",
        xLabel: "Applied Voltage (V)",
        yLabel: "Leakage Current (microAmpere)",
        defaultX: 25.0,
        defaultUserY: 4.5,
        defaultCompId: "NASA-IGBT-Part-18",
        xMin: 0,
        xMax: 600,
        yMin: 0,
        yMax: 10.0,
        presets: [
            { name: "Latent Defect (25V)", x: 25.0, userY: 4.5, cid: "NASA-Part-18 (Latent)" },
            { name: "Healthy (10V)", x: 10.0, userY: 0.05, cid: "NASA-Part-11 (Healthy)" },
            { name: "Thermal Bias (40V)", x: 40.0, userY: 2.5, cid: "NASA-Part-15 (Thermal)" }
        ]
    },
    turnon: {
        id: "turnon",
        title: "Turn-On Model",
        paramTag: "Voltage (V) vs Current (microAmpere)",
        xLabel: "Gate Voltage (V)",
        yLabel: "Collector Current (microAmpere)",
        defaultX: 5.0,
        defaultUserY: 25.0,
        defaultCompId: "NASA-IGBT-Part-14",
        xMin: 0,
        xMax: 15,
        yMin: 0,
        yMax: 250.0,
        presets: [
            { name: "Oxide Trap (5V)", x: 5.0, userY: 25.0, cid: "NASA-Part-14 (Oxide Trap)" },
            { name: "Normal (6V)", x: 6.0, userY: 150.0, cid: "NASA-Part-11 (Normal)" },
            { name: "Degraded gm (8V)", x: 8.0, userY: 10.0, cid: "NASA-Part-19 (Bond Wire)" }
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
    scatter: { xMin: 0, xMax: 650, yMin: 0, yMax: 150 },
    line: { xMin: 0, xMax: 650, yMin: 0, yMax: 150 }
};

let isDraggingPoint = false;
let isPanning = false;
let panStart = { x: 0, y: 0 };
let debounceTimer = null;

// =============================================================================
// FLOATING AI ASSISTANT DRAWER CONTROLLER
// =============================================================================

function toggleAIChat(forceOpen) {
    const drawer = document.getElementById("aiDrawerPanel");
    const badge = document.getElementById("aiUnreadBadge");
    if (!drawer) return;

    const isCurrentlyOpen = drawer.style.display === "flex";
    const shouldOpen = forceOpen !== undefined ? forceOpen : !isCurrentlyOpen;

    if (shouldOpen) {
        drawer.style.display = "flex";
        if (badge) badge.style.display = "none";
        // Auto scroll to bottom
        const chatBox = document.getElementById("chatMessages");
        if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
        const input = document.getElementById("interactiveChatInput");
        if (input) setTimeout(() => input.focus(), 150);
    } else {
        drawer.style.display = "none";
    }
}

// =============================================================================
// SYSTEM HEALTH & DYNAMIC API DISCOVERY
// =============================================================================

async function fetchSystemHealth() {
    try {
        const res = await fetch("/api/health");
        const data = await res.json();
        const badge = document.getElementById("engineText");
        const pill = document.getElementById("chatEnginePill");

        if (data.status === "healthy") {
            const providerStr = data.active_llm || (data.ai_provider ? data.ai_provider.toUpperCase() : "Online");
            if (badge) badge.textContent = providerStr;
            if (pill) pill.textContent = providerStr;
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

    // Clear chat and reset results panel
    document.getElementById("chatMessages").innerHTML = "";

    defaultChartBounds.scatter = { xMin: cfg.xMin, xMax: cfg.xMax, yMin: cfg.yMin, yMax: cfg.yMax };
    defaultChartBounds.line = { xMin: cfg.xMin, xMax: cfg.xMax, yMin: cfg.yMin, yMax: cfg.yMax };

    navigateTo("model");
    loadDatasetAndInitCharts(modelType);

    // Immediately execute live dynamic pipeline inference for the selected model
    runModelPipeline();
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
            yPred = 71.0 * Math.pow(x / 600, 4) + 0.01;
        } else if (modelType === "leakage") {
            yPred = (1.84 / 300) * x + 0.01;
        } else {
            yPred = x > 4.0 ? 25.0 * Math.pow(x - 4.0, 1.8) : 0.01;
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

            const cfg = MODEL_CONFIGS[currentActiveModel] || { xMin: 0, xMax: 650, yMin: 0, yMax: 1.5e-4 };
            const baseXSpan = cfg.xMax - cfg.xMin;
            const baseYSpan = cfg.yMax - cfg.yMin;
            
            // Strictly enforce max 15% padding beyond nominal model range
            const allowedXMin = cfg.xMin - (0.15 * baseXSpan);
            const allowedXMax = cfg.xMax + (0.15 * baseXSpan);
            const allowedYMin = Math.max(0, cfg.yMin - (0.15 * baseYSpan));
            const allowedYMax = cfg.yMax + (0.15 * baseYSpan);

            const xRange = chart.scales.x.max - chart.scales.x.min;
            const dxVal = (dxPx / chart.width) * xRange;
            let newXMin = chart.scales.x.min - dxVal;
            let newXMax = chart.scales.x.max - dxVal;

            if (newXMin < allowedXMin) {
                newXMin = allowedXMin;
                newXMax = allowedXMin + xRange;
            } else if (newXMax > allowedXMax) {
                newXMax = allowedXMax;
                newXMin = allowedXMax - xRange;
            }

            const yRange = chart.scales.y.max - chart.scales.y.min;
            const dyVal = (dyPx / chart.height) * yRange;
            let newYMin = chart.scales.y.min + dyVal;
            let newYMax = chart.scales.y.max + dyVal;

            if (newYMin < allowedYMin) {
                newYMin = allowedYMin;
                newYMax = allowedYMin + yRange;
            } else if (newYMax > allowedYMax) {
                newYMax = allowedYMax;
                newYMin = allowedYMax - yRange;
            }

            chart.scales.x.options.min = newXMin;
            chart.scales.x.options.max = newXMax;
            chart.scales.y.options.min = newYMin;
            chart.scales.y.options.max = newYMax;

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

    const cfg = MODEL_CONFIGS[currentActiveModel] || { xMin: 0, xMax: 650, yMin: 0, yMax: 1.5e-4 };
    const baseXSpan = cfg.xMax - cfg.xMin;
    const baseYSpan = cfg.yMax - cfg.yMin;
    const allowedXMin = cfg.xMin - (0.15 * baseXSpan);
    const allowedXMax = cfg.xMax + (0.15 * baseXSpan);
    const allowedYMin = Math.max(0, cfg.yMin - (0.15 * baseYSpan));
    const allowedYMax = cfg.yMax + (0.15 * baseYSpan);

    const xMin = chart.scales.x.min;
    const xMax = chart.scales.x.max;
    const xCenter = (xMin + xMax) / 2;
    let newXSpan = (xMax - xMin) / factor;

    // Limit maximum zoom out to 1.30x base span (15% padding) and minimum zoom in to 10%
    newXSpan = Math.max(baseXSpan * 0.1, Math.min(baseXSpan * 1.30, newXSpan));

    let newXMin = xCenter - (newXSpan / 2);
    let newXMax = xCenter + (newXSpan / 2);

    if (newXMin < allowedXMin) {
        newXMin = allowedXMin;
        newXMax = Math.min(allowedXMax, allowedXMin + newXSpan);
    }
    if (newXMax > allowedXMax) {
        newXMax = allowedXMax;
        newXMin = Math.max(allowedXMin, allowedXMax - newXSpan);
    }

    const yMin = chart.scales.y.min;
    const yMax = chart.scales.y.max;
    const yCenter = (yMin + yMax) / 2;
    let newYSpan = (yMax - yMin) / factor;

    newYSpan = Math.max(baseYSpan * 0.1, Math.min(baseYSpan * 1.30, newYSpan));

    let newYMin = yCenter - (newYSpan / 2);
    let newYMax = yCenter + (newYSpan / 2);

    if (newYMin < allowedYMin) {
        newYMin = allowedYMin;
        newYMax = Math.min(allowedYMax, allowedYMin + newYSpan);
    }
    if (newYMax > allowedYMax) {
        newYMax = allowedYMax;
        newYMin = Math.max(allowedYMin, allowedYMax - newYSpan);
    }

    chart.scales.x.options.min = newXMin;
    chart.scales.x.options.max = newXMax;
    chart.scales.y.options.min = newYMin;
    chart.scales.y.options.max = newYMax;

    chart.update("none");
}

function resetChartZoom(chartKey) {
    const chart = chartKey === "scatter" ? scatterChartInstance : lineChartInstance;
    if (!chart) return;

    const cfg = MODEL_CONFIGS[currentActiveModel] || { xMin: 0, xMax: 650, yMin: 0, yMax: 1.5e-4 };
    chart.scales.x.options.min = cfg.xMin;
    chart.scales.x.options.max = cfg.xMax;
    chart.scales.y.options.min = cfg.yMin;
    chart.scales.y.options.max = cfg.yMax;
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
// PIPELINE & CHATBOT EXECUTION (100% Dynamic API)
// =============================================================================

async function runModelPipeline() {
    const rawX = parseFloat(document.getElementById("inputRawX").value);
    const userYVal = document.getElementById("inputUserY").value.trim();
    const userY = userYVal !== "" ? parseFloat(userYVal) : null;
    const cid = document.getElementById("inputCompId").value.trim() || "DUT-01";

    const btn = document.getElementById("runPipelineBtn");
    btn.innerHTML = "Screening Live...";
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

        // Dynamically display results panel
        const resPanel = document.getElementById("resultsPanel");
        resPanel.style.display = "block";

        const badge = document.getElementById("riskDecisionBadge");
        const decision = data.discrepancy.risk_decision;
        badge.textContent = decision;
        badge.className = "verdict-pill " + (decision === "PASS" ? "badge-pass" : (decision === "HOLD" ? "badge-hold" : "badge-reject"));

        document.getElementById("statRawX").textContent = `${data.raw_input.toFixed(1)} V`;
        const statScaled = document.getElementById("statScaledX");
        if (statScaled) {
            statScaled.textContent = data.scaled_input !== undefined ? `${data.scaled_input.toFixed(4)}` : "—";
        }
        document.getElementById("statModelY").textContent = `${formatSci(data.physical_output)} microAmpere`;
        document.getElementById("statUserY").textContent = data.user_said_output !== null ? `${formatSci(data.user_said_output)} microAmpere` : "N/A";
        document.getElementById("statPctDiff").textContent = data.discrepancy.pct_diff !== null ? `${data.discrepancy.pct_diff > 0 ? "+" : ""}${data.discrepancy.pct_diff.toFixed(1)}%` : "0.0%";
        document.getElementById("statRatio").textContent = data.discrepancy.ratio !== null ? `${data.discrepancy.ratio.toFixed(2)}x` : "1.00x";

        // Update on-screen AI Report Box inside resultsPanel
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
        updateChartMarkersOnly(rawX, userY !== null ? userY : data.physical_output);

        // Notify user via unread badge on floating AI widget if collapsed
        const drawer = document.getElementById("aiDrawerPanel");
        const unread = document.getElementById("aiUnreadBadge");
        if (drawer && drawer.style.display !== "flex" && unread) {
            unread.style.display = "flex";
        }

    } catch (err) {
        alert("API Error: " + err.message);
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

    // Show temporary thinking indicator
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
    fetchSystemHealth();
    navigateTo("landing");
});
