# ⚡ SIH26170 - Quick Start & System Walkthrough Guide
### AI-Driven Anomaly Detection in Component Burn-In & Screening
**Team: Dhrishti — Insightful Vision • Symbiosis Institute of Technology (SIT), Pune • SIH 2026**

---

## 1. Project Overview

Traditional semiconductor screening uses fixed pass/fail limits. However, components can pass static datasheet limits while showing abnormal degradation drift relative to the healthy population.

This project provides a **fullstack predictive screening and explainability system**:
1. **Frontend**: Clean Indian Flag-themed dashboard (Landing Page + Split-Screen Model Diagnostics with interactive Scatterplots and Line Charts).
2. **Backend**: Automatic feature standardization for unscaled user inputs, ML model inference, and SQLite transaction logging.
3. **AI Chatbot Explainer**: Powered by **Groq Llama 3.3** (with a zero-dependency offline physics fallback) providing concise 3-point failure diagnostics and **PASS / HOLD / REJECT** screening decisions.

---

## 2. Prerequisites

- **Python 3.8+** installed.
- **Zero mandatory external pip packages required** (all core backend networking, SQLite database, and scalers run purely on the Python standard library).

---

##  3. How to Start the Project

### Option A: Run the Complete Web Application (Recommended)

1. Open your terminal in the project root directory:
   ```bash
   cd "/Users/samarth/Documents/SIH 26"
   ```

2. Start the unified Backend & Frontend server:
   ```bash
   python3 backend/app.py --port 5000
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

---

### Option B: Run the Terminal CLI Chatbot

If you prefer testing directly in the terminal without opening a browser:
```bash
python3 models/chatbot.py
```
**CLI Commands**:
- Type `explain` to launch the step-by-step discrepancy wizard.
- Type `preset` to test pre-configured NASA IGBT aging test cases.
- Type `models` to inspect feature definitions and formulas.
- Or type any natural language question to chat with the AI.

---

### Option C: Run in Jupyter Notebooks

Open any model notebook or [`models/chatbot_demo.ipynb`](file:///Users/samarth/Documents/SIH%2026/models/chatbot_demo.ipynb):
```python
from models.chatbot_helper import explain_discrepancy, chat

# 1. Run discrepancy diagnosis on test measurements
diag = explain_discrepancy(
    model_type="breakdown",
    x_input=550.0,
    y_model=3.87e-6,
    y_user=1.25e-5,
    component_id="NASA-IGBT-Part-12"
)

