#!/usr/bin/env python3
"""
SIH26170 - Specification Sheet DOCX Generator
=============================================================================
Generates a complete, beautifully structured Microsoft Word (.docx) specification
sheet for Project SIH26170 - Team Drishti (Insightful Vision).
"""

import zipfile
import html
from pathlib import Path

def generate_docx():
    target_file = Path("/Users/samarth/Documents/SIH 26/Drishti_System_Specification_Sheet.docx")
    
    # 1. Content Types XML
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    # 2. Package Relationships XML
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    # 3. Document Relationships XML
    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    # 4. Styles XML
    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
        <w:sz w:val="22"/>
        <w:color w:val="1F2937"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:after="140" w:line="276" w:lineRule="auto"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
  
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:rPr>
      <w:rFonts w:ascii="Calibri Light" w:hAnsi="Calibri Light"/>
      <w:b/>
      <w:sz w:val="34"/>
      <w:color w:val="1E40AF"/>
    </w:rPr>
    <w:pPr>
      <w:spacing w:before="300" w:after="120"/>
    </w:pPr>
  </w:style>
  
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/>
      <w:sz w:val="28"/>
      <w:color w:val="EA580C"/>
    </w:rPr>
    <w:pPr>
      <w:spacing w:before="240" w:after="100"/>
    </w:pPr>
  </w:style>
  
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/>
    <w:rPr>
      <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
      <w:b/>
      <w:sz w:val="24"/>
      <w:color w:val="0F2B5C"/>
    </w:rPr>
    <w:pPr>
      <w:spacing w:before="180" w:after="80"/>
    </w:pPr>
  </w:style>
</w:styles>"""

    # 5. Core Document Content Helper Functions
    def escape_xml(text):
        return html.escape(str(text))

    def make_p(text="", style=None, bold=False, italic=False, color="1F2937", size=22, space_before=0, space_after=140, align="left"):
        p_align = f'<w:jc w:val="{align}"/>' if align != "left" else ""
        p_style = f'<w:pStyle w:val="{style}"/>' if style else ""
        p_spacing = f'<w:spacing w:before="{space_before}" w:after="{space_after}" w:line="276" w:lineRule="auto"/>'
        
        r_bold = "<w:b/>" if bold else ""
        r_italic = "<w:i/>" if italic else ""
        r_color = f'<w:color w:val="{color}"/>' if color else ""
        r_size = f'<w:sz w:val="{size}"/>' if size else ""
        
        xml = f"""<w:p>
  <w:pPr>{p_style}{p_align}{p_spacing}</w:pPr>
  <w:r>
    <w:rPr>{r_bold}{r_italic}{r_color}{r_size}</w:rPr>
    <w:t xml:space="preserve">{escape_xml(text)}</w:t>
  </w:r>
</w:p>"""
        return xml

    def make_bullet(bold_prefix, text):
        return f"""<w:p>
  <w:pPr>
    <w:pStyle w:val="ListParagraph"/>
    <w:spacing w:before="40" w:after="80" w:line="276" w:lineRule="auto"/>
    <w:ind w:left="360" w:hanging="180"/>
  </w:pPr>
  <w:r>
    <w:rPr><w:b/><w:color w:val="1E40AF"/></w:rPr>
    <w:t>• </w:t>
  </w:r>
  <w:r>
    <w:rPr><w:b/><w:color w:val="0F2B5C"/></w:rPr>
    <w:t xml:space="preserve">{escape_xml(bold_prefix)}: </w:t>
  </w:r>
  <w:r>
    <w:rPr><w:color w:val="334155"/></w:rPr>
    <w:t xml:space="preserve">{escape_xml(text)}</w:t>
  </w:r>
</w:p>"""

    def make_callout(title, body_text):
        return f"""<w:p>
  <w:pPr>
    <w:spacing w:before="120" w:after="120"/>
    <w:pBdr>
      <w:left w:val="single" w:sz="24" w:space="12" w:color="EA580C"/>
    </w:pBdr>
    <w:shd w:val="clear" w:color="auto" w:fill="FFF7ED"/>
  </w:pPr>
  <w:r>
    <w:rPr><w:b/><w:color w:val="EA580C"/><w:sz w:val="22"/></w:rPr>
    <w:t xml:space="preserve">{escape_xml(title)}&#10;</w:t>
  </w:r>
  <w:r>
    <w:rPr><w:color w:val="7C2D12"/><w:sz w:val="21"/></w:rPr>
    <w:t xml:space="preserve">{escape_xml(body_text)}</w:t>
  </w:r>
