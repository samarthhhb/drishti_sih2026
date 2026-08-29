#!/usr/bin/env python3
"""
SIH26170 - Semiconductor Component Screening & Anomaly Detection
Model Dynamics & Output Discrepancy Explanation Chatbot
=============================================================================
An API-based free chatbot (with zero-dependency fallback) specialized in:
1. Explaining semiconductor ML model dynamics (Breakdown, Leakage IV, Turn-On).
2. Explaining and diagnosing differences between ML Model Output (Y_model)
   and User-Specified / Observed Output (Y_user).
3. Providing physics-grounded degradation analysis (impact ionization, SRH
   recombination, threshold shift, thermal runaway, oxide trapping).
4. Generating SIH-26 Risk Assessment decisions (PASS, HOLD, REJECT).

Supported Free API Providers:
- Google Gemini API (Free tier: gemini-2.0-flash, gemini-1.5-flash)
- Groq API (Free fast tier: llama-3.3-70b-versatile, llama3-8b-8192)
- Hugging Face Inference API / OpenRouter (Free tier)
- Local Ollama (localhost:11434)
- Built-in Offline Physics & SIH-26 Expert System (100% Free, 0 API Key needed)
"""

import os
import sys
import json
import math
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, Optional, List, Tuple

# =============================================================================
# MODEL DOMAIN KNOWLEDGE BASE & PHYSICS CONSTANTS
# =============================================================================

MODEL_DEFINITIONS = {
    "breakdown": {
        "name": "Breakdown Model",
        "input_param": "Collector-Emitter Voltage",
        "input_unit": "V",
        "output_param": "Leakage Current",
        "output_unit": "microAmpere",
        "typical_input_range": (0.0, 650.0),
        "typical_output_range": (0.0, 150.0),
        "nominal_breakdown_voltage": 600.0,
        "description": "Models collector-emitter leakage current across applied collector-emitter voltage.",
        "key_dynamics": [
            "Sub-breakdown region: Thermal generation of electron-hole pairs yields nA-level leakage.",
            "Breakdown knee: Impact ionization causes carrier multiplication at high electric field.",
            "Aging: Guard ring oxide damage and edge termination micro-cracks lower breakdown voltage and increase leakage."
        ]
    },
    "leakage": {
        "name": "Leakage IV Model",
        "input_param": "Applied Voltage",
        "input_unit": "V",
        "output_param": "Leakage Current",
        "output_unit": "microAmpere",
        "typical_input_range": (0.0, 600.0),
        "typical_output_range": (0.0, 10.0),
        "nominal_limit": 50.0,
        "description": "Models reverse leakage current as a function of applied bias voltage.",
        "key_dynamics": [
            "Ohmic & sub-threshold leakage: Governed by Shockley-Read-Hall (SRH) generation-recombination.",
            "High-field leakage: Poole-Frenkel emission and Fowler-Nordheim field emission.",
            "Latent Defect Indication: Increased leakage at low voltage signifies dielectric thinning or localized precipitates."
        ]
    },
    "turnon": {
        "name": "Turn-On Model",
        "input_param": "Gate Voltage",
        "input_unit": "V",
        "output_param": "Collector Current",
        "output_unit": "microAmpere",
        "typical_input_range": (0.0, 15.0),
        "typical_output_range": (0.0, 250.0),
        "nominal_vth": 4.0,
        "description": "Models IGBT transfer characteristics (Gate Voltage vs Collector Current).",
        "key_dynamics": [
            "Sub-threshold: Near-zero collector current.",
            "Active Region: Drift current through inversion layer modulated by gate field.",
            "Degradation: Hot carrier injection traps electrons in gate oxide, causing positive threshold voltage shift."
        ]
    }
}

SYSTEM_PROMPT = """You are 'Drishti AI' for Project SIH26170 (Semiconductor Stress Screening).
IMPORTANT INSTRUCTION: Always provide CONCISE, DIRECT, and HIGH-IMPACT answers. Avoid conversational filler or long preambles.
For discrepancy explanations, format in 3 crisp bullet points:
1. **Discrepancy**: Exact drift magnitude (% and ratio).
2. **Physics Cause**: Key semiconductor mechanism (e.g. Avalanche, SRH, oxide charge trapping ΔVth, solder fatigue).
3. **Screening Verdict**: PASS / HOLD / REJECT with immediate next validation step.
"""


# =============================================================================
# DISCREPANCY ANALYSIS & PHYSICAL DIAGNOSTIC ENGINE
# =============================================================================

