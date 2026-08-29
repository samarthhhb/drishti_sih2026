# SIH26170 - Quick Start and System Walkthrough Guide
### AI-Driven Anomaly Detection in Component Burn-In and Screening
**Team Drishti • Symbiosis Institute of Technology, Pune • Smart India Hackathon 2024**

---

## 1. System Overview

Traditional semiconductor screening uses fixed pass or fail limits. However, components can pass static datasheet limits while showing abnormal degradation drift relative to the healthy population.

This platform provides a complete predictive screening and explainability system:
1. **Frontend**: Clean dashboard and split-screen model layout with live time-series plots, interactive point placement, and in-toolbar sample data views.
2. **Backend**: Automatic feature standardization, gradient boosted regression time-series forecasting, and persistent SQLite transaction logging.
3. **AI Explainability**: Powered by Groq Llama 3.3 with local physics rule fallback, generating structured failure analyses and PASS, HOLD, or REJECT verdicts.

---

## 2. Prerequisites

- Python 3.9 or higher.
- Modern web browser (Chrome, Brave, Firefox, Edge, Safari).
- Zero mandatory external pip packages required for basic server startup.

---

## 3. How to Start the System

### Option A: Run the Web Interface (Recommended)

1. Open your terminal in the project directory:
```bash
cd "/Users/samarth/Documents/SIH 26"
```

2. Start the local server:
```bash
python3 backend/app.py --port 5000
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

---

### Option B: Run the Terminal CLI Assistant

If you prefer testing directly in the terminal:
```bash
python3 models/chatbot.py
```

Available commands:
- `explain`: Run the step-by-step discrepancy wizard.
- `preset`: Test pre-configured aging cases.
- `models`: Inspect feature definitions and operating ranges.
- Or type any natural language question to ask the failure physics assistant.

---

## 4. User Interface Architecture

```
+-----------------------------------------------------------------------------------+
| [SIH26170 Drishti]        [Home] [Breakdown] [Leakage IV] [Turn-On] [About Us]    |
+-----------------------------------------------------------------------------------+
| DASHBOARD OVERVIEW: 4 Executive Cards                                             |
| [ Breakdown Model ]   [ Leakage IV ]   [ Turn-On Model ]   [ About Us ]           |
+-----------------------------------------------------------------------------------+
| SPLIT-SCREEN MODEL VIEW:                                                          |
| ┌─────────────────────────────────────┐ ┌──────────────────────────────────────┐ |
| │ LEFT: Controls and Verdict          │ │ RIGHT: AI and Telemetry Graphs       │ |
| │ • Input Voltage (V) and Slider      │ │ 1. AI Failure Physics (Top)          │ |
| │ • Elapsed Time Scrubber (min)       │ │    (Deviation, Physics, Actions)     │ |
| │   [Auto-Play] [+5h Step] [Reset]    │ │ 2. Leakage vs Time Telemetry         │ |
| │ • Measured Current (uA) and Slider  │ │    Toolbar: [Move] [Pan] [Sample]... │ |
| │ • Quick Presets                     │ │ 3. Operating Voltage vs Time         │ |
| │ • [ Run Screening & Explain ]       │ │    Toolbar: [Sample Curve] [Zoom]... │ |
| │ • Verdict Card: PASS / HOLD / REJECT│ │                                      │ |
| └─────────────────────────────────────┘ └──────────────────────────────────────┘ |
+-----------------------------------------------------------------------------------+
```

---

## 5. Operational Workflow

1. **Select a Model**: From the Dashboard, select **Breakdown Model**, **Leakage IV**, or **Turn-On Model**.
2. **Configure Test Conditions**:
   - Adjust the **Input Voltage** directly or with the slider.
   - Use the **Elapsed Time Scrubber** to inspect aging from 0 to 113,700 minutes, or click **Auto-Play** to watch the degradation simulation.
   - Enter or slide the **Measured Current** in microAmpere.
3. **Execute Screening**:
   - Click **Run Screening & Explain** (or pick a preset like Aged, Pristine, or Runaway).
   - The engine standardizes inputs, evaluates the gradient boosted regression model, and updates the **Screening Verdict**:
     - **PASS**: Normal baseline operation within safe limits.
     - **HOLD**: Moderate drift; requires quarantine and secondary thermal curve analysis.
     - **REJECT**: High latent defect risk or premature breakdown detected.
4. **Review AI Explainability and Telemetry Graphs**:
   - Read the structured 3-point failure physics diagnosis at the top of the right column.
   - Inspect the **Leakage Current vs Time** forecast and the **Operating Voltage Stress** trajectory.
   - Click **Sample Data** or **Sample Curve** directly in the chart toolbars to inspect underlying laboratory measurements.
5. **Ask Follow-Up Questions**:
   - Type questions into the interactive **Ask AI** bar located inside the explainability panel.

---

## 6. Team Members and Student IDs

**Symbiosis Institute of Technology, Pune**

| Number | Member Name | Student ID | Domain |
| :---: | :--- | :--- | :--- |
| 1 | **Samarth Buchake** | 25070126151 | Machine Learning and Fullstack Architecture |
| 2 | **Vibhuti Patil** | 25070126193 | Physics of Failure and Semiconductor Models |
| 3 | **Maitreyee Kulkarni** | 24070123058 | Data Preprocessing and Statistical Calibration |
| 4 | **Varija Korti** | 24070123165 | Time-Series Regression and Drift Prediction |
| 5 | **Kaushal Sidhpura** | 25070127093 | Dynamic Outlier Detection and Anomaly Scoring |
| 6 | **Prachi Hirve** | 26070126090 | Explainability Engine and Quality Diagnostics |

