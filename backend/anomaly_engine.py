#!/usr/bin/env python3
"""
SIH26170 - Dynamic Outlier Detection System Engine
=============================================================================
Implements full curve-level population anomaly detection across semiconductor
I-V sweeps (Breakdown, Leakage IV, Turn-On) based on module_a:
1. Multi-cycle sweep segmentation (voltage reset detection).
2. 17-feature morphometric & electrical extraction (slopes, knee, span, area).
3. Layer 1: Robust IQR Dynamic Outlier Detection (Z-scores vs threshold).
4. Layer 2: Unsupervised Machine Learning (Isolation Forest).
5. Dual-Layer Score Fusion (0.60 Dynamic + 0.40 Isolation) -> PASS/HOLD/REJECT.
"""

import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

FEATURE_NAMES = [
    "min_voltage",
    "max_voltage",
    "min_current",
    "max_current",
    "mean_current",
    "std_current",
    "max_slope",
    "mean_slope",
    "knee_voltage",
    "current_v25",
    "current_v50",
    "current_v75",
    "current_v90",
    "voltage_10pct",
    "voltage_50pct",
    "voltage_90pct",
    "curve_area"
]

FEATURE_LABELS = {
    "min_voltage": "Min Voltage (V)",
    "max_voltage": "Max Voltage (V)",
    "min_current": "Min Current (μA)",
    "max_current": "Max Current (μA)",
    "mean_current": "Mean Conduction (μA)",
    "std_current": "Current Std Dev (μA)",
    "max_slope": "Max Transconductance / Steepness (dI/dV)",
    "mean_slope": "Mean Dynamic Conductance (dI/dV)",
    "knee_voltage": "Avalanche / Threshold Knee Voltage (V)",
    "current_v25": "Current at 25% Voltage Span (μA)",
    "current_v50": "Current at 50% Voltage Span (μA)",
    "current_v75": "Current at 75% Voltage Span (μA)",
    "current_v90": "Current at 90% Voltage Span (μA)",
    "voltage_10pct": "Voltage at 10% Peak Current (V)",
    "voltage_50pct": "Voltage at 50% Peak Current (V)",
    "voltage_90pct": "Voltage at 90% Peak Current (V)",
    "curve_area": "Integrated I-V Area (μA·V)"
}

MODEL_MAP = {
    "breakdown": {
        "file": "Breakdown_timeseries_microampere.csv",
        "fallback_file": "Breakdown.csv",
        "x_col": "Collector_Emitter_Voltage_Vce",
        "y_col": "Leakage_Current_Ic_microampere",
        "y_col_alt": "Leakage_Current_Ic",
        "x_unit": "V",
        "y_unit": "microAmpere",
        "display_name": "Breakdown Model (Vce vs Ic)",
        "reset_threshold": 0.5
    },
    "leakage": {
        "file": "LeakageIV_timeseries_microampere.csv",
        "fallback_file": "LeakageIV.csv",
        "x_col": "Applied_Voltage",
        "y_col": "Leakage_Current_microampere",
        "y_col_alt": "Leakage_Current",
        "x_unit": "V",
        "y_unit": "microAmpere",
        "display_name": "Leakage IV Model (Vapp vs Ileak)",
        "reset_threshold": 0.5
    },
    "turnon": {
        "file": "TurnOn_timeseries_microampere.csv",
        "fallback_file": "TurnOn.csv",
        "x_col": "Gate_Voltage",
        "y_col": "Collector_Current_microampere",
        "y_col_alt": "Collector_Current",
        "x_unit": "V",
        "y_unit": "microAmpere",
        "display_name": "Turn-On Model (Vge vs Ic)",
        "reset_threshold": 0.5
    }
}


def compute_median(values: List[float]) -> float:
    if not values:
        return 0.0
    sorted_v = sorted(values)
    n = len(sorted_v)
    mid = n // 2
    if n % 2 == 1:
        return sorted_v[mid]
    return (sorted_v[mid - 1] + sorted_v[mid]) / 2.0


def compute_mad(values: List[float], med: Optional[float] = None) -> float:
    if not values:
        return 0.0
    if med is None:
        med = compute_median(values)
    devs = [abs(x - med) for x in values]
    return compute_median(devs)


