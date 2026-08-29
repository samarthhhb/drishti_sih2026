# SIH26170 - REST API and Architecture Reference
### Semiconductor Stress Screening, Time-Series Inference, and AI Explainability Engine
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
   - [POST /api/chat](#post-apichat)
   - [GET /api/screenings](#get-apiscreenings)
   - [GET /api/screenings/{id}](#get-apiscreeningsid)
4. [Feature Standardization and Scaling](#4-feature-standardization-and-scaling)
5. [AI Explainability Engine](#5-ai-explainability-engine)
6. [Python Programmatic Usage](#6-python-programmatic-usage)
7. [Resilience and Fallback Modes](#7-resilience-and-fallback-modes)

---

## 1. Architecture Overview

The backend API coordinates communication between the browser dashboard, time-series machine learning models, statistical scaling layers, the Groq Llama 3.3 explanation service, and persistent database storage:

```
  CLIENT (Web Browser, CLI, or Automated Test Bench)
  │
  ▼
  ┌────────────────────────────────────────────────────────┐
  │         HTTP REST Server (backend/app.py)              │
  │         Port 5000 • Python Standard Library            │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │        Master Screening Pipeline (pipeline.py)         │
  └───────────┬───────────────────────────────┬────────────┘
              │                               │
  ┌───────────┴──────────────┐   ┌────────────┴───────────────┐
  ▼                          ▼   ▼                            ▼
┌──────────────────┐ ┌──────────────────┐ ┌───────────────────────────┐
│  MinMax Scaler   │ │  Time-Series GBR │ │     Groq AI Explainer     │
│   (scaler.py)    │ │(model_engine.py) │ │    (models/chatbot.py)    │
│  [0, 1] Normal.  │ │ Degr. Forecast   │ │  Llama 3.3 70B Versatile  │
└──────────────────┘ └──────────────────┘ └─────────────┬─────────────┘
                                                        │
                                                        ▼
                                          ┌───────────────────────────┐
                                          │  SQLite Audit Database    │
                                          │    (data/screening.db)    │
                                          └───────────────────────────┘
```

---

## 2. Base URL and Protocol

- **Base URL**: `http://localhost:5000`
- **Default Content Type**: `application/json`
- **Authentication**: None required for local screening endpoints.
- **Environment Keys**: `GROQ_API_KEY` is loaded from `.env` on startup. If unavailable, the engine falls back to deterministic physics explanations automatically.

---

## 3. REST API Endpoints

### `GET /api/health`
Returns system status, active database path, and language model provider configuration.

**Example Request:**
```bash
curl -X GET http://localhost:5000/api/health
```

**Example Response:**
```json
{
  "status": "healthy",
  "service": "SIH26170 Semiconductor Screening API",
  "version": "1.0.0",
  "ai_provider": "groq",
  "ai_model": "llama-3.3-70b-versatile",
  "groq_key_detected": true,
  "database": "backend/data/screening.db"
}
```

---

### `GET /api/models`
Returns metadata, physics definitions, input and output units, and operating bounds for supported semiconductor models.

**Example Request:**
```bash
curl -X GET http://localhost:5000/api/models
```

**Example Response:**
```json
{
  "models": {
    "breakdown": {
      "name": "Time-Series & Breakdown Model",
      "input_param": "Collector-Emitter Voltage",
      "input_unit": "V",
      "output_param": "Leakage Current",
      "output_unit": "microAmpere",
      "typical_input_range": [0.0, 650.0],
      "typical_output_range": [0.01, 150.0],
      "description": "Models chronological collector-emitter degradation and high-voltage breakdown."
    },
    "leakage": {
      "name": "Applied Voltage vs Leakage IV",
      "input_param": "Applied Stress Voltage",
      "input_unit": "V",
      "output_param": "Reverse Leakage Current",
      "output_unit": "microAmpere",
      "typical_input_range": [0.0, 600.0],
      "typical_output_range": [0.01, 120.0],
      "description": "Evaluates reverse junction leakage current and thermal carrier generation."
    },
    "turnon": {
      "name": "Gate Voltage vs Collector Current",
      "input_param": "Gate-Emitter Voltage",
      "input_unit": "V",
      "output_param": "Collector Current",
      "output_unit": "microAmpere",
      "typical_input_range": [0.0, 15.0],
      "typical_output_range": [0.01, 100.0],
      "description": "Analyzes channel conduction threshold shifts and gate dielectric integrity."
    }
  }
}
```

---

### `GET /api/timeseries-data`
Returns sequential chronological points formatted for chart rendering, including historical training data, future ground truth, model forecast, and voltage trajectories.

**Query Parameters:**
- `model` (optional, default=`breakdown`): `breakdown`, `leakage`, or `turnon`.
- `limit` (optional, default=120): Number of time points to return.

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/timeseries-data?model=breakdown&limit=5"
```

**Example Response:**
```json
{
  "model_type": "breakdown",
  "total_points": 5,
  "voltage_points": [
    { "x": 0.0, "y": 550.0 },
    { "x": 30.0, "y": 550.0 }
  ],
  "train_points": [
    { "x": 0.0, "y": 0.01 },
    { "x": 30.0, "y": 0.012 }
  ],
  "test_actual_points": [
    { "x": 90960.0, "y": 14.2 },
    { "x": 90990.0, "y": 14.5 }
  ],
  "test_predicted_points": [
    { "x": 90960.0, "y": 13.9 },
    { "x": 90990.0, "y": 14.1 }
  ],
  "metrics": {
    "train_rows": 3032,
    "test_rows": 758,
    "r2_score": 0.989,
    "mae_microampere": 1.87
  }
}
```

---

### `GET /api/dataset-sample`
Returns sampled experimental laboratory points from the characterization CSV dataset for rendering scatterplots.

**Query Parameters:**
- `model` (optional, default=`breakdown`): `breakdown`, `leakage`, or `turnon`.
- `limit` (optional, default=100): Number of points to sample.

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/dataset-sample?model=breakdown&limit=3"
```

**Example Response:**
```json
{
  "model_type": "breakdown",
  "count": 3,
  "points": [
    { "x": 10.0, "y": 0.01 },
    { "x": 300.0, "y": 0.08 },
    { "x": 550.0, "y": 12.5 }
  ]
}
```

---

### `POST /api/pipeline/run`
**Primary Screening Execution Endpoint**. Receives test bench inputs, standardizes features, executes regression forecasting, calculates mathematical discrepancies, produces AI failure physics explanations, and stores the audit record.

**Request Body:**
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `model_type` | string | Yes | `breakdown`, `leakage`, or `turnon` |
| `raw_input` | float | Yes | Applied voltage (in Volts) |
| `time_minutes` | float | No | Elapsed burn-in time (default: `90960.0`) |
| `user_said_output` | float | No | Measured current from test bench (in microAmpere) |
| `use_ai` | boolean | No | Enable generative failure explanation (default: `true`) |

**Example Request:**
```bash
curl -X POST http://localhost:5000/api/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "breakdown",
    "raw_input": 550.0,
    "time_minutes": 90960.0,
    "user_said_output": 12.50,
    "use_ai": true
  }'
```

**Example Response:**
```json
{
  "screening_id": 1,
  "model_type": "breakdown",
  "model_name": "Time-Series & Breakdown Model",
  "raw_input": 550.0,
  "input_unit": "V",
  "time_minutes": 90960.0,
  "scaled_input": 0.846,
  "physical_output": 0.01,
  "output_unit": "microAmpere",
  "user_said_output": 12.50,
  "discrepancy": {
    "delta": 12.49,
    "pct_diff": 99.92,
    "ratio": 1250.0,
    "direction": "HIGHER",
    "risk_decision": "PASS",
    "severity": "NORMAL"
  },
  "chatbot_explanation": "Screening Verdict: PASS\n\n1. Deviation: Measured current matches normal operating envelope within calibrated limits.\n2. Physics Cause: Standard thermal generation with negligible dielectric degradation.\n3. Next Action: Proceed to subsequent screening stage.",
  "timestamp": "2026-08-30T03:00:00.000000"
}
```

---

### `POST /api/chat`
Interactive conversational endpoint for asking physics, degradation mechanism, or screening criteria questions.

**Request Body:**
```json
{
  "message": "Why does leakage current increase under high temperature burn-in?"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Why does leakage current increase under high temperature burn-in?"}'
```

**Example Response:**
```json
{
  "query": "Why does leakage current increase under high temperature burn-in?",
  "reply": "Elevated thermal stress at 125°C increases intrinsic carrier concentration exponentially via thermal generation. Trapped charges in gate and field oxides become active, creating additional conduction paths that accelerate leakage drift.",
  "provider": "groq",
  "model": "llama-3.3-70b-versatile"
}
```

---

### `GET /api/screenings`
Retrieves past screening transactions from the persistent audit database.

**Query Parameters:**
- `limit` (optional, default=50): Maximum number of records to return.
- `model` (optional): Filter by `breakdown`, `leakage`, or `turnon`.

**Example Response:**
```json
{
  "total": 1,
  "screenings": [
    {
      "id": 1,
      "model_type": "breakdown",
      "raw_input": 550.0,
      "time_minutes": 90960.0,
      "physical_output": 0.01,
      "user_said_output": 12.50,
      "pct_diff": 99.92,
      "risk_decision": "PASS",
      "timestamp": "2026-08-30 03:00:00"
    }
  ]
}
```

---

## 4. Feature Standardization and Scaling

Input voltages and times are normalized internally into the `[0, 1]` interval using calibrated statistics:

$$\text{Normalized Feature: } X_{\text{norm}} = \frac{X_{\text{raw}} - X_{\min}}{X_{\max} - X_{\min}}$$

Output currents are computed in physical units of **microAmpere** ($\mu\text{A}$) to ensure direct compatibility with laboratory test instrumentation.

---

## 5. AI Explainability Engine

Explanations are produced by Groq Llama 3.3 using structured failure physics templates:
1. **Deviation Summary**: Quantitative drift percentage and baseline ratio.
2. **Physics Cause**: Primary semiconductor degradation mechanism (e.g., Avalanche multiplication, Shockley-Read-Hall recombination, oxide trapping, or thermal fatigue).
3. **Screening Action**: Decision (PASS, HOLD, or REJECT) with recommended physical testing action.

---

## 6. Python Programmatic Usage

The pipeline can be executed directly within Python environments:

```python
from backend.pipeline import ScreeningPipeline

pipeline = ScreeningPipeline()

result = pipeline.process_screening(
    model_type="breakdown",
    raw_input=550.0,
    time_minutes=90960.0,
    user_said_output=12.50
)

print("Decision:", result["discrepancy"]["risk_decision"])
print("Explanation:\n", result["chatbot_explanation"])
```

---

## 7. Resilience and Fallback Modes

- **Zero Mandatory Package Dependencies**: Runs directly on the Python standard library.
- **Automatic Fallback**: If external API connections are unavailable, the system switches immediately to local rule-based physics explanations without interrupting screening operations.
- **Consistent Error Structure**:
  ```json
  {
    "error": "Descriptive error message",
    "status": 400
  }
  ```

