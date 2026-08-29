#!/usr/bin/env python3
"""
SIH26170 - Backend Feature & Target Scaler Module
=============================================================================
Deals with raw (unscaled) user input, performing standard feature scaling
(z-score standardization) before passing to ML models, and inverse target
transformation to convert model predictions back into physical engineering units.
"""

import os
import csv
import math
from typing import Dict, Any, Tuple, Optional

# Default calibrated scaler parameters fitted from NASA Accelerated Aging Datasets
MODEL_SCALERS = {
    "breakdown": {
        "name": "Breakdown Model Scaler",
        "input_feature": "Collector-Emitter Voltage",
        "input_unit": "V",
        "output_target": "Leakage Current",
        "output_unit": "A",
        # Scaler stats from dataset
        "mean_x": 3.883881,
        "std_x": 0.9993945,
        "mean_y": 7.107203e-05,
        "std_y": 1.073088e-04,
        # Scaled linear model parameters: y_scaled = w * x_scaled + b
        "weight": 0.739114,
        "bias": 0.0
    },
    "leakage": {
        "name": "Leakage IV Model Scaler",
        "input_feature": "Applied Voltage",
        "input_unit": "V",
        "output_target": "Leakage Current",
        "output_unit": "A",
        "mean_x": 301.3095,
        "std_x": 173.3395,
        "mean_y": 1.844920e-06,
        "std_y": 1.385642e-06,
        "weight": 0.974888,
        "bias": 0.0
    },
    "turnon": {
        "name": "Turn-On Model Scaler",
        "input_feature": "Gate Voltage",
        "input_unit": "V",
        "output_target": "Collector Current",
        "output_unit": "A",
        "mean_x": 3.883881,
        "std_x": 0.9993945,
        "mean_y": 7.107203e-05,
        "std_y": 1.073088e-04,
        "weight": 0.739114,
        "bias": 0.0
    }
}


class FeatureScaler:
    """
    Standardizes raw, unscaled inputs to zero-mean unit-variance space (X_scaled)
    and maps model predictions back to original physical units (Y_physical).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or MODEL_SCALERS

    def get_scaler_info(self, model_type: str) -> Dict[str, Any]:
        """Retrieve scaler parameters for a given model."""
        key = self._normalize_key(model_type)
        if key in self.config:
            return self.config[key]
        raise ValueError(f"Unknown model type: '{model_type}'. Supported: {list(self.config.keys())}")

    def transform_input(self, model_type: str, raw_x: float) -> Tuple[float, Dict[str, float]]:
        """
        Takes raw unscaled user input X and standardizes it:
            X_scaled = (raw_x - mean_x) / std_x
            
        Returns:
            (scaled_x, scaling_metadata)
        """
        info = self.get_scaler_info(model_type)
        mean_x = info["mean_x"]
        std_x = info["std_x"] if info["std_x"] > 1e-15 else 1.0

        scaled_x = (raw_x - mean_x) / std_x
        metadata = {
            "raw_input": raw_x,
            "scaled_input": scaled_x,
            "mean_x": mean_x,
            "std_x": std_x,
            "input_unit": info["input_unit"]
        }
        return scaled_x, metadata

    def inverse_transform_input(self, model_type: str, scaled_x: float) -> float:
        """Unscales standardized X back to physical input."""
        info = self.get_scaler_info(model_type)
        return (scaled_x * info["std_x"]) + info["mean_x"]

    def transform_target(self, model_type: str, raw_y: float) -> float:
        """Standardizes target value: Y_scaled = (raw_y - mean_y) / std_y."""
        info = self.get_scaler_info(model_type)
        std_y = info["std_y"] if info["std_y"] > 1e-15 else 1.0
        return (raw_y - info["mean_y"]) / std_y

    def inverse_transform_target(self, model_type: str, scaled_y: float) -> Tuple[float, Dict[str, float]]:
        """
        Converts model predicted output from scaled space back to physical units:
            Y_physical = (scaled_y * std_y) + mean_y
            
        Returns:
            (physical_y, scaling_metadata)
        """
        info = self.get_scaler_info(model_type)
        mean_y = info["mean_y"]
        std_y = info["std_y"]

        physical_y = (scaled_y * std_y) + mean_y
        
        # Enforce physical non-negativity constraint for current if needed
        if "current" in info["output_target"].lower() and physical_y < 0:
            physical_y = max(1e-12, physical_y)

        metadata = {
            "scaled_output": scaled_y,
            "physical_output": physical_y,
            "mean_y": mean_y,
            "std_y": std_y,
            "output_unit": info["output_unit"]
        }
        return physical_y, metadata

    def fit_from_csv(self, model_type: str, csv_path: str, x_col: str, y_col: str):
        """
        Dynamically calculate and update scaler parameters (mean, std, weights)
        from a new dataset CSV file.
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Dataset file not found: {csv_path}")

        xs, ys = [], []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    xs.append(float(row[x_col]))
                    ys.append(float(row[y_col]))
                except (ValueError, KeyError):
                    continue

        n = len(xs)
        if n < 2:
            raise ValueError(f"Insufficient data points in {csv_path}")

        mean_x = sum(xs) / n
        std_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs) / n)
        mean_y = sum(ys) / n
        std_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys) / n)

        # Fit scaled regression line
        xs_scaled = [(x - mean_x) / (std_x if std_x > 0 else 1.0) for x in xs]
        ys_scaled = [(y - mean_y) / (std_y if std_y > 0 else 1.0) for y in ys]

        mean_xs = sum(xs_scaled) / n
        mean_ys = sum(ys_scaled) / n
        cov = sum((xs_scaled[i] - mean_xs) * (ys_scaled[i] - mean_ys) for i in range(n))
        var_x = sum((xs_scaled[i] - mean_xs) ** 2 for i in range(n))
        w = cov / var_x if var_x > 0 else 1.0
        b = mean_ys - (w * mean_xs)

        key = self._normalize_key(model_type)
        self.config[key] = {
            "name": f"{model_type.capitalize()} Scaler (Dynamically Fitted)",
            "input_feature": x_col,
            "input_unit": "units",
            "output_target": y_col,
            "output_unit": "units",
            "mean_x": mean_x,
            "std_x": std_x,
            "mean_y": mean_y,
            "std_y": std_y,
            "weight": w,
            "bias": b
        }
        return self.config[key]

    @staticmethod
    def _normalize_key(model_type: str) -> str:
        k = model_type.lower().replace("-", "").replace("_", "").replace(" ", "")
        if "break" in k:
            return "breakdown"
        elif "leak" in k:
            return "leakage"
        elif "turn" in k or "on" in k:
            return "turnon"
        return model_type.lower()
