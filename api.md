# 🌐 SIH26170 - REST API & Architecture Documentation
### Semiconductor Stress Screening, ML Inference & AI Explainability Engine
**Project**: SIH26170 • Team SIT Pune (Smart India Hackathon 2026)

---

## 📑 Table of Contents
1. [Overview & Architecture](#1-overview--architecture)
2. [Base URL & Authentication](#2-base-url--authentication)
3. [REST API Endpoints](#3-rest-api-endpoints)
   - [GET /api/health](#get-apihealth)
   - [GET /api/models](#get-apimodels)
   - [GET /api/dataset-sample](#get-apidataset-sample)
   - [POST /api/pipeline/run](#post-apipipelinerun)
   - [POST /api/chat](#post-apichat)
   - [GET /api/screenings](#get-apiscreenings)
   - [GET /api/screenings/<id>](#get-apiscreeningsid)
4. [Auto-Scaling & Normalization Engine](#4-auto-scaling--normalization-engine)
5. [AI Explainability & LLM Integration (Groq Llama 3.3)](#5-ai-explainability--llm-integration-groq-llama-33)
6. [Python Programmatic API Reference](#6-python-programmatic-api-reference)
7. [Error Handling & High-Availability Fallback](#7-error-handling--high-availability-fallback)

---

## 1. Overview & Architecture

The SIH26170 Backend API serves as the orchestration layer between:
- **Client Frontend Dashboard** (`frontend/`)
- **Physics-Informed ML Models** (`models/`)
- **Feature Auto-Scaler Engine** (`backend/scaler.py`)
- **Groq Llama 3.3 AI Explainability Service** (`models/chatbot.py`)
- **SQLite Screening History Database** (`backend/data/screening.db`)

```
                          CLIENT (Frontend / CLI / Notebooks)
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │    HTTP REST Server (backend/app.py)   │
                      │     Port 5000 • Python Standard Lib    │
                      └───────────────────┬────────────────────┘
                                          │
                                          ▼
                      ┌────────────────────────────────────────┐
                      │ Master Screening Pipeline (pipeline.py)│
                      └───────┬────────────────────────┬───────┘
                              │                        │
            ┌─────────────────┴────────┐   ┌───────────┴────────────────┐
            ▼                          ▼   ▼                            ▼
  ┌──────────────────┐   ┌──────────────────┐   ┌───────────────────────────┐
  │ Feature Scaler   │   │ ML Model Engine  │   │ Groq AI Explainer         │
  │ (scaler.py)      │   │ (model_engine.py)│   │ (models/chatbot.py)       │
  │ Z-score standard │   │ Scaled Inference │   │ Llama 3.3 70B Versatile   │
  └──────────────────┘   └──────────────────┘   └─────────────┬─────────────┘
                                                              │
                                                              ▼
                                                ┌───────────────────────────┐
                                                │ SQLite Database           │
                                                │ (data/screening.db)       │
                                                └───────────────────────────┘
```

---

## 2. Base URL & Authentication

- **Base URL**: `http://localhost:5000` (or configured host/port)
- **Content-Type**: `application/json`
- **Authentication**: None required for local screening endpoints.
- **AI Keys**: Groq (`GROQ_API_KEY`) and Gemini (`GEMINI_API_KEY`) keys are loaded automatically from `.env` on startup.

---

## 3. REST API Endpoints

### `GET /api/health`
Checks server status, database connection, and AI LLM engine status.

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
Returns metadata, physics definitions, input/output parameters, and operating ranges for all supported models.

**Example Request:**
```bash
curl -X GET http://localhost:5000/api/models
```

**Example Response:**
```json
{
  "models": {
    "breakdown": {
      "name": "Breakdown Model",
      "input_param": "Collector-Emitter Voltage",
      "input_unit": "V",
      "output_param": "Leakage Current",
      "output_unit": "A",
      "typical_input_range": [0.0, 650.0],
      "typical_output_range": [1e-9, 0.0001],
      "description": "Models collector-emitter leakage current across applied collector-emitter voltage."
    },
    "leakage": {
      "name": "Leakage IV Model",
      "input_param": "Applied Voltage",
      "input_unit": "V",
      "output_param": "Leakage Current",
      "output_unit": "A",
      "typical_input_range": [0.0, 50.0],
      "typical_output_range": [1e-9, 1e-05],
      "description": "Models reverse leakage current as a function of applied bias voltage."
    },
    "turnon": {
      "name": "Turn-On Model",
      "input_param": "Gate Voltage",
      "input_unit": "V",
      "output_param": "Collector Current",
      "output_unit": "A",
      "typical_input_range": [0.0, 15.0],
      "typical_output_range": [0.0, 30.0],
      "description": "Models IGBT transfer characteristics (Gate Voltage vs Collector Current)."
    }
  }
}
```

---

### `GET /api/dataset-sample`
Returns sampled $(X, Y)$ coordinate points from the underlying NASA laboratory CSV datasets (`final_data/dataset/*.csv`) for rendering scatterplots.

**Query Parameters:**
- `model` *(required)*: `breakdown`, `leakage`, or `turnon`.
- `limit` *(optional, default=100)*: Number of points to sample (max=500).

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/dataset-sample?model=breakdown&limit=5"
```

**Example Response:**
```json
{
  "model_type": "breakdown",
  "count": 5,
  "points": [
    { "x": 2.020181, "y": 5.885971e-09 },
    { "x": 10.052814, "y": 7.420194e-09 },
    { "x": 50.192847, "y": 1.250194e-08 },
    { "x": 300.49102, "y": 3.850194e-08 },
    { "x": 550.18274, "y": 3.871029e-06 }
  ]
}
```

---

### `POST /api/pipeline/run`
**The Master Screening Endpoint**. Takes an unscaled, raw physical measurement, automatically standardizes the feature, performs ML regression inference, inverse-transforms the output to physical units, computes mathematical discrepancy metrics ($\Delta, \%\Delta, \text{ratio}$), generates a 3-point Groq AI failure explanation, and persists the record to SQLite.

**Request Body:**
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `model_type` | string | Yes | `breakdown`, `leakage`, or `turnon` |
| `raw_input` | float | Yes | Raw, unscaled test voltage (e.g. `550.0` V) |
| `user_said_output` | float | No | Observed measured current from test bench (e.g. `1.25e-5` A) |
| `component_id` | string | No | Serial/batch ID (default: `"DUT-01"`) |
| `use_ai` | bool | No | Enable LLM generative explainability (default: `true`) |

**Example Request:**
```bash
curl -X POST http://localhost:5000/api/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "breakdown",
    "raw_input": 550.0,
    "user_said_output": 1.25e-5,
    "component_id": "NASA-IGBT-Part-12",
    "use_ai": true
  }'
```

**Example Response:**
```json
{
  "screening_id": 1,
  "component_id": "NASA-IGBT-Part-12",
  "model_type": "breakdown",
  "model_name": "Breakdown Model",
  "raw_input": 550.0,
  "input_unit": "V",
  "scaled_input": 546.447,
  "scaled_output": 403.886,
  "physical_output": 0.04341,
  "output_unit": "A",
  "user_said_output": 1.25e-5,
  "discrepancy": {
    "delta": -0.04339,
    "pct_diff": -99.97,
    "ratio": 0.00028,
    "direction": "LOWER",
    "risk_decision": "HOLD",
    "severity": "MODERATE",
    "physics_causes": [
      "Model over-estimation at sub-breakdown voltage or superior die quality with lower defect density.",
      "Incomplete contact formation during burn-in test probing."
    ],
    "recommendations": [
      "Verify instrument sensitivity threshold (femto-ammeter vs standard SMU).",
      "Re-screen at elevated junction temperature (125°C) to accelerate thermal carrier generation."
    ]
  },
  "chatbot_explanation": "**Screening Verdict: 🟡 HOLD** (`NASA-IGBT-Part-12` • Breakdown Model)\n\n1. **Deviation**: `-99.97%` drift (0.00x baseline). Observed output is LOWER than model prediction.\n2. **Physics Cause**: Model over-estimation at sub-breakdown voltage or superior die quality.\n3. **Next Action**: Verify instrument sensitivity threshold and re-screen at 125°C.",
  "timestamp": "2026-08-29T13:45:00.000000"
}
```

---

### `POST /api/chat`
Conversational endpoint for asking semiconductor physics, ML model dynamics, or screening criteria questions.

**Request Body:**
```json
{
  "message": "Why does leakage current increase exponentially near breakdown voltage?"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Why does leakage current increase exponentially near breakdown voltage?"}'
```

**Example Response:**
```json
{
  "query": "Why does leakage current increase exponentially near breakdown voltage?",
  "reply": "Near breakdown voltage ($V_{BR}$), the internal electric field in the space-charge region exceeds the critical field ($E > E_{crit}$). Carriers acquire sufficient kinetic energy to knock valence electrons into the conduction band via impact ionization, creating an exponential avalanche multiplication of electron-hole pairs.",
  "provider": "groq",
  "model": "llama-3.3-70b-versatile"
}
```

---

### `GET /api/screenings`
Retrieves past component screening transactions from the SQLite database.

**Query Parameters:**
- `limit` *(optional, default=50)*: Number of past records to return.
- `model` *(optional)*: Filter by `breakdown`, `leakage`, or `turnon`.

**Example Response:**
```json
{
  "total": 12,
  "screenings": [
    {
      "id": 1,
      "component_id": "NASA-IGBT-Part-12",
      "model_type": "breakdown",
      "raw_input": 550.0,
      "scaled_input": 546.447,
      "physical_output": 0.04341,
      "user_said_output": 1.25e-5,
      "pct_diff": -99.97,
      "risk_decision": "HOLD",
      "timestamp": "2026-08-29 13:45:00"
    }
  ]
}
```

---

## 4. Auto-Scaling & Normalization Engine

User inputs from physical laboratory instruments are provided in raw physical units (e.g. `550.0 V`). The backend handles scaling transparently:

### Formulas:
$$\text{Feature Standardization: } X_{\text{scaled}} = \frac{X_{\text{raw}} - \mu_x}{\sigma_x}$$
$$\text{Scaled Forward Model: } Y_{\text{scaled}} = w \cdot X_{\text{scaled}} + b$$
$$\text{Target Inverse Scaling: } Y_{\text{phys}} = Y_{\text{scaled}} \cdot \sigma_y + \mu_y$$

### Calibrated Calibration Parameters (NASA Dataset):
| Model | Mean $X$ ($\mu_x$) | Std $X$ ($\sigma_x$) | Mean $Y$ ($\mu_y$) | Std $Y$ ($\sigma_y$) | Weight ($w$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Breakdown** | `3.883881` | `0.999395` | `7.1072e-5` | `1.0731e-4` | `0.739114` |
| **Leakage IV** | `301.3095` | `173.3395` | `1.8449e-6` | `1.3856e-6` | `0.974888` |
| **Turn-On** | `3.883881` | `0.999395` | `7.1072e-5` | `1.0731e-4` | `0.739114` |

---

## 5. AI Explainability & LLM Integration (Groq Llama 3.3)

The AI Diagnostic Chatbot uses **Groq's Llama 3.3 70B Versatile** model (`llama-3.3-70b-versatile`) via direct HTTP REST API calls.

### Prompt Structuring:
Prompts are structured to enforce **concise, direct, 3-point outputs strictly under 100 words**:
1. **Deviation Summary**: Quantitative drift percentage and ratio relative to baseline.
2. **Physics Cause**: Primary semiconductor degradation mechanism (e.g. Avalanche multiplication, Shockley-Read-Hall recombination, oxide charge trapping $\Delta V_{th}$, or solder fatigue).
3. **Screening Action**: Decision (🟢 PASS / 🟡 HOLD / 🔴 REJECT) and immediate next validation test step.

---

## 6. Python Programmatic API Reference

You can call the screening pipeline directly in Python scripts or Jupyter Notebooks:

```python
from backend.pipeline import ScreeningPipeline

pipeline = ScreeningPipeline()

# Process component measurement
result = pipeline.process_screening(
    model_type="breakdown",
    raw_input=550.0,
    user_said_output=1.25e-5,
    component_id="NASA-IGBT-Part-12"
)

print("Verdict:", result["discrepancy"]["risk_decision"])
print("Explanation:\n", result["chatbot_explanation"])
```

Or invoke the AI Chatbot directly:
```python
from models.chatbot import SemiconductorChatbot

bot = SemiconductorChatbot()
reply = bot.chat("Explain the difference between Fowler-Nordheim tunneling and Poole-Frenkel emission.")
print(reply)
```

---

## 7. Error Handling & High-Availability Fallback

The API guarantees **100% uptime and resilience**:
- **Zero External PIP Dependencies**: Standard library `urllib.request` and `http.server` ensure the server starts anywhere without `pip install` failures.
- **Graceful AI Fallback**: If Groq API experiences rate limits, network timeouts, or missing keys, the system automatically falls back to its built-in rule-based physics engine with zero downtime and zero user-facing errors.
- **Standard Error Schema**:
  ```json
  {
    "error": "Descriptive error message",
    "status": 400
  }
  ```
