#!/usr/bin/env python3
"""
SIH26170 - Backend MinMaxScaler Module
=============================================================================
Provides MinMaxScaler normalization [0, 1] for semiconductor parameters,
converting small physical numbers (nano-amperes, micro-amperes) into intuitive
normalized values for machine learning regression, database persistence, and UI.
"""

from typing import Dict, Any, Tuple, Optional

# MinMax Calibration Bounds for the 3 Semiconductor Screening Models
MINMAX_BOUNDS = {
    "breakdown": {
        "name": "Breakdown Model",
        "input_feature": "Collector-Emitter Voltage",
        "input_unit": "V",
        "output_target": "Leakage Current",
        "output_unit": "microAmpere",
        "x_min": 0.0,
        "x_max": 650.0,
        "y_min": 0.0,
        "y_max": 150.0,     # 150 microAmpere max span
        "model_type": "polynomial",
        "poly_power": 4
    },
    "leakage": {
        "name": "Leakage IV Model",
        "input_feature": "Applied Voltage",
        "input_unit": "V",
        "output_target": "Leakage Current",
        "output_unit": "microAmpere",
        "x_min": 0.0,
        "x_max": 600.0,
        "y_min": 0.0,
        "y_max": 10.0,      # 10 microAmpere max span
        "model_type": "linear",
        "slope_norm": 0.95
    },
    "turnon": {
        "name": "Turn-On Model",
        "input_feature": "Gate Voltage",
        "input_unit": "V",
        "output_target": "Collector Current",
        "output_unit": "microAmpere",
        "x_min": 0.0,
        "x_max": 15.0,
        "y_min": 0.0,
        "y_max": 250.0,     # 250 microAmpere sensor scale
        "model_type": "threshold",
        "vth_norm": 4.0 / 15.0
    }
}


class MinMaxScaler:
    """
    MinMaxScaler for transforming inputs and outputs into [0, 1] range:
        X_scaled = (X - X_min) / (X_max - X_min)
        Y_scaled = (Y - Y_min) / (Y_max - Y_min)
    """

    def __init__(self, bounds: Optional[Dict[str, Any]] = None):
        self.bounds = bounds or MINMAX_BOUNDS

    def _normalize_key(self, model_type: str) -> str:
        k = model_type.lower().replace("-", "").replace("_", "").replace(" ", "")
        if "break" in k:
            return "breakdown"
        elif "leak" in k:
            return "leakage"
        elif "turn" in k or "on" in k:
            return "turnon"
        return "breakdown"

    def get_bounds(self, model_type: str) -> Dict[str, Any]:
        key = self._normalize_key(model_type)
        return self.bounds.get(key, self.bounds["breakdown"])

    def transform_x(self, model_type: str, raw_x: float) -> float:
        """Scale raw input X into [0, 1] range."""
        b = self.get_bounds(model_type)
        span = b["x_max"] - b["x_min"]
        if span == 0:
            return 0.0
        scaled = (raw_x - b["x_min"]) / span
        return max(0.0, min(1.0, scaled))

    def inverse_transform_x(self, model_type: str, scaled_x: float) -> float:
        """Convert scaled X [0, 1] back into raw physical input."""
        b = self.get_bounds(model_type)
        span = b["x_max"] - b["x_min"]
        return (scaled_x * span) + b["x_min"]

    def transform_y(self, model_type: str, physical_y: float) -> float:
        """Scale physical output Y into [0, 1] range."""
        b = self.get_bounds(model_type)
        span = b["y_max"] - b["y_min"]
        if span == 0:
            return 0.0
        scaled = (physical_y - b["y_min"]) / span
        return max(0.0, min(1.0, scaled))

    def inverse_transform_y(self, model_type: str, scaled_y: float) -> float:
        """Convert scaled Y [0, 1] back into physical output."""
        b = self.get_bounds(model_type)
        span = b["y_max"] - b["y_min"]
        return max(0.0, (scaled_y * span) + b["y_min"])