def linear_interp(x_target: float, x_arr: List[float], y_arr: List[float]) -> float:
    """1D piecewise linear interpolation."""
    if not x_arr or not y_arr:
        return 0.0
    if x_target <= x_arr[0]:
        return y_arr[0]
    if x_target >= x_arr[-1]:
        return y_arr[-1]
    for i in range(len(x_arr) - 1):
        if x_arr[i] <= x_target <= x_arr[i + 1]:
            dx = x_arr[i + 1] - x_arr[i]
            if abs(dx) < 1e-12:
                return y_arr[i]
            frac = (x_target - x_arr[i]) / dx
            return y_arr[i] + frac * (y_arr[i + 1] - y_arr[i])
    return y_arr[-1]


def trapezoid_area(y_arr: List[float], x_arr: List[float]) -> float:
    """Calculates integral area under curve using trapezoidal rule."""
    if len(x_arr) < 2:
        return 0.0
    area = 0.0
    for i in range(len(x_arr) - 1):
        dx = x_arr[i + 1] - x_arr[i]
        area += 0.5 * (y_arr[i] + y_arr[i + 1]) * dx
    return area


class DynamicOutlierEngine:
    """
    Curve-Level Dynamic Outlier & Anomaly Detection System.
    Loads population sweeps, builds feature distributions, and evaluates test curves.
    """

    def __init__(self):
        self._models_data: Dict[str, Dict[str, Any]] = {}
        self._initialize_population_models()

    def _initialize_population_models(self):
        """Pre-processes all 3 semiconductor models and computes population baselines."""
        for m_key, cfg in MODEL_MAP.items():
            self._models_data[m_key] = self._build_model_baseline(m_key, cfg)

    def _build_model_baseline(self, m_key: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Loads dataset from disk, segments curves, and computes 17-feature distributions."""
        csv_file = DATA_DIR / cfg["file"]
        if not csv_file.exists():
            csv_file = DATA_DIR / cfg["fallback_file"]
        if not csv_file.exists():
            csv_file = ROOT_DIR / "archive" / "final_data" / "dataset" / cfg["fallback_file"]

        raw_points = []
        if csv_file.exists():
            import csv
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        x_val = float(row[cfg["x_col"]])
                        if cfg["y_col"] in row:
                            y_val = float(row[cfg["y_col"]])
                        elif cfg["y_col_alt"] in row:
                            y_raw = float(row[cfg["y_col_alt"]])
                            y_val = y_raw * 1e6 if y_raw < 0.1 else y_raw
                        else:
                            continue
                        t_val = float(row.get("time_minutes", len(raw_points) * 30.0))
                        raw_points.append({"t": t_val, "x": x_val, "y": y_val})
                    except (ValueError, KeyError):
                        continue

        if not raw_points:
            # Synthetic backup if files are missing
            raw_points = [{"t": i * 30.0, "x": 2.0 + (i % 200) * 0.015, "y": 0.005 + (i % 200)**3 * 0.0001} for i in range(3790)]

        # Segment into individual sweep curves by detecting large voltage resets
        curves = []
        curr_curve = []
        reset_thresh = cfg.get("reset_threshold", 0.5)

        for i, pt in enumerate(raw_points):
            if curr_curve and (curr_curve[-1]["x"] - pt["x"] > reset_thresh):
                curves.append(curr_curve)
                curr_curve = []
            curr_curve.append(pt)
        if curr_curve:
            curves.append(curr_curve)

        # Extract 17 features for every curve in population
        population_features: List[Dict[str, float]] = []
        curves_clean = []
        for c_idx, curve_pts in enumerate(curves):
            # Sort by voltage
            sorted_pts = sorted(curve_pts, key=lambda p: p["x"])
            # Remove duplicate x by averaging y
            dedup_dict: Dict[float, List[float]] = {}
            for p in sorted_pts:
                dedup_dict.setdefault(round(p["x"], 6), []).append(p["y"])
            x_arr = sorted(dedup_dict.keys())
            y_arr = [sum(dedup_dict[x]) / len(dedup_dict[x]) for x in x_arr]

            if len(x_arr) < 5:
                continue

            feats = self.extract_curve_features(x_arr, y_arr, c_idx)
            population_features.append(feats)
            curves_clean.append({
                "curve_id": c_idx,
                "x": x_arr,
                "y": y_arr,
                "features": feats
            })

        # Compute Population Statistics per feature (median, MAD, IQR, mean, std)
        feature_stats = {}
        for feat in FEATURE_NAMES:
            vals = [cf[feat] for cf in population_features]
            med = compute_median(vals)
            mad = compute_mad(vals, med)
            if mad == 0.0:
                mad = 1e-12
            mean_v = sum(vals) / max(1, len(vals))
            std_v = math.sqrt(sum((v - mean_v)**2 for v in vals) / max(1, len(vals)))
            if std_v == 0.0:
                std_v = 1.0
            feature_stats[feat] = {
                "median": med,
                "mad": mad,
                "mean": mean_v,
                "std": std_v,
                "min": min(vals) if vals else 0.0,
                "max": max(vals) if vals else 0.0
            }

        # Calculate dynamic scores for all population curves
        pop_dynamic_scores = []
        for cf in population_features:
            max_z = 0.0
            for feat in FEATURE_NAMES:
                z = abs(cf[feat] - feature_stats[feat]["median"]) / (1.4826 * feature_stats[feat]["mad"])
                if z > max_z:
                    max_z = z
            pop_dynamic_scores.append(max_z)

        score_med = compute_median(pop_dynamic_scores)
        score_mad = compute_mad(pop_dynamic_scores, score_med)
        if score_mad == 0.0:
            score_mad = 1.0
        dynamic_threshold = score_med + 3.0 * score_mad

        # Build Isolation Forest baseline scoring heuristic
        # If scikit-learn is available, use IsolationForest; else use robust Mahalanobis/IQR distance
        iso_scores = []
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler
            import numpy as np

            X_mat = [[cf[feat] for feat in FEATURE_NAMES] for cf in population_features]
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_mat)
            iso = IsolationForest(n_estimators=300, contamination=0.10, random_state=42)
            iso.fit(X_scaled)
            scores = -iso.decision_function(X_scaled)
            iso_scores = list(scores)
            iso_model = iso
            scaler_model = scaler
        except Exception:
            iso_model = None
            scaler_model = None
            for cf in population_features:
                dist = math.sqrt(sum(((cf[feat] - feature_stats[feat]["mean"]) / feature_stats[feat]["std"])**2 for feat in FEATURE_NAMES))
                iso_scores.append(dist / math.sqrt(len(FEATURE_NAMES)))

        min_iso = min(iso_scores) if iso_scores else 0.0
        max_iso = max(iso_scores) if iso_scores else 1.0

        # Mark curve anomaly flags in population
        for i, c in enumerate(curves_clean):
            d_score = pop_dynamic_scores[i]
            d_norm = min(3.0, max(0.0, d_score / (dynamic_threshold + 1e-12)))
            iso_raw = iso_scores[i]
            iso_norm = (iso_raw - min_iso) / (max_iso - min_iso + 1e-12)
            comb = 0.60 * d_norm + 0.40 * iso_norm
            c["dynamic_score"] = round(d_score, 4)
            c["isolation_score"] = round(iso_raw, 4)
            c["combined_score"] = round(comb, 4)
            if comb >= 1.00:
                c["decision"] = "REJECT"
                c["severity"] = "HIGH"
            elif comb >= 0.70:
                c["decision"] = "HOLD"
                c["severity"] = "MODERATE"
            else:
                c["decision"] = "PASS"
                c["severity"] = "LOW"

        return {
            "model_type": m_key,
            "config": cfg,
            "curves": curves_clean,
            "feature_stats": feature_stats,
            "dynamic_threshold": dynamic_threshold,
            "min_iso": min_iso,
            "max_iso": max_iso,
            "iso_model": iso_model,
            "scaler_model": scaler_model,
            "total_curves": len(curves_clean)
        }

    def extract_curve_features(self, x_arr: List[float], y_arr: List[float], curve_id: int = 0) -> Dict[str, float]:
        """
        Extracts the 17 morphometric and electrical features from a single I-V curve:
        [min_v, max_v, min_i, max_i, mean_i, std_i, max_slope, mean_slope, knee_v,
         i_v25, i_v50, i_v75, i_v90, v_10pct, v_50pct, v_90pct, curve_area]
        """
        n = len(x_arr)
        min_v = float(min(x_arr))
        max_v = float(max(x_arr))
        min_i = float(min(y_arr))
        max_i = float(max(y_arr))
        mean_i = sum(y_arr) / max(1, n)
        std_i = math.sqrt(sum((y - mean_i)**2 for y in y_arr) / max(1, n))

        # Slopes dI / dV
        slopes = []
        knee_idx = 0
        max_slope = 0.0
        for i in range(n - 1):
            dx = x_arr[i + 1] - x_arr[i]
            if abs(dx) > 1e-12:
                s = (y_arr[i + 1] - y_arr[i]) / dx
                slopes.append(s)
                if s > max_slope:
                    max_slope = s
                    knee_idx = i

        mean_slope = (sum(slopes) / max(1, len(slopes))) if slopes else 0.0
        knee_voltage = float(x_arr[knee_idx]) if slopes else (min_v + max_v) / 2.0

        # Current at voltage span fractions
        v_span = max_v - min_v if max_v > min_v else 1.0
        v25 = min_v + 0.25 * v_span
        v50 = min_v + 0.50 * v_span
        v75 = min_v + 0.75 * v_span
        v90 = min_v + 0.90 * v_span

        current_v25 = linear_interp(v25, x_arr, y_arr)
        current_v50 = linear_interp(v50, x_arr, y_arr)
        current_v75 = linear_interp(v75, x_arr, y_arr)
        current_v90 = linear_interp(v90, x_arr, y_arr)

        # Voltage at current peak fractions
        t10 = 0.10 * max_i
        t50 = 0.50 * max_i
        t90 = 0.90 * max_i

        idx10 = 0
        idx50 = 0
        idx90 = 0
        for i, y in enumerate(y_arr):
            if y >= t10 and idx10 == 0:
                idx10 = i
            if y >= t50 and idx50 == 0:
                idx50 = i
            if y >= t90 and idx90 == 0:
                idx90 = i

        voltage_10pct = float(x_arr[idx10])
        voltage_50pct = float(x_arr[idx50])
        voltage_90pct = float(x_arr[idx90])

        area = trapezoid_area(y_arr, x_arr)

        return {
            "curve_id": curve_id,
            "min_voltage": min_v,
            "max_voltage": max_v,
            "min_current": min_i,
            "max_current": max_i,
            "mean_current": mean_i,
            "std_current": std_i,
            "max_slope": max_slope,
            "mean_slope": mean_slope,
            "knee_voltage": knee_voltage,
            "current_v25": current_v25,
            "current_v50": current_v50,
            "current_v75": current_v75,
            "current_v90": current_v90,
            "voltage_10pct": voltage_10pct,
            "voltage_50pct": voltage_50pct,
            "voltage_90pct": voltage_90pct,
            "curve_area": area
        }

    def detect_curve_anomaly(
        self,
        model_type: str,
        x_points: List[float],
        y_points: List[float],
        component_id: Optional[str] = "DUT-SWEEP-01",
        include_curve_data: bool = True
    ) -> Dict[str, Any]:
        """
        Executes end-to-end curve anomaly detection on user submitted curve.
        """
        m_key = model_type.lower().replace("-", "").replace("_", "")
        if "break" in m_key:
            m_key = "breakdown"
        elif "leak" in m_key:
            m_key = "leakage"
        elif "turn" in m_key or "on" in m_key:
            m_key = "turnon"
        else:
            m_key = "breakdown"

        baseline = self._models_data.get(m_key)
        if not baseline:
            self._models_data[m_key] = self._build_model_baseline(m_key, MODEL_MAP[m_key])
            baseline = self._models_data[m_key]

        if not x_points or not y_points or len(x_points) != len(y_points):
            raise ValueError("Invalid curve: x and y arrays must be non-empty and of equal length.")

        # Sort and clean curve
        paired = sorted(zip(x_points, y_points), key=lambda p: p[0])
        x_sorted = [float(p[0]) for p in paired]
        y_sorted = [float(p[1]) for p in paired]

        # Extract 17 features
        features = self.extract_curve_features(x_sorted, y_sorted, curve_id=999)

        # Layer 1: Robust Dynamic IQR Outlier Score
        stats = baseline["feature_stats"]
        outlier_features = []
        all_feature_scores = {}
        max_dynamic_z = 0.0

        for feat in FEATURE_NAMES:
            val = features[feat]
            med = stats[feat]["median"]
            mad = stats[feat]["mad"]
            robust_z = (val - med) / (1.4826 * mad)
            abs_z = abs(robust_z)
            all_feature_scores[feat] = {
                "name": feat,
                "label": FEATURE_LABELS.get(feat, feat),
                "value": round(val, 6),
                "population_median": round(med, 6),
                "population_mad": round(mad, 6),
                "robust_z": round(robust_z, 3),
                "abs_z": round(abs_z, 3),
                "is_outlier": abs_z >= 3.5
            }
            if abs_z >= 3.5:
                outlier_features.append({
                    "feature": feat,
                    "label": FEATURE_LABELS.get(feat, feat),
                    "robust_score": round(abs_z, 3),
                    "value": round(val, 6),
                    "direction": "HIGH" if robust_z > 0 else "LOW"
                })
            if abs_z > max_dynamic_z:
                max_dynamic_z = abs_z

        outlier_features.sort(key=lambda item: item["robust_score"], reverse=True)

        dynamic_score = max_dynamic_z
        dynamic_threshold = baseline["dynamic_threshold"]
        dynamic_flag = "ANOMALY" if dynamic_score >= dynamic_threshold else "NORMAL"
        dynamic_normalized = min(3.0, max(0.0, dynamic_score / (dynamic_threshold + 1e-12)))

        # Layer 2: Isolation Forest Score
        iso_model = baseline.get("iso_model")
        scaler_model = baseline.get("scaler_model")
        min_iso = baseline["min_iso"]
        max_iso = baseline["max_iso"]

        if iso_model and scaler_model:
            try:
                feat_vec = [[features[feat] for feat in FEATURE_NAMES]]
                feat_scaled = scaler_model.transform(feat_vec)
                iso_raw = float(-iso_model.decision_function(feat_scaled)[0])
                pred_label = iso_model.predict(feat_scaled)[0]
                ml_flag = "ANOMALY" if pred_label == -1 else "NORMAL"
            except Exception:
                dist = math.sqrt(sum(((features[feat] - stats[feat]["mean"]) / stats[feat]["std"])**2 for feat in FEATURE_NAMES))
                iso_raw = dist / math.sqrt(len(FEATURE_NAMES))
                ml_flag = "ANOMALY" if iso_raw > 1.8 else "NORMAL"
        else:
            dist = math.sqrt(sum(((features[feat] - stats[feat]["mean"]) / stats[feat]["std"])**2 for feat in FEATURE_NAMES))
            iso_raw = dist / math.sqrt(len(FEATURE_NAMES))
            ml_flag = "ANOMALY" if iso_raw > 1.8 else "NORMAL"

        iso_normalized = max(0.0, min(1.0, (iso_raw - min_iso) / (max_iso - min_iso + 1e-12)))

        # Combined Fusion Score
        combined_score = 0.60 * dynamic_normalized + 0.40 * iso_normalized

        # Decision Policy (PASS / HOLD / REJECT)
        if combined_score >= 1.00:
            decision = "REJECT"
            severity = "HIGH"
        elif combined_score >= 0.70:
            decision = "HOLD"
            severity = "MODERATE"
        else:
            decision = "PASS"
            severity = "LOW"

        # Construct failure physics diagnostic text
        physics_report = self._build_physics_report(m_key, component_id, decision, severity, dynamic_score, dynamic_threshold, outlier_features, combined_score)

        response = {
            "success": True,
            "system_name": "Dynamic Outlier Detection System",
            "model_type": m_key,
            "model_display_name": baseline["config"]["display_name"],
            "component_id": component_id,
            "anomaly": {
                "dynamic_score": round(dynamic_score, 4),
                "dynamic_threshold": round(dynamic_threshold, 4),
                "dynamic_flag": dynamic_flag,
                "outlier_feature_count": len(outlier_features),
                "outlier_features": outlier_features,
                "isolation_score": round(iso_raw, 4),
                "isolation_flag": ml_flag,
                "combined_score": round(combined_score, 4),
                "decision": decision,
                "severity": severity,
                "weights": {"dynamic": 0.60, "isolation_forest": 0.40}
            },
            "features": {feat: round(features[feat], 6) for feat in FEATURE_NAMES},
            "feature_details": all_feature_scores,
            "diagnostic_report": physics_report,
            "population_summary": {
                "total_curves": baseline["total_curves"],
                "threshold_rule": "θ = median + 3 * MAD",
                "feature_count": len(FEATURE_NAMES)
            }
        }

        if include_curve_data:
            response["curve"] = {
                "x": [round(x, 4) for x in x_sorted],
                "y": [round(y, 6) for y in y_sorted],
                "x_unit": baseline["config"]["x_unit"],
                "y_unit": baseline["config"]["y_unit"]
            }

        return response

    def _build_physics_report(
        self,
        m_key: str,
        component_id: Optional[str],
        decision: str,
        severity: str,
        dynamic_score: float,
        threshold: float,
        outliers: List[Dict[str, Any]],
        combined_score: float
    ) -> str:
        cid = component_id or "DUT"
        if decision == "PASS":
            return (
                f"### ✅ Nominal Curve Population Alignment — {decision}\n"
                f"- **Component**: `{cid}`\n"
                f"- **Combined Anomaly Score**: `{combined_score:.4f}` (Below 0.70 threshold)\n"
                f"- **Morphometry Status**: The complete I-V sweep characteristics align closely with the healthy NASA screening lot. "
                f"No significant dynamic outlier features or isolation tree anomalies detected."
            )
        elif decision == "HOLD":
            top_outlier = outliers[0]["label"] if outliers else "morphology variance"
            return (
                f"### ⚠️ Subtle Population Anomaly — {decision} (Inspector Review Required)\n"
                f"- **Component**: `{cid}` | **Severity**: `{severity}`\n"
                f"- **Combined Score**: `{combined_score:.4f}` (0.70 - 0.99 range)\n"
                f"- **Key Trigger**: `{top_outlier}` exhibiting `{outliers[0]['robust_score'] if outliers else dynamic_score:.2f}σ` robust deviation from lot median.\n"
                f"- **Semiconductor Physics**: Indicative of pre-screening guard ring oxide thinning or sub-threshold channel leakage inception. Recommend secondary sweep validation."
            )
        else:
            top_names = ", ".join([f"`{o['label']}` ({o['robust_score']}σ)" for o in outliers[:3]]) if outliers else "multi-feature collapse"
            return (
                f"### 🛑 Critical Curve-Level Defect — {decision}\n"
                f"- **Component**: `{cid}` | **Severity**: `{severity}`\n"
                f"- **Combined Score**: `{combined_score:.4f}` (Exceeds 1.00 threshold)\n"
                f"- **Significant Anomaly Features**: {top_names}\n"
                f"- **Physical Failure Mode**: Premature avalanche breakdown multiplication or transconductance degradation resulting from deep-level trap density in space-charge region. Discard component from flight qualification."
            )

    def get_population_curves(self, model_type: str) -> Dict[str, Any]:
        """Returns sampled curve points from population baseline for visualization."""
        m_key = model_type.lower().replace("-", "").replace("_", "")
        if "break" in m_key:
            m_key = "breakdown"
        elif "leak" in m_key:
            m_key = "leakage"
        elif "turn" in m_key or "on" in m_key:
            m_key = "turnon"
        else:
            m_key = "breakdown"

        baseline = self._models_data.get(m_key)
        if not baseline:
            self._models_data[m_key] = self._build_model_baseline(m_key, MODEL_MAP[m_key])
            baseline = self._models_data[m_key]

        cfg = baseline["config"]
        curves_payload = []
        for c in baseline["curves"]:
            x_raw = c["x"]
            y_raw = c["y"]
            step = max(1, len(x_raw) // 40)
            curves_payload.append({
                "curve_id": c["curve_id"],
                "decision": c.get("decision", "PASS"),
                "dynamic_score": c.get("dynamic_score", 1.0),
                "combined_score": c.get("combined_score", 0.2),
                "x": [round(x_raw[i], 3) for i in range(0, len(x_raw), step)],
                "y": [round(y_raw[i], 6) for i in range(0, len(y_raw), step)],
                "full_x": x_raw,
                "full_y": y_raw
            })

        return {
            "model_type": m_key,
            "display_name": cfg["display_name"],
            "x_unit": cfg["x_unit"],
            "y_unit": cfg["y_unit"],
            "total_curves": len(curves_payload),
            "dynamic_threshold": round(baseline["dynamic_threshold"], 3),
            "feature_stats": baseline["feature_stats"],
            "curves": curves_payload
        }
