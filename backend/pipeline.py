#!/usr/bin/env python3
"""
SIH26170 - Backend Master Screening Pipeline & Chatbot Orchestrator
=============================================================================
Coordinates the complete end-to-end flow:
1. Intake unscaled user input (and optional observed user output Y_user).
2. Deal with unscaled input -> Standardize to X_scaled.
3. Generate output from ML Model -> Inverse scale to physical Y_model.
4. Explain model dynamics & discrepancy using the AI Chatbot.
5. Persist the complete record and diagnosis into the SQLite Database.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is accessible for model & backend imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.scaler import FeatureScaler
from backend.model_engine import ModelEngine
from backend.database import ScreeningDatabase
from models.chatbot import SemiconductorChatbot, DiscrepancyAnalyzer


class ScreeningPipeline:
    """
    Master backend controller managing communication between:
    User Input -> Feature Scaler -> ML Model Engine -> Chatbot Explainer -> SQLite DB.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        ai_provider: str = "auto",
        api_key: Optional[str] = None
    ):
        self.scaler = FeatureScaler()
        self.model_engine = ModelEngine(scaler=self.scaler)
        self.database = ScreeningDatabase(db_path=db_path)
        self.chatbot = SemiconductorChatbot(provider=ai_provider, api_key=api_key)

    def process_screening(
        self,
        model_type: str,
        raw_input: float,
        user_said_output: Optional[float] = None,
        component_id: str = "DUT-01",
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the primary end-to-end pipeline:
        1. Takes unscaled user input X.
        2. Standardizes X into X_scaled.
        3. Evaluates model to produce scaled prediction Y_scaled and physical Y_model.
        4. If user_said_output is given, computes discrepancy and generates physics explanation.
           If user_said_output is omitted, explains model dynamics at that operating point.
        5. Saves full record into SQLite DB.
        
        Returns:
            Structured dictionary with all intermediate representations,
            predictions, explanations, and database record ID.
        """
        # Step 1 & 2 & 3: Run Model Inference with Automatic Scaling
        pred = self.model_engine.predict(model_type, raw_input)
        physical_y_model = pred["physical_output"]
        scaled_x = pred["scaled_input"]
        scaled_y = pred["scaled_output"]

        # Step 4: Discrepancy & Chatbot Explanation
        if user_said_output is not None:
            # User provided observed/ground truth output: evaluate discrepancy
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
        else:
            # Pure model prediction mode: Explain model dynamics at this operating point
            delta = None
            pct_diff = None
            ratio = None
            direction = "NOMINAL_PREDICTION"
            risk_decision = "PASS"
            severity = "LOW"
            physics_causes = [
                f"Nominal operation predicted by ML model for input {raw_input} {pred['input_unit']}."
            ]
            recommendations = [
                "Verify sensor telemetry matches baseline prediction."
            ]
            explanation = (
                f"### ⚡ Model Dynamics & Prediction Summary\n"
                f"- **Component ID**: `{component_id}`\n"
                f"- **Model**: **{pred['model_name']}**\n"
                f"- **Raw Input**: `{DiscrepancyAnalyzer.format_val(raw_input, pred['input_unit'])}` (Scaled: `{scaled_x:+.4f} σ`)\n"
                f"- **Predicted Physical Output**: `{DiscrepancyAnalyzer.format_val(physical_y_model, pred['output_unit'])}` (Scaled: `{scaled_y:+.4f} σ`)\n\n"
                f"**Dynamics Overview**:\n"
                f"The component is evaluated under standard operational bounds. If experimental testing reveals higher leakage or shifted thresholds, submit the observed measurement to trigger discrepancy diagnostics."
            )

        # Step 5: Persist transaction into SQLite Database
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

        # Step 6: Return complete response payload
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
            "physical_output": physical_y_model,
            "user_said_output": user_said_output,
            "discrepancy": {
                "delta": delta,
                "pct_diff": pct_diff,
                "ratio": ratio,
                "direction": direction,
                "risk_decision": risk_decision,
                "severity": severity
            },
            "physics_causes": physics_causes,
            "recommendations": recommendations,
            "chatbot_explanation": explanation,
            "ai_provider": self.chatbot.api_client.provider,
            "scaling_metadata": pred["scaling_parameters"]
        }

    def chat(self, user_message: str, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Conversational chat interface with automatic persistence to SQLite database.
        """
        # Save user message
        self.database.save_chat_message(session_id, "user", user_message)

        # Generate response from chatbot
        reply = self.chatbot.chat(user_message)

        # Save assistant message
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
    print(f"Raw Input: {res['raw_input']} V -> Scaled: {res['scaled_input']:.4f}")
    print(f"Model Output: {res['physical_output']:.4e} A -> Scaled: {res['scaled_output']:.4f}")
    print(f"User Output: {res['user_said_output']:.4e} A")
    print(f"Screening Decision: {res['discrepancy']['risk_decision']}")
    print("\nChatbot Explanation Preview:")
    print(res["chatbot_explanation"][:250] + "...")
    print("\n✅ Pipeline executed successfully!")
