# SIH26170 - REST API and Architecture Reference
### Semiconductor Stress Screening, Time-Series Inference, and Dynamic Outlier Detection Engine
**Project: SIH26170 • Team Drishti • Symbiosis Institute of Technology, Pune • Smart India Hackathon 2024**

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Base URL and Protocol](#2-base-url-and-protocol)
3. [REST API Endpoints](#3-rest-api-endpoints)
   - [GET /api/health](#get-apihealth)
   - [GET /api/models](#get-apimodels)
   - [GET /api/timeseries-data](#get-apitimeseries-data)
   - [GET /api/dataset-sample](#get-apidataset-sample)
   - [POST /api/pipeline/run](#post-apipipelinerun)
   - [POST /api/predict](#post-apipredict)
   - [POST /api/anomaly/detect](#post-apianomalydetect)
   - [GET /api/anomaly/population](#get-apianomalypopulation)
   - [GET /api/anomaly/features](#get-apianomalyfeatures)
   - [POST /api/chat](#post-apichat)
   - [GET /api/stats](#get-apistats)
   - [GET /api/screenings](#get-apiscreenings)
   - [GET /api/screenings/{id}](#get-apiscreeningsid)
4. [Dynamic Outlier Detection Architecture (17-Feature Morphometry)](#4-dynamic-outlier-detection-architecture-17-feature-morphometry)
5. [Feature Standardization and Scaling](#5-feature-standardization-and-scaling)
6. [Physics-Grounded AI Explainability Engine](#6-physics-grounded-ai-explainability-engine)
7. [Python Programmatic Usage](#7-python-programmatic-usage)
8. [Resilience and Fallback Modes](#8-resilience-and-fallback-modes)

---

## 1. Architecture Overview

The backend coordinates communication between the client dashboard, time-series Gradient Boosted regression models, the 17-feature Dynamic Outlier Detection Engine, the Groq Llama 3.3 explanation service, and persistent SQLite storage:

```
  CLIENT (Browser Dashboard, Automated Test Bench, or Python Script)
  │
  ▼
  ┌──────────────────────────────────────────────────────────────┐
  │              HTTP REST Server (backend/app.py)               │
  │             Port 5000 • Python Standard Library              │
  └───────────────┬──────────────────────────────┬───────────────┘
                  │                              │
                  ▼                              ▼
  ┌───────────────────────────────┐ ┌────────────────────────────┐
  │  Screening Pipeline           │ │  Dynamic Outlier Engine    │
  │  (backend/pipeline.py)        │ │ (backend/anomaly_engine.py)│
  └───────┬───────────────┬───────┘ └────────────┬───────────────┘
          │               │                      │
  ┌───────┴───────┐ ┌─────┴─────────┐ ┌──────────┴───────────────┐
  ▼               ▼ ▼               ▼ ▼                          ▼
┌──────────────┐ ┌───────────────┐ ┌─────────────┐ ┌─────────────┐
│MinMax Scaler │ │Time-Series GBR│ │ 17-Feature  │ │Dual-Layer   │
│ (scaler.py)  │ │(model_engine) │ │ Morphometry │ │Fusion Engine│
└──────────────┘ └───────────────┘ └─────────────┘ └─────────────┘
          │               │                      │
          └───────────────┼──────────────────────┘
                          ▼
            ┌───────────────────────────┐
            │   Groq AI Physics Agent   │
            │    (models/chatbot.py)    │
            │  Llama 3.3 70B Versatile  │
            └─────────────┬─────────────┘
                          │
                          ▼
            ┌───────────────────────────┐
            │  SQLite Screening Audit   │
            │    (backend/data/*.db)    │
            └───────────────────────────┘
```

---

## 2. Base URL and Protocol

- **Base URL**: `http://localhost:5000`
- **Default Content-Type**: `application/json`
- **CORS**: Enabled (`*`) for local test benches and web clients.
- **Environment Keys**: `GROQ_API_KEY` (or `GEMINI_API_KEY`) loaded from `.env`. If offline or without keys, the built-in deterministic semiconductor physics engine executes with zero downtime.

---

## 3. REST API Endpoints

### `GET /api/health`
Returns full system health, service metadata, active language model provider, connected LLM architecture, and status text.

**Example Request:**
```bash
curl -X GET http://localhost:5000/api/health
```

**Example Response:**
```json
{
  "status": "healthy",
  "service": "SIH26170-Fullstack-System",
  "ai_provider": "groq",
  "ai_model": "llama-3.3-70b-versatile",
  "ai_provider_display": "Groq LPU",
  "ai_badge": "Groq • Llama 3.3 70B Versatile",
  "ai_status": "ONLINE",
  "llm_connected": "llama-3.3-70b-versatile"
}
```

---

### `GET /api/models`
Returns physics metadata, input/output parameters, units, typical ranges, and min/max calibration bounds for all 3 screening models (`breakdown`, `leakage`, `turnon`).

---

### `GET /api/timeseries-data?model={breakdown|leakage|turnon}&limit=120`
Returns sequential chronological telemetry points for time-series degradation charts (3,790 observations with 30-minute sampling intervals).

---

### `POST /api/pipeline/run`
**Primary Screening Execution Endpoint**. Evaluates scalar test bench measurements, normalizes inputs, forecasts expected degradation via Gradient Boosted Regression, calculates residuals, and produces a physics-grounded verdict.

**Request Body:**
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `model_type` | string | Yes | `breakdown`, `leakage`, or `turnon` |
| `raw_input` | float | Yes | Applied voltage in Volts |
| `time_minutes` | float | No | Accelerated burn-in time in minutes (default: `90960.0`) |
| `user_said_output` | float | No | Measured current from test bench in $\mu\text{A}$ |
| `component_id` | string | No | Component DUT Identifier (default: `DUT-01`) |
| `use_ai` | boolean | No | Enable generative failure explanation (default: `true`) |

**Example Response:**
```json
{
  "record_id": 14,
  "component_id": "NASA-IGBT-Part-12",
  "model_type": "breakdown",
  "raw_input": 550.0,
  "input_unit": "V",
  "scaled_input": 0.8462,
  "physical_output": 86.69,
  "output_unit": "microAmpere",
  "user_said_output": 20.67,
  "timestamp": 100110,
  "actual_value_uA": 20.67,
  "predicted_value_uA": 86.69,
  "residual_uA": -66.02,
  "drift_percentage": -76.2,
  "trend": "increasing",
  "prediction_status": "underprediction",
  "explanation": "Model significantly underpredicted the observed leakage current (drift: -76.2%).",
  "time_series_monitor": {
    "timestamp": 100110,
    "actual_value_uA": 20.67,
    "predicted_value_uA": 86.69,
    "residual_uA": -66.02,
    "drift_percentage": -76.2,
    "trend": "increasing",
    "prediction_status": "underprediction",
    "explanation": "Model significantly underpredicted the observed leakage current."
  },
  "discrepancy": {
    "delta": -66.02,
    "pct_diff": -76.16,
    "residual_uA": -66.02,
    "drift_percentage": -76.2,
    "risk_decision": "HOLD",
    "severity": "MODERATE"
  }
}
```

---

### `POST /api/monitor`
**Time-Series Telemetry & Residual Monitoring Endpoint**. Accepts elapsed burn-in timestamp and measured values to compute dynamic residuals, drift rate, prediction status, and physical trend.

**Request Body:**
```json
{
  "timestamp": 100110,
  "actual_value_uA": 20.67,
  "predicted_value_uA": 86.69
}
```

**Response:**
```json
{
  "timestamp": 100110,
  "actual_value_uA": 20.67,
  "predicted_value_uA": 86.69,
  "residual_uA": -66.02,
  "drift_percentage": -76.2,
  "trend": "increasing",
  "prediction_status": "underprediction",
  "explanation": "Model significantly underpredicted the observed leakage current."
}
```

---

### `POST /api/anomaly/detect`
**Dynamic Outlier Detection System Endpoint**. Ingests a complete multi-cycle I-V characterization sweep curve, extracts 17 morphometric & electrical features, computes Robust Dynamic IQR Z-Scores relative to lot threshold $\theta_{\text{dynamic}}$, executes Isolation Forest ML scoring, and produces a Dual-Layer Fusion Verdict (`PASS` / `HOLD` / `REJECT`).

**Request Body:**
```json
{
  "model_type": "breakdown",
  "component_id": "NASA-IGBT-DUT-09",
  "curve": {
    "x": [2.02, 3.50, 4.80, 5.15, 5.20],
    "y": [0.0058, 0.080, 5.20, 45.0, 85.0]
  },
  "include_curve_data": true
}
```

**Example Response:**
```json
{
  "success": true,
  "system_name": "Dynamic Outlier Detection System",
  "model_type": "breakdown",
  "component_id": "NASA-IGBT-DUT-09",
  "anomaly": {
    "dynamic_score": 31.123,
    "dynamic_threshold": 8.083,
    "dynamic_flag": "ANOMALY",
    "outlier_feature_count": 3,
    "outlier_features": [
      {
        "feature": "max_slope",
        "label": "Max Transconductance / Steepness (dI/dV)",
        "robust_score": 31.12,
        "direction": "HIGH"
      },
      {
        "feature": "curve_area",
        "label": "Integrated I-V Area (μA·V)",
        "robust_score": 10.00,
        "direction": "HIGH"
      }
    ],
    "isolation_score": 0.6306,
    "isolation_flag": "ANOMALY",
    "combined_score": 2.20,
    "decision": "REJECT",
    "severity": "HIGH",
    "weights": {
      "dynamic": 0.60,
      "isolation_forest": 0.40
    }
  },
  "features": {
    "min_voltage": 2.02,
    "max_voltage": 5.20,
    "knee_voltage": 5.15,
    "max_slope": 0.00144,
    "curve_area": 0.000042
  },
  "feature_details": {
    "max_slope": {
      "name": "max_slope",
      "label": "Max Transconductance / Steepness (dI/dV)",
      "value": 0.00144,
      "population_median": 0.000045,
      "population_mad": 0.000021,
      "robust_z": 31.12,
      "abs_z": 31.12,
      "is_outlier": true
    }
  },
  "diagnostic_report": "### 🛑 Critical Curve-Level Defect — REJECT\n- **Physical Failure Mode**: Premature avalanche breakdown multiplication."
}
```

---

### `GET /api/anomaly/population?model={breakdown|leakage|turnon}`
Returns baseline population sweep curves across the screening lot, feature statistics (median & MAD), and dynamic threshold $\theta_{\text{dynamic}}$ for interactive population overlay charts.

---

### `GET /api/anomaly/features`
Returns full dictionary of the 17 morphometric feature names, human-readable labels, and electrical definitions.

---

### `POST /api/chat`
Conversational chat endpoint for asking physics, degradation mechanism, or screening criteria questions. Responses stream with Groq Llama 3.3 or deterministic semiconductor fallback.

**Request Body:**
```json
{
  "message": "Explain how SRH recombination causes sub-threshold leakage increase during burn-in.",
  "session_id": "lab_bench_session_1"
}
```

---

### `GET /api/stats`
Returns summary statistics of historical screenings stored in SQLite (total screenings, PASS count, HOLD count, REJECT count, average delta).

---

### `GET /api/screenings?limit=50&offset=0`
Returns paginated historical screening records with full audit trail.

---

## 4. Dynamic Outlier Detection Architecture (17-Feature Morphometry)

| # | Feature | Definition | Physical Significance |
| :---: | :--- | :--- | :--- |
| 1 | `min_voltage` | Minimum sweep voltage ($V_{\min}$) | Zero-bias contact offset |
| 2 | `max_voltage` | Peak sweep voltage ($V_{\max}$) | Peak stress electric field |
| 3 | `min_current` | Minimum sweep current ($I_{\min}$) | Sub-threshold noise floor |
| 4 | `max_current` | Maximum sweep current ($I_{\max}$) | Peak conduction / avalanche ceiling |
| 5 | `mean_current` | Mean sweep current ($\bar{I}$) | Global thermal dissipation |
| 6 | `std_current` | Current standard deviation ($\sigma_I$) | Curve dispersion / variability |
| 7 | `max_slope` | Maximum slope ($\max dI/dV$) | Peak transconductance / avalanche steepness |
| 8 | `mean_slope` | Mean conductance ($\overline{dI/dV}$) | Global channel conductance |
| 9 | `knee_voltage` | Voltage at max slope ($V_{\text{knee}}$) | Avalanche knee $V_{BR}$ or threshold $V_{th}$ |
| 10 | `current_v25` | Current at 25% span ($I_{V25}$) | Low-field ohmic / SRH leakage |
| 11 | `current_v50` | Current at 50% span ($I_{V50}$) | Mid-field Poole-Frenkel emission |
| 12 | `current_v75` | Current at 75% span ($I_{V75}$) | Pre-avalanche carrier multiplication |
| 13 | `current_v90` | Current at 90% span ($I_{V90}$) | High-field avalanche onset |
| 14 | `voltage_10pct` | Voltage at 10% peak current | Sub-threshold turn-on boundary |
| 15 | `voltage_50pct` | Voltage at 50% peak current | Conduction transition midpoint |
| 16 | `voltage_90pct` | Voltage at 90% peak current | Hard saturation / avalanche boundary |
| 17 | `curve_area` | Total integrated area ($\int I \, dV$) | Total energy dissipation integral |

---

## 5. Feature Standardization and Scaling

All features are normalized using calibrated MinMax transforms to preserve model numerical stability:

$$x_{\text{scaled}} = \frac{x_{\text{raw}} - x_{\min}}{x_{\max} - x_{\min}}, \quad x_{\text{scaled}} \in [0, 1]$$

---

## 6. Physics-Grounded AI Explainability Engine

Powered by Groq Llama 3.3 70B Versatile, the explainability engine translates mathematical discrepancies into structured root-cause physical reports:
1. **Time-Series Residual**: Residual error ($e = I_{\text{user}} - I_{\text{forecast}}$) and percentage drift.
2. **Semiconductor Degradation Mechanism**: Identifies Impact Ionization, SRH Trap Recombination, Gate Oxide Charge Trapping, or Thermal Runaway.
3. **Flight Qualification Verdict**: Actionable recommendation (`PASS` / `HOLD` / `REJECT`).

---

## 7. Python Programmatic Usage

```python
import urllib.request
import json

# 1. Check System Health
with urllib.request.urlopen("http://localhost:5000/api/health") as resp:
    print(json.loads(resp.read().decode("utf-8")))

# 2. Run Dynamic Outlier Detection
payload = json.dumps({
    "model_type": "breakdown",
    "component_id": "NASA-DUT-09",
    "curve": {
        "x": [2.0, 3.5, 4.8, 5.2],
        "y": [0.005, 0.08, 5.2, 85.0]
    }
}).encode("utf-8")

req = urllib.request.Request(
    "http://localhost:5000/api/anomaly/detect",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode("utf-8"))
    print("Verdict:", result["anomaly"]["decision"])
    print("Combined Score:", result["anomaly"]["combined_score"])
```

---

## 8. Resilience and Fallback Modes

- **Zero-Dependency Fallback**: If external APIs are unreachable, the engine utilizes the built-in offline semiconductor physics expert system with 0% downtime.
- **Graceful ML Degradation**: If scikit-learn is unavailable, the system executes robust Mahalanobis/IQR statistical anomaly estimators.
