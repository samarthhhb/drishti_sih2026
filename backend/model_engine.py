#!/usr/bin/env python3
"""
SIH26170 - Backend Model Inference Engine
=============================================================================
Executes machine learning regression models for Breakdown, Leakage IV, and
Turn-On characteristics in scaled feature space and transforms predictions
back into unscaled physical measurements.
"""

from typing import Dict, Any, Tuple, Optional
from .scaler import FeatureScaler


class ModelEngine:
    """
    Handles model inference execution with automatic feature scaling
    and inverse output transformation.
    """

    def __init__(self, scaler: Optional[FeatureScaler] = None):
        self.scaler = scaler or FeatureScaler()

    def predict(self, model_type: str, raw_x: float) -> Dict[str, Any]:
        """
        End-to-end forward pass:
        1. Takes unscaled user input X (e.g. 550.0 Volts or 5.0 Volts)
        2. Scales input: X_scaled = (X - mean_x) / std_x
        3. Runs inference: Y_scaled = w * X_scaled + b
        4. Inverses scaling: Y_physical = Y_scaled * std_y + mean_y
        
        Returns:
            Dictionary containing raw input, scaled input, scaled output,
            physical prediction, and unit metadata.
        """
        # Step 1: Scale raw input
        scaled_x, x_meta = self.scaler.transform_input(model_type, raw_x)
        
        # Step 2: Retrieve model weights
        info = self.scaler.get_scaler_info(model_type)
        w = info.get("weight", 1.0)
        b = info.get("bias", 0.0)

        # Step 3: Run model inference in scaled space
        scaled_y = (w * scaled_x) + b

        # Step 4: Inverse scale target to physical units
        physical_y, y_meta = self.scaler.inverse_transform_target(model_type, scaled_y)

        return {
            "model_type": self.scaler._normalize_key(model_type),
            "model_name": info["name"],
            "input_feature": info["input_feature"],
            "input_unit": info["input_unit"],
            "output_target": info["output_target"],
            "output_unit": info["output_unit"],
            "raw_input": raw_x,
            "scaled_input": scaled_x,
            "scaled_output": scaled_y,
            "physical_output": physical_y,
            "scaling_parameters": {
                "mean_x": info["mean_x"],
                "std_x": info["std_x"],
                "mean_y": info["mean_y"],
                "std_y": info["std_y"],
                "weight": w,
                "bias": b
            }
        }