class DiscrepancyAnalyzer:
    """Computes quantitative metrics and physics-grounded diagnostics for model vs user output."""

    @staticmethod
    def format_val(val: float, unit: str = "") -> str:
        """Format number in scientific or standard notation depending on magnitude."""
        if abs(val) == 0:
            return f"0.00 {unit}".strip()
        if abs(val) < 1e-3 or abs(val) >= 1e5:
            return f"{val:.4e} {unit}".strip()
        return f"{val:.4f} {unit}".strip()

    @classmethod
    def analyze(
        cls,
        model_type: str,
        x_input: float,
        y_model: float,
        y_user: float,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform complete quantitative and physical discrepancy analysis.
        """
        m_key = model_type.lower().replace("-", "").replace("_", "").replace(" ", "")
        if "break" in m_key:
            model_info = MODEL_DEFINITIONS["breakdown"]
            category = "breakdown"
        elif "leak" in m_key:
            model_info = MODEL_DEFINITIONS["leakage"]
            category = "leakage"
        elif "turn" in m_key or "on" in m_key:
            model_info = MODEL_DEFINITIONS["turnon"]
            category = "turnon"
        else:
            model_info = {
                "name": f"Custom Model ({model_type})",
                "input_param": "Input_X",
                "input_unit": "units",
                "output_param": "Output_Y",
                "output_unit": "units",
                "typical_input_range": (0.0, 1000.0),
                "typical_output_range": (0.0, 1000.0),
                "description": "User-defined semiconductor regression model.",
                "key_dynamics": ["General semiconductor transfer characteristic."]
            }
            category = "custom"

        # Quantitative metrics
        delta = y_user - y_model
        abs_delta = abs(delta)
        
        # Percentage difference
        denominator = abs(y_model) if abs(y_model) > 1e-18 else 1e-18
        pct_diff = (delta / denominator) * 100.0
        abs_pct_diff = abs(pct_diff)
        
        # Magnitude factor (e.g. 3.5x higher)
        ratio = (y_user / y_model) if y_model != 0 else float("inf")

        # Direction
        if abs_pct_diff < 3.0:
            direction = "NOMINAL_ALIGNMENT"
            direction_desc = "User output closely matches the model prediction."
        elif delta > 0:
            direction = "USER_HIGHER_THAN_MODEL"
            direction_desc = f"Observed output is HIGHER than model prediction (+{abs_pct_diff:.1f}%)."
        else:
            direction = "USER_LOWER_THAN_MODEL"
            direction_desc = f"Observed output is LOWER than model prediction (-{abs_pct_diff:.1f}%)."

        # Risk & Physics Classification
        risk_decision, severity, physics_causes, recommendations = cls._classify_physics(
            category, x_input, y_model, y_user, delta, pct_diff, abs_pct_diff, ratio
        )

        return {
            "model_type": category,
            "model_name": model_info["name"],
            "input_param": model_info["input_param"],
            "input_unit": model_info["input_unit"],
            "output_param": model_info["output_param"],
            "output_unit": model_info["output_unit"],
            "x_input": x_input,
            "y_model": y_model,
            "y_user": y_user,
            "delta": delta,
            "abs_delta": abs_delta,
            "pct_diff": pct_diff,
            "abs_pct_diff": abs_pct_diff,
            "ratio": ratio,
            "direction": direction,
            "direction_desc": direction_desc,
            "risk_decision": risk_decision,  # PASS, HOLD, REJECT
            "severity": severity,          # LOW, MODERATE, HIGH, CRITICAL
            "physics_causes": physics_causes,
            "recommendations": recommendations,
            "model_dynamics_summary": model_info.get("key_dynamics", [])
        }

    @staticmethod
    def _classify_physics(
        category: str,
        x: float,
        y_model: float,
        y_user: float,
        delta: float,
        pct_diff: float,
        abs_pct: float,
        ratio: float
    ) -> Tuple[str, str, List[str], List[str]]:
        """Determine physical causes, screening decision, and recommendations based on semiconductor physics."""
        causes = []
        recs = []

        if abs_pct <= 10.0:
            decision = "PASS"
            severity = "LOW"
            causes.append("Normal manufacturing process variation and measurement sensor noise within ±10% tolerance.")
            causes.append("Device operates well within healthy statistical population baseline.")
            recs.append("Proceed with normal screening workflow.")
            recs.append("Log telemetry for longitudinal lot tracking.")
            return decision, severity, causes, recs

        if category == "breakdown":
            # Breakdown: X is Vce, Y is Leakage Ic
            if delta > 0:  # User observed higher leakage than model predicted at voltage X
                if x >= 500.0 or abs_pct > 100.0 or y_user > 1e-5:
                    decision = "REJECT"
                    severity = "CRITICAL" if abs_pct > 300.0 else "HIGH"
                    causes.append("Premature Avalanche Breakdown: Guard ring oxide degradation or field plate micro-defects triggering localized impact ionization below nominal V_BR.")
                    causes.append("High Surface Leakage: Passivation layer cracking or ionic contamination along the collector-emitter edge termination.")
                    causes.append("Thermal Runaway Warning: Intrinsic carrier concentration n_i multiplied by localized hot-spot Joule heating.")
                    recs.append("REJECT component from flight/high-reliability batch (high latent failure risk).")
                    recs.append("Perform full IV curve sweep from 0V to rated V_BR to identify exact breakdown knee shift.")
                    recs.append("Conduct emission microscopy (EMMI) or thermal IR imaging to locate hot-spot localization.")
                else:
                    decision = "HOLD"
                    severity = "MODERATE"
                    causes.append("Early onset of pre-breakdown leakage drift due to thermal stress or crystal lattice point defects.")
                    causes.append("Possible temperature divergence: Tested component junction temp may be higher than baseline calibration (25°C).")
                    recs.append("HOLD for secondary stress screening (burn-in re-test at 125°C).")
                    recs.append("Verify ambient and case temperature calibration.")
            else:  # delta < 0 (user observed lower leakage than model)
                decision = "HOLD" if abs_pct > 50.0 else "PASS"
                severity = "LOW" if abs_pct <= 50.0 else "MODERATE"
                causes.append("Model over-estimation at sub-breakdown voltage or superior die quality with lower defect density.")
                causes.append("Measurement instrument range / compliance limit saturation.")
                recs.append("Verify instrument sensitivity threshold (femto-ammeter vs standard SMU).")
                recs.append("Refine regression model calibration in the low-field sub-threshold region.")

        elif category == "leakage":
            # Leakage: X is Applied Voltage, Y is Leakage Current
            if delta > 0:
                if y_user >= 4e-5 or abs_pct > 200.0 or ratio > 3.0:
                    decision = "REJECT"
                    severity = "HIGH"
                    causes.append("Latent Die Degradation: Increased Shockley-Read-Hall (SRH) generation centers due to metallic impurities or crystal dislocation loops.")
                    causes.append("Gate-to-Emitter / Collector Oxide Thinning: Enhanced Poole-Frenkel or Fowler-Nordheim field emission.")
                    causes.append("Package Solder Delamination: Thermal resistance (Rth_jc) increase leading to higher junction temperature and exponential leakage surge.")
                    recs.append("REJECT from active flight assembly; route to destructive physical analysis (DPA).")
                    recs.append("Apply high-temperature reverse bias (HTRB) stress screening to evaluate drift trajectory.")
                elif abs_pct > 25.0:
                    decision = "HOLD"
                    severity = "MODERATE"
                    causes.append("Elevated leakage relative to healthy lot population, indicating early thermal aging or surface state traps.")
                    causes.append("Temperature-adjusted leakage discrepancy: Verify if device is undergoing self-heating.")
                    recs.append("Quarantine component under HOLD status.")
                    recs.append("Compute safety-slope drift comparison against historical aging trajectories.")
                else:
                    decision = "PASS"
                    severity = "LOW"
                    causes.append("Mild drift within acceptable environmental stress screening band.")
                    recs.append("Monitor for future drift acceleration.")
            else:
                decision = "PASS"
                severity = "LOW"
                causes.append("Leakage is lower than predicted, indicating ultra-low defect density or cooler operating die.")
                recs.append("No immediate reliability risk detected.")

        elif category == "turnon":
            # TurnOn: X is Vge (Gate Voltage), Y is Collector Current Ic
            if delta < 0:  # User observed LESS current than model predicted for given Vge
                if abs_pct > 50.0 or (x >= 6.0 and y_user < 0.1):
                    decision = "REJECT"
                    severity = "HIGH"
                    causes.append("Positive Threshold Voltage Shift (ΔVth > 0): Negative charge / electron trapping in the gate SiO2 dielectric.")
                    causes.append("Transconductance (gm) Collapse: Severe degradation of channel electron mobility (μ_eff) from interface state generation (Dit).")
                    causes.append("Bond Wire Lift-off / High On-State Resistance: Partial emitter bond wire detachment increasing series parasitic resistance.")
                    recs.append("REJECT component due to increased conduction losses and risk of thermal destruction.")
                    recs.append("Perform Vth measurement at constant Ic = 1mA and measure R_on / Vce(sat).")
                else:
                    decision = "HOLD"
                    severity = "MODERATE"
                    causes.append("Moderate Vth drift or slight transconductance drop due to gate electrical overstress or aging.")
                    recs.append("HOLD for gate-stress test (HTGB - High Temperature Gate Bias).")
                    recs.append("Track gate leakage (Iges) to ensure dielectric integrity.")
            else:  # User observed MORE current than model predicted
                if x < 4.0 and y_user > 1.0:
                    decision = "REJECT"
                    severity = "CRITICAL"
                    causes.append("Negative Threshold Voltage Shift / Parasitic Inversion: Device turns on prematurely at sub-threshold gate bias.")
                    causes.append("Risk of uncommanded turn-on, shoot-through in half-bridge configurations, or parasitic thyristor latch-up.")
                    recs.append("IMMEDIATE REJECT. Do not use in power conversion stages.")
                else:
                    decision = "PASS" if abs_pct < 30.0 else "HOLD"
                    severity = "LOW" if abs_pct < 30.0 else "MODERATE"
                    causes.append("High channel mobility or model saturation under-fitting at high gate drive.")
                    recs.append("Verify gate drive voltage calibration.")

        else:  # Custom model
            if abs_pct > 100.0:
                decision = "REJECT"
                severity = "HIGH"
                causes.append("Major deviation from ML model prediction (>100% error).")
                recs.append("Flag for manual engineering review and recalibrate regression model.")
            elif abs_pct > 25.0:
                decision = "HOLD"
                severity = "MODERATE"
                causes.append("Moderate statistical divergence from expected response.")
                recs.append("Quarantine component and evaluate historical lot drift.")
            else:
                decision = "PASS"
                severity = "LOW"
                causes.append("Within statistical baseline limits.")
                recs.append("Accept component.")

        return decision, severity, causes, recs


# =============================================================================
# FREE API CONNECTORS & LLM CLIENT (Stdlib HTTP - Zero Dependencies)
# =============================================================================

class FreeAPIClient:
    """
    Handles API calls to free LLM providers using pure standard library urllib.
    Supports:
    1. Groq Free Tier (llama-3.3-70b-versatile, llama3-8b-8192)
    2. Google Gemini Free Tier (gemini-2.0-flash, gemini-1.5-flash)
    3. Hugging Face Inference API / OpenRouter
    4. Local Ollama
    """

    def __init__(self, provider: str = "auto", api_key: Optional[str] = None):
        self._load_env_file()
        self.provider = provider.lower()
        self.api_key = api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("HF_TOKEN") or os.environ.get("OPENROUTER_API_KEY")
        self._detect_provider()

    @staticmethod
    def _load_env_file():
        """Lightweight .env loader (zero dependencies)."""
        from pathlib import Path
        for p in [Path.cwd() / ".env", Path(__file__).resolve().parent.parent / ".env"]:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                k, v = k.strip(), v.strip().strip('"').strip("'")
                                if k not in os.environ:
                                    os.environ[k] = v
                except Exception:
                    pass

    def _detect_provider(self):
        if self.provider == "auto":
            if os.environ.get("GROQ_API_KEY"):
                self.provider = "groq"
                self.api_key = os.environ.get("GROQ_API_KEY")
            elif os.environ.get("GEMINI_API_KEY"):
                self.provider = "gemini"
                self.api_key = os.environ.get("GEMINI_API_KEY")
            elif os.environ.get("OPENROUTER_API_KEY"):
                self.provider = "openrouter"
                self.api_key = os.environ.get("OPENROUTER_API_KEY")
            elif os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY"):
                self.provider = "huggingface"
                self.api_key = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
            else:
                self.provider = "offline"

    def set_config(self, provider: str, api_key: Optional[str] = None):
        self.provider = provider.lower()
        self.api_key = api_key

    def generate(self, prompt: str, system_instruction: str = SYSTEM_PROMPT) -> str:
        """Generate response from selected API provider or fall back to offline engine."""
        if not self.api_key and self.provider not in ("ollama", "offline"):
            # Check if any env var is set
            self._detect_provider()

        if self.provider == "gemini":
            return self._call_gemini(prompt, system_instruction)
        elif self.provider == "groq":
            return self._call_groq(prompt, system_instruction)
        elif self.provider == "openrouter":
            return self._call_openrouter(prompt, system_instruction)
        elif self.provider == "huggingface":
            return self._call_huggingface(prompt, system_instruction)
        elif self.provider == "ollama":
            return self._call_ollama(prompt, system_instruction)
        else:
            return self._call_offline(prompt)

    def _call_gemini(self, prompt: str, system_instruction: str) -> str:
        """Call Google Gemini API (Free Tier)."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        
        # Try gemini-2.0-flash first, fallback to gemini-1.5-flash
        models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        last_err = None
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": f"{system_instruction}\n\nUser Request / Query:\n{prompt}"}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 2048,
                }
            }
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=20) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    candidates = res_data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"]
            except Exception as e:
                last_err = e
                continue
        raise RuntimeError(f"Gemini API error: {last_err}")

    def _call_groq(self, prompt: str, system_instruction: str) -> str:
        """Call Groq API (Free Tier)."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set.")
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 2048
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Groq API error: {e}")

    def _call_openrouter(self, prompt: str, system_instruction: str) -> str:
        """Call OpenRouter Free Models API."""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not set.")
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"OpenRouter API error: {e}")

    def _call_huggingface(self, prompt: str, system_instruction: str) -> str:
        """Call Hugging Face Inference API."""
        if not self.api_key:
            raise ValueError("HF_TOKEN is not set.")
        url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
        payload = {
            "inputs": f"<s>[INST] {system_instruction}\n\n{prompt} [/INST]",
            "parameters": {"max_new_tokens": 1024, "temperature": 0.2}
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                if isinstance(res_data, list) and len(res_data) > 0:
                    text = res_data[0].get("generated_text", "")
                    if "[/INST]" in text:
                        return text.split("[/INST]")[-1].strip()
                    return text
                return str(res_data)
        except Exception as e:
            raise RuntimeError(f"HuggingFace API error: {e}")

    def _call_ollama(self, prompt: str, system_instruction: str) -> str:
        """Call Local Ollama API (localhost:11434)."""
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3.2",
            "prompt": f"{system_instruction}\n\n{prompt}",
            "stream": False
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data.get("response", "")
        except Exception as e:
            raise RuntimeError(f"Ollama local connection error: {e}")

    def _call_offline(self, prompt: str) -> str:
        """Offline fallback - handled by expert rule-based generator."""
        return "Offline Mode Active. Use `explain_discrepancy()` for comprehensive semiconductor physics diagnostics."


# =============================================================================
# MAIN CHATBOT CLASS: SEMICONDUCTOR MODEL EXPLAINER
# =============================================================================

class SemiconductorChatbot:
    """
    Main Chatbot engine combining:
    - Quantitative Discrepancy Analyzer
    - Semiconductor Physical Diagnostics
    - Multi-provider Free AI API generation (with smart offline fallback)
    - Interactive Chat conversation management
    """

    def __init__(self, provider: str = "auto", api_key: Optional[str] = None):
        self.api_client = FreeAPIClient(provider=provider, api_key=api_key)
        self.analyzer = DiscrepancyAnalyzer()
        self.history: List[Dict[str, str]] = []

    def set_api_key(self, provider: str, api_key: str):
        """Update active API provider and key."""
        self.api_client.set_config(provider, api_key)

    def explain_discrepancy(
        self,
        model_type: str,
        x_input: float,
        y_model: float,
        y_user: float,
        component_id: str = "DUT-IGBT-01",
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Explain the discrepancy between Model Output and User Said Output.
        Returns a rich structured diagnostic dictionary and natural language explanation.
        """
        # Step 1: Compute mathematical & physical metrics
        diag = self.analyzer.analyze(model_type, x_input, y_model, y_user)
        
        # Step 2: Build detailed diagnostic report
        report_md = self._format_expert_report(diag, component_id)
        
        # Step 3: If AI API is available and requested, enhance with generative insights
        ai_explanation = None
        if use_ai and self.api_client.provider != "offline":
            try:
                ai_prompt = f"""
Analyze this discrepancy concisely for {component_id} ({diag['model_name']}):
Input: {DiscrepancyAnalyzer.format_val(x_input, diag['input_unit'])}
Model Prediction (Y_model): {DiscrepancyAnalyzer.format_val(y_model, diag['output_unit'])}
User Measurement (Y_user): {DiscrepancyAnalyzer.format_val(y_user, diag['output_unit'])}
Deviation: {diag['pct_diff']:+.2f}% ({diag['ratio']:.2f}x) | Decision: {diag['risk_decision']}

Provide a CONCISE 3-point response:
1. **Deviation Summary**: Magnitude and direction.
2. **Semiconductor Failure Physics**: Root cause (e.g. Avalanche, SRH, oxide charge trapping ΔVth, solder fatigue).
3. **Screening Action**: Decision ({diag['risk_decision']}) and next test step.
Keep it strictly under 100 words.
"""
                ai_explanation = self.api_client.generate(ai_prompt)
            except Exception as e:
                ai_explanation = None  # Seamless fallback to built-in report

        diag["component_id"] = component_id
        diag["expert_report"] = report_md
        diag["ai_explanation"] = ai_explanation
        diag["final_explanation"] = ai_explanation if (ai_explanation and not ai_explanation.startswith("[Note:")) else report_md

        return diag

    def chat(self, user_message: str) -> str:
        """
        Conversational chat interface for answering questions about model dynamics,
        IGBT physics, training datasets, and screening criteria.
        """
        # Check if the user is asking about a specific discrepancy calculation
        parsed_discrepancy = self._try_parse_discrepancy_query(user_message)
        if parsed_discrepancy:
            m_type, x_in, y_mod, y_usr = parsed_discrepancy
            res = self.explain_discrepancy(m_type, x_in, y_mod, y_usr)
            reply = res["final_explanation"]
            self.history.append({"role": "user", "content": user_message})
            self.history.append({"role": "assistant", "content": reply})
            return reply

        # Standard conversational query
        self.history.append({"role": "user", "content": user_message})
        
        if self.api_client.provider != "offline":
            try:
                # Build context from history
                conv_history = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in self.history[-6:]])
                prompt = f"""Conversation History:\n{conv_history}\n\nPlease answer the user's latest query accurately using semiconductor physics and SIH-26 context."""
                reply = self.api_client.generate(prompt)
                self.history.append({"role": "assistant", "content": reply})
                return reply
            except Exception as e:
                pass  # Fall back to rule-based conversation helper

        # Offline fallback response generator
        reply = self._generate_offline_chat_response(user_message)
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def _format_expert_report(self, diag: Dict[str, Any], component_id: str) -> str:
        """Format a concise, high-impact diagnostic report."""
        badge = " PASS" if diag["risk_decision"] == "PASS" else (" HOLD" if diag["risk_decision"] == "HOLD" else " REJECT")
        
        report = []
        report.append(f"**Screening Verdict: {badge}** (`{component_id}` • {diag['model_name']})\n")
        report.append(f"1. **Deviation**: `{diag['pct_diff']:+.2f}%` drift ({diag['ratio']:.2f}x baseline). {diag['direction_desc']}")
        
        primary_cause = diag["physics_causes"][0] if diag["physics_causes"] else "Nominal operation within lot bounds."
        report.append(f"2. **Physics Cause**: {primary_cause}")
        
        primary_rec = diag["recommendations"][0] if diag["recommendations"] else "Continue standard screening."
        report.append(f"3. **Next Action**: {primary_rec}")

        return "\n".join(report)

    def _generate_offline_chat_response(self, query: str) -> str:
        """Rule-based intelligent physics knowledge engine for offline operation."""
        q = query.lower()
        if "breakdown" in q:
            return (
                "###  Breakdown Model Dynamics (IRG4BC30K IGBT)\n"
                "- **Dataset**: NASA Accelerated Aging Dataset (`final_data/dataset/Breakdown.csv`).\n"
                "- **Input**: Collector-Emitter Voltage ($V_{ce}$, Volts).\n"
                "- **Output**: Collector Leakage Current ($I_c$, Amperes).\n"
                "- **Physics**: At low $V_{ce}$, thermal generation causes minor nA leakage. At high electric fields near $V_{BR}$ (~600V), "
                "avalanche impact ionization multiplies carriers exponentially.\n"
                "- **Discrepancy Meaning**: If user output is higher than model prediction at sub-breakdown voltages, the device suffers from guard ring degradation or hot-carrier stress."
            )
        elif "leakage" in q:
            return (
                "###  Leakage Current IV Model Dynamics\n"
                "- **Dataset**: `final_data/dataset/LeakageIV.csv`.\n"
                "- **Input**: Applied Voltage ($V$, Volts).\n"
                "- **Output**: Leakage Current ($I_{leak}$, Amperes).\n"
                r"- **Physics**: Governed by Shockley-Read-Hall (SRH) generation-recombination and field emission ($I_{leak} \propto T^2 e^{-E_g/2kT}$)." "\n"
                "- **Screening Significance**: Components passing static datasheet limits (<50μA) but showing abnormal population deviation (e.g. 45μA vs lot average 10μA) are flagged for latent defect risk."
            )
        elif "turn" in q or "on" in q or "vge" in q or "vth" in q:
            return (
                "###  Turn-On Characteristics Model Dynamics\n"
                "- **Dataset**: `final_data/dataset/TurnOn.csv`.\n"
                "- **Input**: Gate Voltage ($V_{ge}$, Volts).\n"
                "- **Output**: Collector Current ($I_c$, Amperes).\n"
                r"- **Physics**: Above threshold voltage $V_{th}$ (~4.0V), inversion channel forms. Gate oxide charge trapping shifts $V_{th}$, while interface states degrade transconductance ($g_m$)." "\n"
                "- **Discrepancy Meaning**: If user current is lower than model, positive $V_{th}$ drift is present, causing higher switching losses."
            )
        elif "explain" in q or "diff" in q or "vs" in q or "compare" in q:
            return (
                "To explain a discrepancy between model prediction and observed measurement, please provide:\n"
                "1. **Model Name** (`breakdown`, `leakage`, or `turnon`)\n"
                "2. **Input Value** (e.g. `Vce = 550V` or `Gate Voltage = 5V`)\n"
                "3. **Model Predicted Output** ($Y_{model}$)\n"
                "4. **User Observed Output** ($Y_{user}$)\n\n"
                "*Example command*: `explain breakdown x=550 y_model=3.8e-6 y_user=1.2e-5`"
            )
        else:
            return (
                "###  Drishti AI - Model Dynamics & Output Discrepancy Assistant\n"
                "I am ready to help you analyze semiconductor models and explain discrepancies between model predictions and user-observed ground truth.\n\n"
                "**Capabilities**:\n"
                "-  Explain model physics for **Breakdown**, **Leakage IV**, and **Turn-On** characteristics.\n"
                r"-  Diagnose physical failure modes (impact ionization, SRH recombination, $\Delta V_{th}$, solder fatigue)." "\n"
                "-  Classify screening decisions (**PASS / HOLD / REJECT**).\n"
                "-  Free API support for Gemini, Groq, OpenRouter, and local Ollama.\n\n"
                "*Try asking: 'Explain the difference between model output 3.8uA and user output 12uA at 550V in breakdown model'*"
            )

    @staticmethod
    def _try_parse_discrepancy_query(query: str) -> Optional[Tuple[str, float, float, float]]:
        """Attempt to extract (model_type, x, y_model, y_user) from natural language query or structured command."""
        import re
        q = query.lower()
        # Pattern 1: explicit keywords like x=... y_model=... y_user=...
        m_type = "breakdown" if "break" in q else ("leakage" if "leak" in q else ("turnon" if ("turn" in q or "vge" in q) else "custom"))
        
        # Regex for numbers including scientific notation
        num_pattern = r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?"
        
        # Check for structured format: x=... y_model=... y_user=...
        x_match = re.search(r"(?:x|input|voltage|vce|vge)\s*[:=]\s*(" + num_pattern + ")", q)
        ym_match = re.search(r"(?:y_model|model|predicted|pred)\s*[:=]\s*(" + num_pattern + ")", q)
        yu_match = re.search(r"(?:y_user|user|observed|actual|ground_truth)\s*[:=]\s*(" + num_pattern + ")", q)

        if x_match and ym_match and yu_match:
            try:
                return m_type, float(x_match.group(1)), float(ym_match.group(1)), float(yu_match.group(1))
            except ValueError:
                pass

        return None


