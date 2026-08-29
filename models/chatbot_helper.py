#!/usr/bin/env python3
"""
SIH26170 - Chatbot Helper Module for Jupyter Notebooks & Python Scripts
=============================================================================
Provides quick helper functions to interact with the Semiconductor Model Explainer
and Discrepancy Chatbot directly within Jupyter Notebooks and Python workflows.

Example in a notebook:
---------------------
    from models.chatbot_helper import explain_discrepancy, chat, set_api_key

    # Explain difference between model prediction and measured value:
    explain_discrepancy('breakdown', x_input=550.0, y_model=3.87e-6, y_user=1.25e-5)

    # Chat with the assistant:
    chat("Why does leakage current increase with temperature?")
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure models directory is in path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from chatbot import SemiconductorChatbot, MODEL_DEFINITIONS, DiscrepancyAnalyzer

# Shared singleton chatbot instance
_default_bot = SemiconductorChatbot()


def set_api_key(provider: str, api_key: str):
    """
    Configure active AI API provider and key.
    
    Args:
        provider: 'gemini', 'groq', 'openrouter', 'huggingface', 'ollama', or 'offline'
        api_key: The API Key string (optional if using offline/ollama)
    """
    _default_bot.set_api_key(provider, api_key)
    print(f" Configured AI Engine: {provider.upper()}")


def explain_discrepancy(
    model_type: str,
    x_input: float,
    y_model: float,
    y_user: float,
    component_id: str = "DUT-01",
    use_ai: bool = True,
    display_output: bool = True
) -> Dict[str, Any]:
    """
    Diagnose and explain discrepancy between Model Output (Y_model) and Observed Output (Y_user).
    
    Args:
        model_type: 'breakdown', 'leakage', 'turnon', or custom
        x_input: Value of test condition / input voltage
        y_model: Value predicted by the Machine Learning model
        y_user: Observed / measured / ground-truth output from component test
        component_id: Identifier for the tested component (e.g. 'NASA-IGBT-Part-12')
        use_ai: Whether to use configured Free LLM API for generative explanation
        display_output: If True, renders markdown in Jupyter Notebook or prints to stdout
        
    Returns:
        Dictionary containing quantitative metrics, physics failure modes, recommendations, and report.
    """
    diag = _default_bot.explain_discrepancy(
        model_type=model_type,
        x_input=x_input,
        y_model=y_model,
        y_user=y_user,
        component_id=component_id,
        use_ai=use_ai
    )

    if display_output:
        _render_markdown(diag["final_explanation"])

    return diag


def explain(
    model_type: str,
    x_input: float,
    y_model: float,
    y_user: float,
    component_id: str = "DUT-01",
    **kwargs
) -> Dict[str, Any]:
    """Shorthand alias for explain_discrepancy."""
    return explain_discrepancy(model_type, x_input, y_model, y_user, component_id=component_id, **kwargs)


def chat(message: str, display_output: bool = True) -> str:
    """
    Send a question or command to the Semiconductor Model Explainer AI.
    
    Args:
        message: Natural language query (e.g. "What is avalanche breakdown?", "explain leakage x=25 ym=10uA yu=45uA")
        display_output: If True, renders markdown or prints output
        
    Returns:
        Chatbot reply string.
    """
    reply = _default_bot.chat(message)
    if display_output:
        _render_markdown(reply)
    return reply


def _render_markdown(md_text: str):
    """Render markdown in Jupyter notebook if available, else standard print."""
    try:
        from IPython.display import display, Markdown
        display(Markdown(md_text))
    except ImportError:
        print("\n" + md_text + "\n")


if __name__ == "__main__":
    print("Testing chatbot_helper module...")
    res = explain("breakdown", 550.0, 3.87e-6, 1.25e-5, component_id="TEST-HELPER-01")
    print("\nTest completed successfully!")