# 2. Ask conversational questions
chat("Why does leakage current increase with temperature in IGBTs?")
```

---

## 4. User Guide & Interface Walkthrough

```
+-----------------------------------------------------------------------------------+
|  🇮🇳 [SIH26170 SemiconScreen]       [Home] [Breakdown] [Leakage IV] [Turn-On] [About]|
+-----------------------------------------------------------------------------------+
|  LANDING PAGE: 4 Functional Cards                                                 |
|  [ 👥 About Us ]   [ ⚡ Breakdown Model ]   [ 🔍 Leakage IV ]   [ 🔄 Turn-On ]   |
+-----------------------------------------------------------------------------------+
|  SPLIT-SCREEN MODEL VIEW:                                                         |
|  ┌─────────────────────────────────────┐ ┌──────────────────────────────────────┐ |
|  │ LEFT: Model & AI Chatbot            │ │ RIGHT: Data Diagrams & Visuals       │ |
|  │ • Raw Input Voltage (e.g. 550V)     │ │ 1. SCATTERPLOT                       │ |
|  │ • Measured Current (e.g. 1.25e-5 A) │ │    (NASA Dataset + Live Point Marker)│ |
|  │ • [Run Screening & Explain]         │ │ 2. LINE CHART                        │ |
|  │ • Verdict: 🔴 REJECT (Δ: +223.0%)   │ │    (Model Curve + Measured Marker)   │ |
|  │ • 3-Point Physics Explanation       │ │                                      │ |
|  └─────────────────────────────────────┘ └──────────────────────────────────────┘ |
+-----------------------------------------------------------------------------------+
```

### Step-by-Step Flow:
1. **Choose a Model**: From the Home Page, click on **Breakdown Model**, **Leakage IV**, or **Turn-On Model**.
2. **Move & Adjust Graphs Directly According to Your Needs**:
   - **🎯 Click & Drag Directly on Graphs**: Click or drag anywhere on the **Scatterplot** or **Line Chart** canvas to instantly move the test point to that position. The input fields and sliders update in real-time.
   - **🖐️ Pan the View**: Click the `🖐️ Pan View` button in the chart header and drag the chart to slide the axes left, right, up, or down.
   - **🔍 Zoom In / Out**: Use the `🔍+` / `🔍-` buttons or simply scroll your **mouse wheel** on the graph to zoom into specific breakdown knees or sub-threshold regions.
   - **🔄 Reset View**: Click `🔄 Reset` at any time to restore default axis bounds.
   - **🎛️ Real-Time Sliders**: Use the smooth range sliders for Input Voltage (V) and Measured Current (A) to slide values and watch the test point glide across the curves.
3. **Click "Run Screening & Explain"** (or adjust points to auto-trigger):
   - The backend automatically standardizes your raw input.
   - Runs model inference in scaled space and converts predictions back to physical units.
   - The **Groq Llama 3.3 AI Chatbot** analyzes the mathematical gap and generates a concise 3-point failure physics explanation.
   - Assigns a color-coded **Screening Verdict**:
     - 🟢 **PASS**: Normal baseline operation (drift <= 10%).
     - 🟡 **HOLD**: Moderate drift; requires quarantine and secondary 125°C curve trace.
     - 🔴 **REJECT**: High latent defect risk or premature breakdown detected.
4. **Inspect the Visual Diagrams**:
   - **1. Dataset Scatterplot**: Shows where your physical component lies relative to hundreds of actual NASA test bench data points.
   - **2. Model Regression Curve**: Plots the predicted drift curve across the voltage sweep alongside your measured data point.
5. **Ask Follow-Up Questions**:
   - Use the chat box under the explanation to ask the AI questions about failure physics.

---

## 5. API Key Configuration

The system is pre-configured with a **Free Groq API Key** stored in `.env`.

- **Active Model**: Groq `llama-3.3-70b-versatile` (Ultra-fast Llama 3.3 70B).
- **100% Uptime Fallback**: If the network is offline or rate-limited, the system automatically falls back to its built-in physics rule engine without errors.
- **Custom Keys**: To use your own key, update `.env`:
  ```bash
  GROQ_API_KEY="gsk_your_key_here"
  # or
  GEMINI_API_KEY="AIzaSy_your_gemini_key"
  ```

---

## 6. Project Directory Map

```
SIH 26/
├── backend/
│   ├── app.py                # Unified REST API & static web server (port 5000)
│   ├── pipeline.py           # Master screening orchestrator (Input -> Scale -> Model -> Explain -> DB)
│   ├── scaler.py             # Feature & target standardization module
│   ├── model_engine.py       # ML Model inference execution in scaled space
│   ├── database.py           # SQLite database persistence layer
│   └── data/
│       └── screening.db      # SQLite database storing all screening records
│
├── frontend/
│   ├── index.html            # 4-card landing page & split-screen model layout
│   ├── styles.css            # Clean white theme with Indian flag accents
│   └── app.js                # SPA routing, Chart.js diagrams & API communication
│
├── models/
│   ├── chatbot.py            # Core Groq / Gemini AI Chatbot & Discrepancy Engine (CLI)
│   ├── chatbot_helper.py     # Jupyter & Python helper module
│   ├── chatbot_demo.ipynb    # Interactive demo notebook
│   ├── models.md             # Detailed models & semiconductor physics documentation
│   ├── breakdown.ipynb       # Vce vs Ic Breakdown Regression Model
│   ├── leakage.ipynb         # Applied Voltage vs Leakage Current Model
│   └── turnOn.ipynb          # Gate Voltage vs Collector Current Model
│
├── final_data/
│   └── dataset/              # Cleaned NASA IGBT accelerated aging CSV datasets
│       ├── Breakdown.csv
│       ├── LeakageIV.csv
│       └── TurnOn.csv
│
├── .env                      # Environment variables (GROQ_API_KEY)
├── .gitignore                # Git ignore rules protecting .env and database
├── README.md                 # Project description & team details
└── walkthrough.md            # This starter guide
```

---

## 7. Team Details — Team Dhrishti (Insightful Vision)

**SIH26170 — Symbiosis Institute of Technology (SIT), Pune**

| # | Member Name | PRN / Student ID | Role / Specialization |
| :-: | :--- | :--- | :--- |
| 1 | **Samarth Buchake** | `25070126151` |
| 2 | **Vibhuti Patil** | `25070126193` | 
| 3 | **Maitreyee Kulkarni** | `24070123058` | 
| 4 | **Varija Korti** | `24070123165` | 
| 5 | **Kaushal Sidhpura** | `25070127093` | 
| 6 | **Prachi Hirve** | `26070126090` | 
