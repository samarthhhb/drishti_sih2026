#!/usr/bin/env python3
"""
SIH26170 - Semiconductor Model Explainer & Discrepancy Web Chatbot
=============================================================================
Zero-dependency web application server providing a modern, interactive web UI
for semiconductor model explanation, output discrepancy diagnosis, and AI chat.

Usage:
    python3 models/web_app.py [--port 8080] [--host 127.0.0.1]
"""

import os
import sys
import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Import the core chatbot engine with robust import resolution
try:
    from .chatbot import SemiconductorChatbot, MODEL_DEFINITIONS, DiscrepancyAnalyzer
except (ImportError, ValueError):
    try:
        from models.chatbot import SemiconductorChatbot, MODEL_DEFINITIONS, DiscrepancyAnalyzer
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from chatbot import SemiconductorChatbot, MODEL_DEFINITIONS, DiscrepancyAnalyzer

# Global chatbot instance
chatbot_instance = SemiconductorChatbot()

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIH26170 - Semiconductor Model Explainer & Discrepancy Chatbot</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0b0f19;
            --bg-secondary: #131b2e;
            --bg-card: #1c2640;
            --bg-card-hover: #233052;
            --border-color: #2b3a5c;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-cyan: #06b6d4;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
            --status-pass: #10b981;
            --status-hold: #f59e0b;
            --status-reject: #ef4444;
            --font-main: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--font-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            line-height: 1.5;
        }

        header {
            background: linear-gradient(90deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 50;
            backdrop-filter: blur(12px);
        }

        .logo-group {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-icon {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            width: 38px;
            height: 38px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.2rem;
            color: #fff;
            box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3);
        }

        .logo-text h1 {
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(90deg, #fff, #93c5fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-text p {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .api-badge {
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.4);
            color: #93c5fd;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .api-badge:hover {
            background: rgba(59, 130, 246, 0.25);
            border-color: var(--accent-blue);
        }

        .api-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
        }

        main {
            flex: 1;
            display: grid;
            grid-template-columns: 480px 1fr;
            gap: 1.5rem;
            padding: 1.5rem 2rem;
            max-width: 1600px;
            margin: 0 auto;
            width: 100%;
        }

        @media (max-width: 1024px) {
            main {
                grid-template-columns: 1fr;
            }
        }

        .panel {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .panel-header {
            padding: 1.1rem 1.4rem;
            border-bottom: 1px solid var(--border-color);
            background: rgba(28, 38, 64, 0.5);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .panel-header h2 {
            font-size: 1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            color: #e2e8f0;
        }

        .panel-body {
            padding: 1.4rem;
            overflow-y: auto;
            flex: 1;
        }

        /* Discrepancy Form Styles */
        .form-group {
            margin-bottom: 1.2rem;
        }

        .form-group label {
            display: block;
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .form-control, select {
            width: 100%;
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 10px 14px;
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .form-control:focus, select:focus {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.2);
        }

        .input-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }

        .btn {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            color: #fff;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            transition: transform 0.15s, opacity 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 14px rgba(6, 182, 212, 0.3);
        }

        .btn:hover {
            opacity: 0.95;
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-secondary {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            box-shadow: none;
            padding: 8px 12px;
            font-size: 0.8rem;
            width: auto;
        }

        .btn-secondary:hover {
            background: var(--bg-card-hover);
            border-color: var(--accent-cyan);
        }

        .presets-bar {
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
        }

        .presets-title {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 8px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .presets-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .preset-chip {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.78rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.15s;
        }

        .preset-chip:hover {
            background: var(--bg-card-hover);
            border-color: var(--accent-blue);
            color: #93c5fd;
        }

        /* Results & Diagnostics Styles */
        .diag-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1.2rem;
            display: none;
        }

        .diag-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .decision-badge {
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.85rem;
            letter-spacing: 0.05em;
        }

        .badge-pass {
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid var(--status-pass);
            color: #34d399;
        }

        .badge-hold {
            background: rgba(245, 158, 11, 0.2);
            border: 1px solid var(--status-hold);
            color: #fbbf24;
        }

        .badge-reject {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid var(--status-reject);
            color: #f87171;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 1rem;
        }

        .metric-box {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }

        .metric-val {
            font-family: var(--font-mono);
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--accent-cyan);
        }

        .metric-label {
            font-size: 0.72rem;
            color: var(--text-muted);
            margin-top: 4px;
            text-transform: uppercase;
        }

        /* Chat Interface Styles */
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        .chat-messages {
            flex: 1;
            padding: 1.4rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            max-height: 600px;
        }

        .chat-msg {
            display: flex;
            gap: 12px;
            max-width: 90%;
        }

        .msg-user {
            align-self: flex-end;
            flex-direction: row-reverse;
        }

        .msg-assistant {
            align-self: flex-start;
        }

        .msg-avatar {
            width: 34px;
            height: 34px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
            font-weight: 700;
            flex-shrink: 0;
        }

        .avatar-user {
            background: var(--accent-purple);
            color: #fff;
        }

        .avatar-assistant {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            color: #fff;
        }

        .msg-bubble {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 0.88rem;
            line-height: 1.6;
        }

        .msg-user .msg-bubble {
            background: #2563eb;
            border-color: #3b82f6;
            color: #fff;
        }

        .msg-bubble h3, .msg-bubble h4 {
            color: #93c5fd;
            margin: 8px 0 4px 0;
            font-size: 0.95rem;
        }

        .msg-bubble p {
            margin-bottom: 8px;
        }

        .msg-bubble p:last-child {
            margin-bottom: 0;
        }

        .msg-bubble table {
            width: 100%;
            border-collapse: collapse;
            margin: 8px 0;
            font-size: 0.8rem;
        }

        .msg-bubble th, .msg-bubble td {
            border: 1px solid var(--border-color);
            padding: 6px 10px;
            text-align: left;
        }

        .msg-bubble th {
            background: rgba(0, 0, 0, 0.2);
        }

        .msg-bubble code {
            font-family: var(--font-mono);
            background: rgba(0, 0, 0, 0.3);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.82em;
        }

        .msg-bubble ul {
            padding-left: 18px;
            margin: 6px 0;
        }

        .chat-input-bar {
            padding: 1rem 1.4rem;
            border-top: 1px solid var(--border-color);
            background: rgba(28, 38, 64, 0.5);
            display: flex;
            gap: 10px;
        }

        .chat-input {
            flex: 1;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 14px;
            color: var(--text-primary);
            font-family: var(--font-main);
            font-size: 0.9rem;
            outline: none;
        }

        .chat-input:focus {
            border-color: var(--accent-cyan);
        }

        .chat-send-btn {
            background: var(--accent-blue);
            color: #fff;
            border: none;
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s;
        }

        .chat-send-btn:hover {
            background: #2563eb;
        }

        /* Modal Styles */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
            visibility: hidden;
            opacity: 0;
            transition: all 0.2s;
        }

        .modal-overlay.active {
            visibility: visible;
            opacity: 1;
        }

        .modal-box {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            width: 90%;
            max-width: 520px;
            padding: 1.8rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }

        .modal-title {
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-close {
            background: none;
            border: none;
            color: var(--text-muted);
            font-size: 1.3rem;
            cursor: pointer;
        }

        .provider-select {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 1.2rem;
        }

        .provider-btn {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            padding: 10px;
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
            transition: all 0.15s;
        }

        .provider-btn.active {
            border-color: var(--accent-cyan);
            background: rgba(6, 182, 212, 0.15);
            color: #67e8f9;
        }
    </style>
</head>
<body>

    <header>
        <div class="logo-group">
            <div class="logo-icon">⚡</div>
            <div class="logo-text">
                <h1>SIH26170 Model Explainer & Discrepancy AI</h1>
                <p>NASA IGBT Aging & Semiconductor Stress Screening Assistant</p>
            </div>
        </div>
        <div class="header-actions">
            <div class="api-badge" id="apiBadgeBtn" onclick="openModal()">
                <span class="api-dot" id="apiDot"></span>
                <span id="apiStatusText">Engine: Gemini / Offline</span>
                <span>⚙️</span>
            </div>
        </div>
    </header>

    <main>
        <!-- LEFT PANEL: Model Discrepancy Analyzer & Presets -->
        <section class="panel">
            <div class="panel-header">
                <h2><span>🔍</span> Discrepancy & Physics Analyzer</h2>
            </div>
            <div class="panel-body">
                <form id="discrepancyForm" onsubmit="event.preventDefault(); runAnalysis();">
                    <div class="form-group">
                        <label for="modelSelect">Target Semiconductor Model</label>
                        <select id="modelSelect" onchange="updateModelFields()">
                            <option value="breakdown">Breakdown Model (Vce vs Ic)</option>
                            <option value="leakage">Leakage IV Model (V_applied vs I_leak)</option>
                            <option value="turnon">Turn-On Model (Vge vs Ic)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="componentId">Component ID / Serial</label>
                        <input type="text" id="componentId" class="form-control" value="DUT-NASA-IGBT-12">
                    </div>

                    <div class="form-group">
                        <label id="inputParamLabel" for="xInput">Collector-Emitter Voltage Vce (V)</label>
                        <input type="number" step="any" id="xInput" class="form-control" value="550.0" required>
                    </div>

                    <div class="input-row">
                        <div class="form-group">
                            <label for="yModel">Model Output (Y_model)</label>
                            <input type="number" step="any" id="yModel" class="form-control" value="3.87e-6" required>
                        </div>
                        <div class="form-group">
                            <label for="yUser">User Output (Y_user)</label>
                            <input type="number" step="any" id="yUser" class="form-control" value="1.25e-5" required>
                        </div>
                    </div>

                    <button type="submit" class="btn" id="analyzeBtn">
                        <span>⚡</span> Explain Discrepancy & Physics
                    </button>
                </form>

                <!-- Live Diagnostic Card -->
                <div class="diag-card" id="diagCard">
                    <div class="diag-header">
                        <span style="font-size:0.85rem; font-weight:600; color:var(--text-secondary);">SCREENING STATUS</span>
                        <span id="decisionBadge" class="decision-badge badge-reject">REJECT</span>
                    </div>
                    <div class="metric-grid">
                        <div class="metric-box">
                            <div class="metric-val" id="metricDelta">8.63e-06</div>
                            <div class="metric-label">Absolute Delta (Δ)</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-val" id="metricPct">+223.0%</div>
                            <div class="metric-label">% Deviation</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-val" id="metricRatio">3.23x</div>
                            <div class="metric-label">Magnitude Ratio</div>
                        </div>
                    </div>
                </div>

                <!-- Presets -->
                <div class="presets-bar">
                    <div class="presets-title">NASA IGBT Aging Test Cases</div>
                    <div class="presets-list">
                        <div class="preset-chip" onclick="loadPreset('breakdown', 550.0, 3.87e-6, 1.25e-5, 'NASA-Part-12 (Aged 500h)')">
                            <span>⚡ [Breakdown] Premature Knee (550V)</span>
                            <span style="color:var(--status-reject); font-weight:700;">REJECT</span>
                        </div>
                        <div class="preset-chip" onclick="loadPreset('leakage', 25.0, 1.05e-5, 4.50e-5, 'NASA-Part-18 (Thermal Stress)')">
                            <span>🔍 [Leakage] High SRH Leakage (25V)</span>
                            <span style="color:var(--status-hold); font-weight:700;">HOLD</span>
                        </div>
                        <div class="preset-chip" onclick="loadPreset('turnon', 5.0, 1.85, 0.42, 'NASA-Part-14 (Oxide Trap)')">
                            <span>🔄 [Turn-On] +ΔVth Shift (Vge=5V)</span>
                            <span style="color:var(--status-reject); font-weight:700;">REJECT</span>
                        </div>
                        <div class="preset-chip" onclick="loadPreset('leakage', 10.0, 3.85e-9, 4.02e-9, 'NASA-Part-11 (Pristine)')">
                            <span>🟢 [Baseline] Healthy Population (10V)</span>
                            <span style="color:var(--status-pass); font-weight:700;">PASS</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- RIGHT PANEL: Conversational AI Chat & Diagnostic Report View -->
        <section class="panel">
            <div class="panel-header">
                <h2><span>🤖</span> Semiconductor Model Dynamics & Output Explainer</h2>
                <button class="btn-secondary" onclick="clearChat()">Clear Chat</button>
            </div>
            <div class="chat-container">
                <div class="chat-messages" id="chatMessages">
                    <div class="chat-msg msg-assistant">
                        <div class="msg-avatar avatar-assistant">AI</div>
                        <div class="msg-bubble">
                            <h3>👋 Welcome to SemiconExplainer AI</h3>
                            <p>I am your dedicated AI diagnostic assistant for <strong>Project SIH26170</strong> (Semiconductor Environmental Stress Screening).</p>
                            <p>You can:</p>
                            <ul>
                                <li>Use the <strong>Discrepancy Analyzer</strong> on the left to compare ML model predictions ($Y_{model}$) with observed ground truth ($Y_{user}$).</li>
                                <li>Ask questions about <strong>Breakdown</strong>, <strong>Leakage IV</strong>, and <strong>Turn-On</strong> physical dynamics.</li>
                                <li>Get instant <strong>PASS / HOLD / REJECT</strong> screening decisions with physics-grounded explanations.</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="chat-input-bar">
                    <input type="text" id="chatInput" class="chat-input" placeholder="Ask about model dynamics, failure physics, or paste values..." onkeydown="if(event.key==='Enter') sendMessage();">
                    <button class="chat-send-btn" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </section>
    </main>

    <!-- Modal for Free API Configuration -->
    <div class="modal-overlay" id="apiModal">
        <div class="modal-box">
            <div class="modal-title">
                <span>⚙️ Configure Free AI API Provider</span>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:1rem;">
                Select a free AI API tier or use the built-in zero-dependency offline physics diagnostic engine:
            </p>
            <div class="provider-select">
                <button type="button" class="provider-btn active" id="btnProviderGemini" onclick="selectProvider('gemini')">Google Gemini (Free)</button>
                <button type="button" class="provider-btn" id="btnProviderGroq" onclick="selectProvider('groq')">Groq Free (Llama 3.3)</button>
                <button type="button" class="provider-btn" id="btnProviderOpenrouter" onclick="selectProvider('openrouter')">OpenRouter (Free)</button>
                <button type="button" class="provider-btn" id="btnProviderOffline" onclick="selectProvider('offline')">Offline Physics Engine</button>
            </div>
            <div class="form-group" id="apiKeyGroup">
                <label for="modalApiKey">API Key</label>
                <input type="password" id="modalApiKey" class="form-control" placeholder="Enter API Key (e.g. AIzaSy...)">
                <small style="font-size:0.75rem; color:var(--text-muted); display:block; margin-top:4px;">
                    Get free Gemini API keys at <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:var(--accent-cyan);">Google AI Studio</a>.
                </small>
            </div>
            <button type="button" class="btn" onclick="saveApiConfig()">Save Configuration</button>
        </div>
    </div>

    <script>
        let currentProvider = "gemini";

        const MODEL_META = {
            breakdown: {
                label: "Collector-Emitter Voltage Vce (V)",
                defaultX: 550.0,
                defaultYm: 3.87e-6,
                defaultYu: 1.25e-5
            },
            leakage: {
                label: "Applied Bias Voltage (V)",
                defaultX: 25.0,
                defaultYm: 1.05e-5,
                defaultYu: 4.50e-5
            },
            turnon: {
                label: "Gate-Emitter Voltage Vge (V)",
                defaultX: 5.0,
                defaultYm: 1.85,
                defaultYu: 0.42
            }
        };

        function updateModelFields() {
            const m = document.getElementById('modelSelect').value;
            document.getElementById('inputParamLabel').textContent = MODEL_META[m].label;
            document.getElementById('xInput').value = MODEL_META[m].defaultX;
            document.getElementById('yModel').value = MODEL_META[m].defaultYm;
            document.getElementById('yUser').value = MODEL_META[m].defaultYu;
        }

        function loadPreset(model, x, ym, yu, cid) {
            document.getElementById('modelSelect').value = model;
            document.getElementById('inputParamLabel').textContent = MODEL_META[model].label;
            document.getElementById('xInput').value = x;
            document.getElementById('yModel').value = ym;
            document.getElementById('yUser').value = yu;
            document.getElementById('componentId').value = cid;
            runAnalysis();
        }

        async function runAnalysis() {
            const model = document.getElementById('modelSelect').value;
            const cid = document.getElementById('componentId').value;
            const x = parseFloat(document.getElementById('xInput').value);
            const ym = parseFloat(document.getElementById('yModel').value);
            const yu = parseFloat(document.getElementById('yUser').value);

            const btn = document.getElementById('analyzeBtn');
            btn.innerHTML = "<span>⏳</span> Analyzing Physics...";
            btn.disabled = true;

            try {
                const response = await fetch('/api/explain', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        model_type: model,
                        x_input: x,
                        y_model: ym,
                        y_user: yu,
                        component_id: cid
                    })
                });
                const data = await response.json();

                // Update metric card
                const diagCard = document.getElementById('diagCard');
                diagCard.style.display = 'block';

                const badge = document.getElementById('decisionBadge');
                badge.textContent = data.risk_decision;
                badge.className = 'decision-badge ' + (data.risk_decision === 'PASS' ? 'badge-pass' : (data.risk_decision === 'HOLD' ? 'badge-hold' : 'badge-reject'));

                document.getElementById('metricDelta').textContent = formatSci(data.delta);
                document.getElementById('metricPct').textContent = (data.pct_diff > 0 ? '+' : '') + data.pct_diff.toFixed(2) + '%';
                document.getElementById('metricRatio').textContent = data.ratio.toFixed(2) + 'x';

                // Append explanation to chat
                appendAssistantMessage(data.final_explanation);

            } catch (err) {
                alert('Analysis error: ' + err.message);
            } finally {
                btn.innerHTML = "<span>⚡</span> Explain Discrepancy & Physics";
                btn.disabled = false;
            }
        }

        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const msg = input.value.trim();
            if (!msg) return;

            appendUserMessage(msg);
            input.value = '';

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const data = await response.json();
                appendAssistantMessage(data.reply);
            } catch (err) {
                appendAssistantMessage('❌ Error generating reply: ' + err.message);
            }
        }

        function appendUserMessage(text) {
            const chat = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.className = 'chat-msg msg-user';
            div.innerHTML = `
                <div class="msg-avatar avatar-user">U</div>
                <div class="msg-bubble">${escapeHtml(text)}</div>
            `;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        function appendAssistantMessage(markdown) {
            const chat = document.getElementById('chatMessages');
            const div = document.createElement('div');
            div.className = 'chat-msg msg-assistant';
            div.innerHTML = `
                <div class="msg-avatar avatar-assistant">AI</div>
                <div class="msg-bubble">${renderMarkdown(markdown)}</div>
            `;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        function clearChat() {
            document.getElementById('chatMessages').innerHTML = '';
        }

        function formatSci(val) {
            if (val === 0) return "0.00";
            if (Math.abs(val) < 1e-3 || Math.abs(val) >= 1e5) return val.toExponential(3);
            return val.toFixed(4);
        }

        function escapeHtml(str) {
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        function renderMarkdown(md) {
            if (!md) return '';
            let html = md
                .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
                .replace(/\\*\\*(.*?)\\*\\*/gim, '<strong>$1</strong>')
                .replace(/\\*(.*?)\\*/gim, '<em>$1</em>')
                .replace(/`([^`]+)`/gim, '<code>$1</code>')
                .replace(/\\n/gim, '<br>');
            return html;
        }

        function openModal() {
            document.getElementById('apiModal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('apiModal').classList.remove('active');
        }

        function selectProvider(p) {
            currentProvider = p;
            ['Gemini', 'Groq', 'Openrouter', 'Offline'].forEach(name => {
                const el = document.getElementById('btnProvider' + name);
                if (el) el.classList.remove('active');
            });
            const selectedBtn = document.getElementById('btnProvider' + p.charAt(0).toUpperCase() + p.slice(1));
            if (selectedBtn) selectedBtn.classList.add('active');

            const keyGroup = document.getElementById('apiKeyGroup');
            keyGroup.style.display = (p === 'offline') ? 'none' : 'block';
        }

        async function saveApiConfig() {
            const key = document.getElementById('modalApiKey').value.trim();
            try {
                await fetch('/api/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({provider: currentProvider, api_key: key})
                });
                document.getElementById('apiStatusText').textContent = 'Engine: ' + currentProvider.toUpperCase();
                closeModal();
            } catch (err) {
                alert('Failed to save config: ' + err.message);
            }
        }
    </script>
</body>
</html>
"""


class WebAppHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for the Chatbot Web UI & API Endpoints."""

    def _set_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(HTML_PAGE.encode("utf-8"))

        elif path == "/api/models":
            self._set_headers(200)
            self.wfile.write(json.dumps(MODEL_DEFINITIONS).encode("utf-8"))

        elif path == "/api/status":
            self._set_headers(200)
            status = {
                "status": "online",
                "active_provider": chatbot_instance.api_client.provider,
                "has_api_key": bool(chatbot_instance.api_client.api_key)
            }
            self.wfile.write(json.dumps(status).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode("utf-8"))
            return

        if path == "/api/explain":
            model_type = data.get("model_type", "breakdown")
            x_input = float(data.get("x_input", 0.0))
            y_model = float(data.get("y_model", 0.0))
            y_user = float(data.get("y_user", 0.0))
            cid = data.get("component_id", "DUT-01")
            use_ai = data.get("use_ai", True)

            try:
                diag = chatbot_instance.explain_discrepancy(
                    model_type=model_type,
                    x_input=x_input,
                    y_model=y_model,
                    y_user=y_user,
                    component_id=cid,
                    use_ai=use_ai
                )
                self._set_headers(200)
                self.wfile.write(json.dumps(diag).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/chat":
            msg = data.get("message", "")
            try:
                reply = chatbot_instance.chat(msg)
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "reply": reply,
                    "provider": chatbot_instance.api_client.provider
                }).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif path == "/api/config":
            provider = data.get("provider", "offline")
            key = data.get("api_key", None)
            chatbot_instance.set_api_key(provider, key)
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "status": "updated",
                "provider": provider,
                "has_key": bool(key)
            }).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Semiconductor Model Explainer Web App")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    args = parser.parse_args()

    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, WebAppHandler)
    print("=" * 70)
    print(f"🚀 SIH26170 Semiconductor Model Explainer & Chatbot Web App")
    print(f"🌐 Server running at http://{args.host}:{args.port}/")
    print(f"⚡ Active AI Engine: {chatbot_instance.api_client.provider.upper()}")
    print("=" * 70)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
        httpd.server_close()


if __name__ == "__main__":
    main()