# =============================================================================
# INTERACTIVE CLI INTERFACE
# =============================================================================

def run_cli():
    """Run interactive terminal chatbot."""
    bot = SemiconductorChatbot()
    
    print("=" * 75)
    print("  SIH26170 - Semiconductor Model Explainer & Discrepancy Chatbot")
    print("=" * 75)
    print("Free AI API Support: Gemini Free Tier | Groq Free Tier | Offline Physics Engine")
    print("Active Mode:", f"{bot.api_client.provider.upper()} API" if bot.api_client.provider != "offline" else "Built-in Physics Engine (100% Free / Offline)")
    print("-" * 75)
    print("Commands:")
    print("  1. 'explain'   : Run structured discrepancy explanation wizard")
    print("  2. 'preset'    : Test preset NASA IGBT aging discrepancy test cases")
    print("  3. 'api'       : Configure API Key (Gemini, Groq, OpenRouter)")
    print("  4. 'models'    : View details of Breakdown, Leakage, and Turn-On models")
    print("  5. 'quit'/'exit': Exit the chatbot")
    print("Or simply type any question to chat!")
    print("=" * 75)

    while True:
        try:
            user_input = input("\n User > ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("\n Exiting Semiconductor Model Explainer. Goodbye!")
                break

            elif user_input.lower() == "api":
                print("\n--- Configure API Key ---")
                print("Available Providers: [1] Gemini (Free) | [2] Groq (Free) | [3] OpenRouter | [4] Offline")
                choice = input("Select provider (1-4): ").strip()
                if choice == "1":
                    key = input("Enter GEMINI_API_KEY: ").strip()
                    bot.set_api_key("gemini", key)
                    print(" Gemini API provider configured.")
                elif choice == "2":
                    key = input("Enter GROQ_API_KEY: ").strip()
                    bot.set_api_key("groq", key)
                    print(" Groq API provider configured.")
                elif choice == "3":
                    key = input("Enter OPENROUTER_API_KEY: ").strip()
                    bot.set_api_key("openrouter", key)
                    print(" OpenRouter provider configured.")
                else:
                    bot.set_api_key("offline", "")
                    print(" Switched to 100% Free Offline Physics Engine.")

            elif user_input.lower() == "models":
                print("\n" + "=" * 70)
                for k, v in MODEL_DEFINITIONS.items():
                    print(f" {v['name']}")
                    print(f"   - Input : {v['input_param']} ({v['input_unit']})")
                    print(f"   - Output: {v['output_param']} ({v['output_unit']})")
                    print(f"   - Info  : {v['description']}")
                print("=" * 70)

            elif user_input.lower() == "preset":
                print("\n--- Preset NASA IGBT Aging Discrepancy Test Cases ---")
                print("1. [Breakdown] Aged IGBT showing premature avalanche breakdown at 550V")
                print("2. [Leakage] Latent defect: High leakage (45uA vs 10uA model baseline at 25V)")
                print("3. [Turn-On] Gate oxide charge trapping: Positive Vth shift at Vge=5V")
                p_choice = input("Select preset (1-3): ").strip()
                
                if p_choice == "1":
                    diag = bot.explain_discrepancy("breakdown", 550.0, 3.87e-6, 1.25e-5, component_id="NASA-IGBT-Part-12")
                elif p_choice == "2":
                    diag = bot.explain_discrepancy("leakage", 25.0, 1.05e-5, 4.50e-5, component_id="NASA-IGBT-Part-18")
                else:
                    diag = bot.explain_discrepancy("turnon", 5.0, 1.85, 0.42, component_id="NASA-IGBT-Part-14")
                
                print("\n" + diag["final_explanation"])

            elif user_input.lower() == "explain":
                print("\n--- Model Discrepancy Analysis Wizard ---")
                print("Select Model: [1] Breakdown (Vce vs Ic) | [2] Leakage IV | [3] Turn-On (Vge vs Ic)")
                m_choice = input("Choice (1-3) [default=1]: ").strip() or "1"
                m_type = "breakdown" if m_choice == "1" else ("leakage" if m_choice == "2" else "turnon")
                
                x_val = float(input(f"Enter Input Value ({MODEL_DEFINITIONS[m_type]['input_param']}): ").strip())
                y_mod = float(input("Enter Model Predicted Output (Y_model): ").strip())
                y_usr = float(input("Enter User Said / Observed Output (Y_user): ").strip())
                cid = input("Enter Component ID [default=DUT-01]: ").strip() or "DUT-01"

                print("\n Analyzing discrepancy and evaluating semiconductor physics...")
                diag = bot.explain_discrepancy(m_type, x_val, y_mod, y_usr, component_id=cid)
                print("\n" + diag["final_explanation"])

            else:
                response = bot.chat(user_input)
                print(f"\n Drishti AI:\n{response}")

        except KeyboardInterrupt:
            print("\n Exiting...")
            break
        except Exception as e:
            print(f"\n Error: {e}")


if __name__ == "__main__":
    run_cli()
