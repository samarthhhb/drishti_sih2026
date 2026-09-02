#!/usr/bin/env python3
"""
SIH26170 - Backend Master Screening Pipeline & Chatbot Orchestrator
=============================================================================
Coordinates the complete end-to-end flow:
1. Intake user input (and optional observed user output Y_user).
2. Apply MinMaxScaler [0, 1] normalization.
3. Generate output from ML Model.
4. Explain model dynamics & discrepancy using the AI Chatbot.
5. Persist the complete record and diagnosis into the SQLite Database.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.model_engine import ModelEngine
from backend.database import ScreeningDatabase
from models.chatbot import SemiconductorChatbot, DiscrepancyAnalyzer


class ScreeningPipeline:
    """
    Master backend controller managing communication between:
    User Input -> MinMaxScaler -> ML Model Engine -> Chatbot Explainer -> SQLite DB.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        ai_provider: str = "auto",
        api_key: Optional[str] = None
    ):
        self.model_engine = ModelEngine()
        self.database = ScreeningDatabase(db_path=db_path)
        self.chatbot = SemiconductorChatbot(provider=ai_provider, api_key=api_key)

    def process_screening(
        self,
        model_type: str,
        raw_input: float,
        user_said_output: Optional[float] = None,
        component_id: str = "DUT-01",
        time_minutes: Optional[float] = None,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Time-Series & MinMaxScaler screening pipeline:
        1. Takes user input X and time_minutes.
        2. Evaluates GBR time-series regression model with normalization.
        3. Computes discrepancy, residuals, and generates physics explanation.
        4. Saves record into SQLite DB.
        """
        # Step 1: Direct Time-Series & Model Inference
        pred = self.model_engine.predict(model_type, raw_input, time_minutes=time_minutes)
        physical_y_model = pred["physical_output"]
        scaled_x = pred["scaled_input"]
        scaled_y = pred["scaled_output"]

        # Step 2: Discrepancy & Chatbot Explanation
        t_stamp = int(time_minutes) if time_minutes is not None else 100110

        if user_said_output is not None:
            diag = self.chatbot.explain_discrepancy(
                model_type=model_type,
                x_input=raw_input,
                y_model=physical_y_model,
                y_user=user_said_output,
                component_id=component_id,
                use_ai=use_ai
            )
            explanation = diag["final_explanation"]
            risk_decision = diag["risk_decision"]
            severity = diag["severity"]
            delta = diag["delta"]
            pct_diff = diag["pct_diff"]
            ratio = diag["ratio"]
            direction = diag["direction"]
            physics_causes = diag["physics_causes"]
            recommendations = diag["recommendations"]

            res_val = round(user_said_output - physical_y_model, 2)
            denom = physical_y_model if abs(physical_y_model) > 1e-9 else 1e-9
            drift_pct = round((res_val / denom) * 100.0, 1)

            # Trend & Prediction Status
            trend = "increasing" if (res_val > 0.5 or t_stamp >= 60000) else ("decreasing" if res_val < -0.5 else "stable")
            if res_val < -1.0:
                pred_status = "underprediction"
                short_explanation = f"Model significantly underpredicted the observed leakage current (drift: {drift_pct:+.1f}%)."
            elif res_val > 1.0:
                pred_status = "overprediction"
                short_explanation = f"Observed leakage current is elevated above baseline forecast by {abs(res_val):.2f} uA ({drift_pct:+.1f}%)."
            else:
                pred_status = "nominal"
                short_explanation = "Observed telemetry matches expected degradation trajectory within calibrated tolerance."

        else:
            delta = None
            pct_diff = None
            ratio = None
            direction = "NOMINAL_PREDICTION"
            risk_decision = "PASS"
            severity = "LOW"
            res_val = 0.0
            drift_pct = 0.0
            trend = "stable"
            pred_status = "nominal"
            short_explanation = "Nominal operation predicted by ML model."
            physics_causes = [
                f"Nominal operation predicted by ML model for input {raw_input} {pred['input_unit']}."
            ]
            recommendations = [
                "Verify sensor telemetry matches baseline prediction."
            ]
            explanation = (
                f"### Model Dynamics & Prediction Summary\n"
                f"- **Component ID**: `{component_id}`\n"
                f"- **Model**: **{pred['model_name']}**\n"
                f"- **Input**: `{DiscrepancyAnalyzer.format_val(raw_input, pred['input_unit'])}` (MinMax Scaled: `{scaled_x:.4f}`)\n"
                f"- **Predicted Output**: `{DiscrepancyAnalyzer.format_val(physical_y_model, pred['output_unit'])}` (MinMax Scaled: `{scaled_y:.4f}`)\n\n"
                f"**Dynamics Overview**:\n"
                f"The component is evaluated under standard operational bounds."
            )

        monitor_obj = {
            "timestamp": t_stamp,
            "actual_value_uA": round(user_said_output, 2) if user_said_output is not None else None,
            "predicted_value_uA": round(physical_y_model, 2),
            "residual_uA": res_val,
            "drift_percentage": drift_pct,
            "trend": trend,
            "prediction_status": pred_status,
            "explanation": short_explanation
        }

        # Step 3: Persist transaction into SQLite Database
        record_data = {
            "component_id": component_id,
            "model_type": pred["model_type"],
            "raw_input": raw_input,
            "scaled_input": scaled_x,
            "scaled_output": scaled_y,
            "physical_output": physical_y_model,
            "user_said_output": user_said_output,
            "delta": delta,
            "pct_diff": pct_diff,
            "ratio": ratio,
            "direction": direction,
            "risk_decision": risk_decision,
            "severity": severity,
            "physics_causes": physics_causes,
            "recommendations": recommendations,
            "chatbot_explanation": explanation,
            "ai_provider": self.chatbot.api_client.provider
        }
        
        record_id = self.database.save_screening(record_data)

        # Step 4: Return complete response payload
        return {
            "record_id": record_id,
            "component_id": component_id,
            "model_type": pred["model_type"],
            "model_name": pred["model_name"],
            "input_feature": pred["input_feature"],
            "input_unit": pred["input_unit"],
            "output_target": pred["output_target"],
            "output_unit": pred["output_unit"],
            "raw_input": raw_input,
            "scaled_input": scaled_x,
            "scaled_output": scaled_y,
            "norm_input": scaled_x,
            "norm_output": scaled_y,
            "physical_output": physical_y_model,
            "user_said_output": user_said_output,
            # Structured Time-Series Monitor Schema
            "timestamp": t_stamp,
            "actual_value_uA": monitor_obj["actual_value_uA"],
            "predicted_value_uA": monitor_obj["predicted_value_uA"],
            "residual_uA": monitor_obj["residual_uA"],
            "drift_percentage": monitor_obj["drift_percentage"],
            "trend": monitor_obj["trend"],
            "prediction_status": monitor_obj["prediction_status"],
            "explanation": monitor_obj["explanation"],
            "monitor": monitor_obj,
            "time_series_monitor": monitor_obj,
            "discrepancy": {
                "delta": delta,
                "pct_diff": pct_diff,
                "residual_uA": res_val,
                "drift_percentage": drift_pct,
                "actual_value_uA": monitor_obj["actual_value_uA"],
                "predicted_value_uA": monitor_obj["predicted_value_uA"],
                "trend": trend,
                "prediction_status": pred_status,
                "ratio": ratio,
                "direction": direction,
                "risk_decision": risk_decision,
                "severity": severity
            },
            "physics_causes": physics_causes,
            "recommendations": recommendations,
            "chatbot_explanation": explanation,
            "ai_provider": self.chatbot.api_client.provider,
            "minmax_bounds": pred.get("minmax_bounds", {})
        }

    def chat(self, user_message: str, session_id: str = "default_session") -> Dict[str, Any]:
        """Conversational chat interface with automatic persistence to SQLite database."""
        self.database.save_chat_message(session_id, "user", user_message)
        reply = self.chatbot.chat(user_message)
        self.database.save_chat_message(session_id, "assistant", reply)
        return {
            "session_id": session_id,
            "reply": reply,
            "provider": self.chatbot.api_client.provider
        }


if __name__ == "__main__":
    print("Testing master screening pipeline...")
    pipeline = ScreeningPipeline()
    res = pipeline.process_screening(
        model_type="breakdown",
        raw_input=550.0,
        user_said_output=1.25e-5,
        component_id="NASA-IGBT-TEST-01"
    )
    print(f"Record ID: {res['record_id']}")
    print(f"Input: {res['raw_input']} V (MinMax Scaled: {res['scaled_input']})")
    print(f"Model Output: {res['physical_output']:.4e} A (MinMax Scaled: {res['scaled_output']})")
    print(f"User Output: {res['user_said_output']:.4e} A")
    print(f"Screening Decision: {res['discrepancy']['risk_decision']}")
    print("\nPipeline executed successfully!")