</w:p>"""

    def make_table(headers, rows, col_widths=None):
        num_cols = len(headers)
        if not col_widths:
            col_widths = [int(9000 / num_cols)] * num_cols
            
        xml = ['<w:tbl><w:tblPr><w:tblW w:w="9000" w:type="dxa"/><w:tblBorders><w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/><w:left w:val="none"/><w:bottom w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/><w:right w:val="none"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/><w:insideV w:val="none"/></w:tblBorders></w:tblPr>']
        
        # Header row
        xml.append('<w:tr><w:trPr><w:tblHeader/></w:trPr>')
        for idx, h in enumerate(headers):
            w = col_widths[idx]
            xml.append(f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="EFF6FF"/></w:tcPr><w:p><w:pPr><w:spacing w:before="80" w:after="80"/></w:pPr><w:r><w:rPr><w:b/><w:color w:val="1E40AF"/><w:sz w:val="20"/></w:rPr><w:t>{escape_xml(h)}</w:t></w:r></w:p></w:tc>')
        xml.append('</w:tr>')
        
        # Body rows
        for row in rows:
            xml.append('<w:tr>')
            for idx, cell in enumerate(row):
                w = col_widths[idx]
                xml.append(f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/></w:tcPr><w:p><w:pPr><w:spacing w:before="60" w:after="60"/></w:pPr><w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{escape_xml(cell)}</w:t></w:r></w:p></w:tc>')
            xml.append('</w:tr>')
            
        xml.append('</w:tbl>')
        xml.append('<w:p><w:pPr><w:spacing w:after="140"/></w:pPr></w:p>')
        return "".join(xml)

    # 6. Build Document Body
    doc_body = []
    
    # Document Header / Cover Style
    doc_body.append(make_p("ENGINEERING SPECIFICATION SHEET", bold=True, color="EA580C", size=24, space_before=100, space_after=60))
    doc_body.append(make_p("Drishti — AI-Driven Semiconductor Burn-In & Anomaly Screening System", bold=True, color="1E40AF", size=36, space_before=40, space_after=100))
    doc_body.append(make_p("Smart India Hackathon (SIH 2026) • Problem Statement ID: SIH26170", bold=True, color="046A38", size=22, space_before=0, space_after=80))
    doc_body.append(make_p("Organization: Symbiosis Institute of Technology (SIT), Pune | Team: Drishti (Insightful Vision)", italic=True, color="64748B", size=20, space_before=0, space_after=240))
    
    doc_body.append(make_callout(
        "MISSION OBJECTIVE",
        "Develop an end-to-end AI/ML predictive environmental stress screening (ESS) system that detects subtle, population-relative latent defects in semiconductor components (IGBTs/MOSFETs) during 125°C Burn-In testing across 0h, 24h, 96h, and 168h before catastrophic mission failure."
    ))

    # SECTION 1: EXECUTIVE SUMMARY & PROBLEM FORMULATION
    doc_body.append(make_p("1. Executive Summary & Problem Formulation", style="Heading1"))
    doc_body.append(make_p(
        "In high-reliability sectors such as space and aerospace, electronic components undergo rigorous Environmental Stress Screening (ESS), including Burn-In testing at elevated temperatures (e.g., 125°C for extended durations). Traditional manufacturing quality assurance relies strictly on static parametric pass/fail limits defined in component datasheets. However, 'latent defects'—components that pass the absolute limits but exhibit anomalous drift over time—often escape into final space payloads, resulting in catastrophic field failures."
    ))
    doc_body.append(make_bullet(
        "The Latent Defect Dilemma",
        "Consider a semiconductor lot with a mean leakage current of 10 μA and a static datasheet upper limit of 50 μA. A component exhibiting 45 μA technically passes traditional screening, yet represents a 4.5x population deviation indicating localized barrier degradation or dielectric micro-cracking."
    ))
    doc_body.append(make_bullet(
        "Drishti Core Purpose",
        "Provides dynamic population-relative outlier detection, time-series drift forecasting, feature auto-scaling, and natural language physics explainability powered by Groq Llama 3.3."
    ))

    # SECTION 2: SYSTEM ARCHITECTURE & TOPOLOGY
    doc_body.append(make_p("2. Fullstack System Architecture & Technology Stack", style="Heading1"))
    doc_body.append(make_p(
        "The system is engineered as a unified, zero-dependency fullstack application adhering to strict enterprise and laboratory deployment requirements. All networking, ML math, database transactions, and AI communications run natively on standard Python 3.8+ libraries."
    ))
    
    arch_headers = ["Layer", "Technology / Framework", "Primary Engineering Responsibility"]
    arch_rows = [
        ["Frontend UI", "HTML5, CSS3 Modern Flex/Grid, Vanilla JS, Chart.js 4.4.1", "SPA Navigation, Draggable Scatterplots, Line Curves, Real-time Sliders, Indian Flag Accents"],
        ["REST Server", "Python 3 Standard Library (http.server, socketserver)", "Zero-dependency HTTP server serving static assets and JSON REST endpoints on port 5000"],
        ["Auto-Scaler", "Custom Z-Score Standardization (scaler.py)", "Normalizes raw physical voltages (X_raw -> X_scaled) and inverse-scales predictions (Y_scaled -> Y_phys)"],
        ["ML Engine", "Physics-Informed Linear & Polynomial Models (model_engine.py)", "Executes scaled parameter inference based on NASA accelerated aging regression curves"],
        ["Explainability", "Groq Llama 3.3 (70B Versatile) + Built-in Rule Engine", "Translates mathematical deviations into 3-point concise physics failure reports & verdicts"],
        ["Database", "SQLite3 (backend/data/screening.db)", "Persists all screening transactions, deviations, AI reports, and timestamps for QA auditing"]
    ]
    doc_body.append(make_table(arch_headers, arch_rows, [1800, 2800, 4400]))

    # SECTION 3: FRONTEND SPECIFICATION & INTERACTIVE CANVAS
    doc_body.append(make_p("3. Frontend Architecture & Human Interface (UX/UI)", style="Heading1"))
    doc_body.append(make_p(
        "The human interface is designed around clean white ergonomics with Indian Flag inspired accent colors (Saffron Orange #EA580C, Chakra Navy Blue #1E40AF, and India Green #15803D), minimal functional typography, and interactive canvas graphics."
    ))
    
    doc_body.append(make_p("3.1 Core User Interface Views", style="Heading2"))
    doc_body.append(make_bullet(
        "Landing Page (4 Executive Cards)",
        "Features 4 dedicated cards: 1) About Us (Team Drishti & SIH26170 specifications), 2) Breakdown Model (Vce vs Ic), 3) Leakage IV Model (Applied Voltage vs Leakage), and 4) Turn-On Model (Vge vs Ic)."
    ))
    doc_body.append(make_bullet(
        "Split-Screen Diagnostic Workspace",
        "Left Column: Model controls, raw voltage inputs, live logarithmic/linear sliders, NASA presets, and real-time AI Chatbot. Right Column: Dedicated data visualizations strictly positioned on the right side."
    ))
    doc_body.append(make_bullet(
        "Right-Aligned Compliance Footer",
        "Features a clean, subtle footer styled with font-size strictly < 11px (10px): 'This website is vibecoded with assistance from - Google Antigravity'."
    ))

    doc_body.append(make_p("3.2 Interactive Graph Movement & Manipulation", style="Heading2"))
    doc_body.append(make_p(
        "The graphs are fully interactive and adaptable to personal engineering needs:"
    ))
    doc_body.append(make_bullet(
        " Direct Canvas Dragging",
        "Clicking or dragging anywhere across the Scatterplot or Line Chart immediately repositions the live test point to that exact (X, Y) coordinate, simultaneously updating the form inputs and triggering real-time re-screening."
    ))
    doc_body.append(make_bullet(
        " Pan View Mode",
        "Activating Pan Mode allows engineers to click and drag the canvas axes in 2D space to explore specific sub-breakdown knees, saturation regions, or high-voltage leakage tails."
    ))
    doc_body.append(make_bullet(
        " Zoom In / Out & Mouse Wheel",
        "Engineers can zoom with toolbar buttons or use the mouse scroll wheel centered at the cursor. A 'Reset View' button instantly restores default axis boundaries."
    ))
    doc_body.append(make_bullet(
        " Real-Time Sliders",
        "Smooth input voltage and current sliders allow dynamic parameter sweeping with debounced ML model evaluation."
    ))

    # SECTION 4: BACKEND & SCALING ENGINE
    doc_body.append(make_p("4. Backend Engineering & Auto-Scaling Pipeline", style="Heading1"))
    doc_body.append(make_p(
        "A critical engineering requirement is dealing with raw, unscaled user input (e.g. 550.0 V, 1.25e-5 A) and mapping it into the scaled feature space required by machine learning models."
    ))
    
    doc_body.append(make_p("4.1 Mathematical Formulation", style="Heading2"))
    doc_body.append(make_p(
        "1. Feature Standardization: X_scaled = (X_raw - μ_x) / σ_x\n"
        "2. Scaled Forward Inference: Y_scaled = w · X_scaled + b\n"
        "3. Target Inverse Transformation: Y_phys = Y_scaled · σ_y + μ_y\n"
        "4. Quantitative Deviation: Δ% = ((Y_user - Y_model) / Y_model) · 100\n"
        "5. Magnitude Ratio: Ratio = Y_user / Y_model"
    ))
    
    doc_body.append(make_p("4.2 NASA Dataset Calibration Statistics", style="Heading2"))
    cal_headers = ["Model Name", "Input Feature", "Min X", "Max X", "Target Feature", "Min Y (microAmpere)", "Max Y (microAmpere)"]
    cal_rows = [
        ["Breakdown", "Collector-Emitter Voltage (V)", "0.0 V", "650.0 V", "Leakage Current", "0.0 microAmpere", "150.0 microAmpere"],
        ["Leakage IV", "Applied Voltage (V)", "0.0 V", "600.0 V", "Leakage Current", "0.0 microAmpere", "10.0 microAmpere"],
        ["Turn-On", "Gate Voltage (V)", "0.0 V", "15.0 V", "Collector Current", "0.0 microAmpere", "250.0 microAmpere"]
    ]
    doc_body.append(make_table(cal_headers, cal_rows, [1200, 1500, 1100, 1100, 1400, 1300, 1400]))

    doc_body.append(make_p("4.3 IGBT Time-Series Degradation & Breakdown Prediction Pipeline", style="Heading2"))
    doc_body.append(make_p(
        "For mission-critical space converters, the system implements an end-to-end time-series degradation pipeline operating on chronological sensor streams (Breakdown_timeseries_microampere.csv • 3,790 observations • 30-minute intervals):\n"
        "1. Leakage-Safe Feature Engineering: Lags [1, 2, 3, 6, 12], Shifted Rolling Statistics [3, 6, 12, 24] with mean and std (shifted by 1 observation before window calculation to strictly prevent lookahead leakage).\n"
        "2. Chronological Split: 80% past historical training / 20% future unseen testing (shuffle=False).\n"
        "3. Gradient Boosting Regression: GradientBoostingRegressor(n_estimators=300, learning_rate=0.03, max_depth=3) evaluated via 5-Fold TimeSeriesSplit.\n"
        "4. Predictive Maintenance Anomaly Signals: Tracks prediction residual e_t = Actual - Predicted in microAmperes with dynamic confidence bounds (+/-2σ, +/-4σ) to flag early degradation warnings before catastrophic avalanche breakdown."
    ))

    # SECTION 5: REST API SPECIFICATION
    doc_body.append(make_p("5. REST API Specifications & Integration Protocols", style="Heading1"))
    doc_body.append(make_p(
        "The backend exposes a clean REST API running on http://localhost:5000:"
    ))
    
    api_headers = ["Endpoint", "Method", "Request Payload", "Response Summary"]
    api_rows = [
        ["/api/health", "GET", "None", "Health status, active AI engine, and database connection status"],
        ["/api/models", "GET", "None", "Metadata, parameters, units, and typical ranges for all 3 models"],
        ["/api/dataset-sample", "GET", "model (str), limit (int)", "Sampled (X, Y) dataset points from NASA CSV files for scatterplot rendering"],
        ["/api/pipeline/run", "POST", "{model_type, raw_input, user_said_output, component_id}", "Auto-scales input, runs inference, inverse-scales output, analyzes discrepancy, generates Groq explanation, logs to DB"],
        ["/api/chat", "POST", "{message: string}", "Answers questions regarding IGBT physics, failure modes, and screening criteria using Groq Llama 3.3"],
        ["/api/screenings", "GET", "limit (int), model (str)", "Retrieves historical screening audit logs from SQLite database"]
    ]
    doc_body.append(make_table(api_headers, api_rows, [1800, 900, 2700, 3600]))

    # SECTION 6: SEMICONDUCTOR FAILURE PHYSICS & EXPLAINABILITY
    doc_body.append(make_p("6. Semiconductor Failure Physics & AI Explainability", style="Heading1"))
    doc_body.append(make_p(
        "The explainability system bridges raw ML predictions with physical device dynamics. Groq Llama 3.3 produces concise 3-point structured reports strictly under 100 words:"
    ))
    
    doc_body.append(make_bullet(
        "1. Quantitative Deviation",
        "Reports the exact percentage drift (Δ%) and magnitude scaling ratio (e.g. +223.0% drift, 3.23x baseline)."
    ))
    doc_body.append(make_bullet(
        "2. Semiconductor Failure Physics",
        "Identifies root causes such as: Premature Avalanche Breakdown & impact ionization in high electric fields; Shockley-Read-Hall (SRH) generation-recombination in the space-charge region; Gate oxide electron trapping causing positive threshold voltage shift (+ΔVth); Die-attach solder fatigue and thermal runaway."
    ))
    doc_body.append(make_bullet(
        "3. SIH-26 Actionable Verdict",
        "Assigns  PASS (normal baseline, |Δ%| <= 10%),  HOLD (moderate drift, requires 125°C curve tracing), or  REJECT (high latent defect risk, immediate flight payload quarantine)."
    ))

    # SECTION 7: QUALITY ASSURANCE & EVALUATION METRICS
    doc_body.append(make_p("7. Quality Assurance & Evaluation Metrics", style="Heading1"))
    doc_body.append(make_bullet(
        "Anomaly Detection Score",
        "Zero-tolerance policy for False Negatives. In aerospace screening, letting a defective component escape into space payloads is catastrophic."
    ))
    doc_body.append(make_bullet(
        "Drift Prediction Accuracy",
        "Minimizes Mean Absolute Error (MAE) between predicted Value_168h and hidden ground-truth laboratory values."
    ))
    doc_body.append(make_bullet(
        "High-Availability Fallback Guarantee",
        "If Groq API experiences rate limits or network disconnects, the system instantly switches to its built-in rule-based physics engine, ensuring 100% uptime without user-facing errors."
    ))

    # SECTION 8: TEAM DHRISHTI ROSTER
    doc_body.append(make_p("8. Team Drishti Roster & Institutional Stamp", style="Heading1"))
    doc_body.append(make_p(
        "Project developed for Smart India Hackathon (SIH 2026) by Team Drishti at Symbiosis Institute of Technology (SIT), Pune:"
    ))
    
    team_headers = ["#", "Member Name", "PRN / Student ID", "Engineering Role / Specialization"]
    team_rows = [
        ["1", "Samarth Buchake", "25070126151", "Machine Learning & Fullstack Architecture Lead"],
        ["2", "Vibhuti Patil", "25070126193", "Physics of Failure & Semiconductor Model Specialist"],
        ["3", "Maitreyee Kulkarni", "24070123058", "Data Preprocessing & Statistical Calibration Engineer"],
        ["4", "Varija Korti", "24070123165", "Time-Series Regression & Drift Prediction Specialist"],
        ["5", "Kaushal Sidhpura", "25070127093", "Dynamic Outlier Detection & Anomaly Scoring Lead"],
        ["6", "Prachi Hirve", "26070126090", "Explainability Engine & QA Diagnostics Engineer"]
    ]
    doc_body.append(make_table(team_headers, team_rows, [500, 2500, 1800, 4200]))

    # Footer note
    doc_body.append(make_p(
        "Document compiled and verified for SIH26170. All rights reserved by Team Drishti (SIT Pune).",
        italic=True, color="64748B", size=18, space_before=180, space_after=60, align="center"
    ))

    # Assemble document.xml
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {"".join(doc_body)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    # 7. Write ZIP archive (.docx)
    with zipfile.ZipFile(target_file, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/_rels/document.xml.rels", doc_rels)
        zf.writestr("word/styles.xml", styles_xml)
        zf.writestr("word/document.xml", document_xml)

    print(f"Specification Sheet successfully generated at: {target_file}")
    print(f"File size: {target_file.stat().st_size} bytes")

if __name__ == "__main__":
    generate_docx()
