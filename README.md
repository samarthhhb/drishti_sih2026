# SIH26170 - AI-Driven Anomaly Detection in Component Burn-In & Screening
## Internal Round Pipeline and Project Description

## Team Members - SIT Pune
1. Samarth Buchake
2. Vibhuti Patil
3. Maitreyee Kulkarni
4. Varija Korti
5. Kaushal Sidhpura
6. Prachi Hirve

Predictive Environmental Stress Screening for Semiconductor Components

### Overview

This project develops an AI-based Predictive Environmental Stress Screening system to detect latent semiconductor defects before conventional failure limits are exceeded.

Traditional screening uses fixed pass/fail limits. Our system additionally learns how components normally behave over time and identifies abnormal drift that may indicate future failure.

⸻

### Problem Statement

A component can remain within its datasheet limits while showing abnormal degradation.

For example:

Lot average leakage current = 10 μA
Component leakage current  = 45 μA
Maximum allowed limit       = 50 μA

The component technically passes, but its behaviour is significantly different from the healthy population.

Our system detects this population-relative abnormality and predicts whether the component is likely to degrade further.

⸻

### Proposed Pipeline

Historical Aging Data
        +
Experimental Measurements
        ↓
Data Preprocessing
        ↓
Feature Engineering
        ↓
Semi-Supervised Learning
        ↓
 ┌───────────────────────┐
 │                       │
 ↓                       ↓
Dynamic Anomaly      Future Drift
Detection            Prediction
 │                       │
 └───────────┬───────────┘
             ↓
      Population Analysis
             ↓
        Risk Assessment
             ↓
     PASS / HOLD / REJECT
             ↓
        Explainability
             ↓
    Physical Validation
             ↓
 Prediction vs Actual Data
             ↓
       Model Refinement

⸻

### Module A — Dynamic Anomaly Detection

An Long Short-Term Memory Autoencoder learns normal component behaviour from healthy and largely unlabeled data.

Time-Series Data
      ↓
Long Short-Term Memory Autoencoder
      ↓
Reconstructed Behaviour
      ↓
Reconstruction Error
      ↓
Dynamic Anomaly Score

This detects components whose value, trajectory or rate of change differs significantly from normal components.

⸻

### Module B — Future Drift Prediction

Early measurements are used to predict a future parameter value.

Initial + Early Measurements
            ↓
Time-Series Regression
            ↓
Predicted Future Value
            ↓
Predicted Drift
            ↓
Safety-Slope Comparison

A component can therefore be flagged before reaching a conventional failure limit.

⸻

Semi-Supervised Learning

Since defective semiconductor samples are difficult to obtain in large quantities, the system uses:

Large Unlabelled Dataset
          +
Small Labelled Dataset
          ↓
Semi-Supervised Learning

This allows the model to learn normal behaviour while still using the limited available defect labels.

⸻

### Risk Assessment

The final decision combines:

* Static engineering limits
* Dynamic anomaly score
* Predicted future value
* Drift slope
* Population deviation
* Thermal behaviour

             Risk Assessment
                    ↓
        ┌───────────┼───────────┐
        ↓           ↓           ↓
      PASS        HOLD       REJECT
     Low Risk   Review      High Risk

⸻

### Explainability

Each decision should provide a clear reason.

Example:

Component: C-104
Decision: HOLD
High dynamic anomaly score
High predicted future drift
Large deviation from healthy population
Main indicators:
• Increasing leakage
• Increasing on-state voltage
• Abnormal temperature-adjusted behaviour

⸻

### Physical Validation

The trained model is ultimately tested using measurements from physical semiconductor components.

Trained Model
     ↓
Physical Measurements
     ↓
Real-Time Prediction
     ↓
PASS / HOLD / REJECT
     ↓
Later Actual Measurements
     ↓
Prediction vs Actual Behaviour

This provides real-world validation rather than relying only on dataset accuracy.

⸻

### Evaluation

Anomaly Detection

* Recall
* False-negative rate
* Precision
* F1-score
* Precision-recall area under the curve

Drift Prediction

* Mean Absolute Error
* Root Mean Squared Error
* Coefficient of determination

Explainability

Identify which parameters caused the warning and why the component was classified as risky.

⸻

### Differentiating Factor

A predictive screening system combining semi-supervised temporal learning, dynamic population-relative anomaly detection, future degradation prediction, explainable risk assessment and physical validation.

The key shift is:

Traditional ESS:
“Has the component crossed the limit?”

Our system:
“Is the component behaving abnormally, where is it heading, and should it be screened before failure?”

⸻

### Expected Outcome

Historical Data
      ↓
AI Training
      ↓
Anomaly Detection
      +
Drift Prediction
      ↓
Risk Assessment
      ↓
PASS / HOLD / REJECT
      ↓
Explainable Report
      ↓
Physical Validation
      ↓
Improved Model

Target Applications: Aerospace, space systems, defense electronics and other high-reliability electronic systems.