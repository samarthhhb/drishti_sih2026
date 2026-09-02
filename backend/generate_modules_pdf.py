#!/usr/bin/env python3
"""
SIH26170 - Module A & Module B PDF Generator (Pure Python Standard Library)
Generates publication-quality, styled PDF documents with proper mathematical formulas,
physics equations, tables, callout boxes, headers, footers, and page numbers.
"""

import os
import math
from pathlib import Path

class PDFBuilder:
    def __init__(self, filename, doc_title="", doc_subtitle="", team_header="Team Drishti • SIH26170"):
        self.filename = filename
        self.doc_title = doc_title
        self.doc_subtitle = doc_subtitle
        self.team_header = team_header
        self.width = 595.28  # A4 width in pt
        self.height = 841.89 # A4 height in pt
        self.margin_left = 46.0
        self.margin_right = 46.0
        self.margin_top = 50.0
        self.margin_bottom = 50.0
        self.content_w = self.width - self.margin_left - self.margin_right
        self.pages = []
        self.current_stream = []
        self.cursor_y = self.height - self.margin_top
        self.page_num = 1

    def new_page(self):
        if self.current_stream:
            self._draw_header_footer()
            self.pages.append("".join(self.current_stream))
            self.current_stream = []
            self.page_num += 1
        self.cursor_y = self.height - self.margin_top

    def _draw_header_footer(self):
        s = []
        # Running Top Header
        s.append("0.5 w 0.059 0.169 0.361 RG ") # Chakra Navy
        s.append(f"{self.margin_left} {self.height - 32} m {self.width - self.margin_right} {self.height - 32} l S ")
        s.append("BT /F2 8 Tf 0.28 0.33 0.41 rg ")
        s.append(f"{self.margin_left} {self.height - 28} Td ({self.team_header}) Tj ET ")
        s.append("BT /F1 8 Tf 0.28 0.33 0.41 rg ")
        # Right aligned title
        title_disp = self.doc_title[:45] + "..." if len(self.doc_title) > 45 else self.doc_title
        s.append(f"{self.width - self.margin_right - 180} {self.height - 28} Td ({title_disp}) Tj ET ")

        # Running Bottom Footer
        s.append("0.5 w 0.8 0.84 0.88 RG ")
        s.append(f"{self.margin_left} 34 m {self.width - self.margin_right} 34 l S ")
        s.append("BT /F1 8 Tf 0.4 0.45 0.5 rg ")
        s.append(f"{self.margin_left} 22 Td (Smart India Hackathon 2024 • Symbiosis Institute of Technology, Pune) Tj ET ")
        s.append(f"BT /F2 8 Tf 0.059 0.169 0.361 rg {self.width - self.margin_right - 55} 22 Td (Page {self.page_num}) Tj ET ")
        self.current_stream.insert(0, "".join(s))

    def ensure_space(self, pts):
        if self.cursor_y - pts < self.margin_bottom:
            self.new_page()

    def add_title_banner(self, category, title, subtitle):
        self.ensure_space(100)
        s = []
        # Top banner background
        s.append("0.94 0.96 0.98 rg ") # soft light slate
        s.append(f"{self.margin_left} {self.cursor_y - 75} {self.content_w} 85 re f ")
        # Left accent stripe (Saffron Orange)
        s.append("0.918 0.345 0.047 rg ")
        s.append(f"{self.margin_left} {self.cursor_y - 75} 5 85 re f ")
        # Navy top border
        s.append("0.059 0.169 0.361 RG 1.5 w ")
        s.append(f"{self.margin_left} {self.cursor_y + 10} m {self.width - self.margin_right} {self.cursor_y + 10} l S ")

        # Category
        s.append(f"BT /F2 9 Tf 0.918 0.345 0.047 rg {self.margin_left + 14} {self.cursor_y - 8} Td ({self._clean(category.upper())}) Tj ET ")
        # Main Title
        s.append(f"BT /F2 16 Tf 0.059 0.169 0.361 rg {self.margin_left + 14} {self.cursor_y - 28} Td ({self._clean(title)}) Tj ET ")
        # Subtitle
        s.append(f"BT /F3 9.5 Tf 0.28 0.33 0.41 rg {self.margin_left + 14} {self.cursor_y - 45} Td ({self._clean(subtitle)}) Tj ET ")
        # Author Line
        s.append(f"BT /F1 8.5 Tf 0.4 0.45 0.5 rg {self.margin_left + 14} {self.cursor_y - 62} Td (Team Drishti • SIT Pune • SIH 26170 Engineering Specification) Tj ET ")

        self.current_stream.append("".join(s))
        self.cursor_y -= 95

    def add_h1(self, text):
        self.ensure_space(42)
        s = []
        self.cursor_y -= 14
        # Section bar
        s.append("0.059 0.169 0.361 RG 1.2 w ")
        s.append(f"{self.margin_left} {self.cursor_y - 4} m {self.width - self.margin_right} {self.cursor_y - 4} l S ")
        s.append(f"BT /F2 13 Tf 0.059 0.169 0.361 rg {self.margin_left} {self.cursor_y} Td ({self._clean(text)}) Tj ET ")
        self.current_stream.append("".join(s))
        self.cursor_y -= 18

    def add_h2(self, text):
        self.ensure_space(32)
        s = []
        self.cursor_y -= 10
        s.append(f"BT /F2 11 Tf 0.118 0.251 0.686 rg {self.margin_left} {self.cursor_y} Td ({self._clean(text)}) Tj ET ")
        self.current_stream.append("".join(s))
        self.cursor_y -= 15

    def add_h3(self, text):
        self.ensure_space(26)
        s = []
        self.cursor_y -= 8
        s.append(f"BT /F2 10 Tf 0.486 0.227 0.929 rg {self.margin_left} {self.cursor_y} Td ({self._clean(text)}) Tj ET ")
        self.current_stream.append("".join(s))
        self.cursor_y -= 14

    def add_p(self, text, indent=0):
        lines = self._wrap_text(text, self.content_w - indent, font_size=9.5, font_name="F1")
        for line in lines:
            self.ensure_space(14)
            s = f"BT /F1 9.5 Tf 0.12 0.16 0.23 rg {self.margin_left + indent} {self.cursor_y} Td ({self._clean(line)}) Tj ET "
            self.current_stream.append(s)
            self.cursor_y -= 13.5
        self.cursor_y -= 3

    def add_bullet(self, bold_prefix, text):
        lines = self._wrap_text(bold_prefix + " " + text, self.content_w - 18, font_size=9.2, font_name="F1")
        for idx, line in enumerate(lines):
            self.ensure_space(13)
            s = []
            if idx == 0:
                s.append(f"BT /F2 10 Tf 0.918 0.345 0.047 rg {self.margin_left + 4} {self.cursor_y} Td (>) Tj ET ")
            s.append(f"BT /F1 9.2 Tf 0.12 0.16 0.23 rg {self.margin_left + 16} {self.cursor_y} Td ({self._clean(line)}) Tj ET ")
            self.current_stream.append("".join(s))
            self.cursor_y -= 13
        self.cursor_y -= 2

    def add_formula_box(self, label, formula, explanation=""):
        f_lines = formula.split("\n")
        exp_lines = self._wrap_text(explanation, self.content_w - 24, font_size=8.5, font_name="F1") if explanation else []
        box_h = 24 + (len(f_lines) * 14) + (len(exp_lines) * 12) + (8 if exp_lines else 0)
        self.ensure_space(box_h + 10)

        s = []
        # Box background
        s.append("0.97 0.98 1.0 rg ") # soft blue-gray
        s.append(f"{self.margin_left} {self.cursor_y - box_h} {self.content_w} {box_h} re f ")
        # Left bar (Navy / Blue)
        s.append("0.059 0.169 0.361 rg ")
        s.append(f"{self.margin_left} {self.cursor_y - box_h} 4 {box_h} re f ")
        # Border
        s.append("0.8 0.85 0.92 RG 0.6 w ")
        s.append(f"{self.margin_left} {self.cursor_y - box_h} {self.content_w} {box_h} re S ")

        # Label
        s.append(f"BT /F2 8.5 Tf 0.059 0.169 0.361 rg {self.margin_left + 12} {self.cursor_y - 12} Td ({self._clean(label.upper())}) Tj ET ")

        # Formulas (Courier Monospace / Bold)
        cur_y = self.cursor_y - 25
        for fl in f_lines:
            s.append(f"BT /F4 9.5 Tf 0.059 0.169 0.361 rg {self.margin_left + 14} {cur_y} Td ({self._clean(fl)}) Tj ET ")
            cur_y -= 14

        # Explanation
        if exp_lines:
            cur_y -= 2
            for el in exp_lines:
                s.append(f"BT /F3 8.5 Tf 0.28 0.33 0.41 rg {self.margin_left + 14} {cur_y} Td ({self._clean(el)}) Tj ET ")
                cur_y -= 12

        self.current_stream.append("".join(s))
        self.cursor_y -= (box_h + 8)

    def add_callout(self, title, text, border_color=(0.918, 0.345, 0.047), bg_color=(1.0, 0.97, 0.93)):
        lines = self._wrap_text(text, self.content_w - 24, font_size=8.8, font_name="F1")
        box_h = 22 + (len(lines) * 12.5)
        self.ensure_space(box_h + 8)

        s = []
        r, g, b = bg_color
        s.append(f"{r} {g} {b} rg ")
        s.append(f"{self.margin_left} {self.cursor_y - box_h} {self.content_w} {box_h} re f ")
        br, bg, bb = border_color
        s.append(f"{br} {bg} {bb} rg ")
        s.append(f"{self.margin_left} {self.cursor_y - box_h} 3.5 {box_h} re f ")
        s.append(f"0.85 0.85 0.85 RG 0.5 w {self.margin_left} {self.cursor_y - box_h} {self.content_w} {box_h} re S ")

        s.append(f"BT /F2 9 Tf {br} {bg} {bb} rg {self.margin_left + 12} {self.cursor_y - 12} Td ({self._clean(title)}) Tj ET ")
        cur_y = self.cursor_y - 24
        for line in lines:
            s.append(f"BT /F1 8.8 Tf 0.2 0.25 0.33 rg {self.margin_left + 12} {cur_y} Td ({self._clean(line)}) Tj ET ")
            cur_y -= 12.5

        self.current_stream.append("".join(s))
        self.cursor_y -= (box_h + 8)

    def add_table(self, headers, rows, col_widths=None):
        num_cols = len(headers)
        if not col_widths:
            col_widths = [self.content_w / num_cols] * num_cols

        row_h = 16.0
        table_h = row_h * (len(rows) + 1)
        self.ensure_space(min(table_h + 10, 120))

        # Header
        s = []
        s.append("0.059 0.169 0.361 rg ") # Navy
        s.append(f"{self.margin_left} {self.cursor_y - row_h} {self.content_w} {row_h} re f ")
        s.append("0.059 0.169 0.361 RG 0.5 w ")

        cur_x = self.margin_left
        for i, h_txt in enumerate(headers):
            w = col_widths[i]
            s.append(f"BT /F2 8.2 Tf 1 1 1 rg {cur_x + 4} {self.cursor_y - 11} Td ({self._clean(h_txt)}) Tj ET ")
            cur_x += w

        self.current_stream.append("".join(s))
        self.cursor_y -= row_h

        # Rows
        for r_idx, row in enumerate(rows):
            self.ensure_space(row_h + 4)
            s = []
            bg = (0.97, 0.98, 0.99) if r_idx % 2 == 1 else (1.0, 1.0, 1.0)
            s.append(f"{bg[0]} {bg[1]} {bg[2]} rg ")
            s.append(f"{self.margin_left} {self.cursor_y - row_h} {self.content_w} {row_h} re f ")
            s.append("0.88 0.91 0.94 RG 0.5 w ")
            s.append(f"{self.margin_left} {self.cursor_y - row_h} m {self.width - self.margin_right} {self.cursor_y - row_h} l S ")

            cur_x = self.margin_left
            for i, val in enumerate(row):
                w = col_widths[i]
                val_str = str(val)
                # truncate if too long
                if len(val_str) > int(w / 4.8):
                    val_str = val_str[:int(w / 4.8) - 2] + ".."
                s.append(f"BT /F1 8.2 Tf 0.12 0.16 0.23 rg {cur_x + 4} {self.cursor_y - 11} Td ({self._clean(val_str)}) Tj ET ")
                cur_x += w

            self.current_stream.append("".join(s))
            self.cursor_y -= row_h

        self.cursor_y -= 8

    def _wrap_text(self, text, max_w, font_size=9.5, font_name="F1"):
        avg_char_w = font_size * 0.48
        max_chars = max(10, int(max_w / avg_char_w))
        words = text.split(" ")
        lines = []
        cur_line = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + 1 <= max_chars:
                cur_line.append(w)
                cur_len += len(w) + 1
            else:
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_len = len(w)
        if cur_line:
            lines.append(" ".join(cur_line))
        return lines

    def _clean(self, text):
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").replace("\r", "").replace("\n", " ")

    def build(self):
        self._draw_header_footer()
        self.pages.append("".join(self.current_stream))

        pdf_objs = []
        # Object 1: Catalog
        pdf_objs.append("<< /Type /Catalog /Pages 2 0 R >>")
        # Object 2: Pages
        page_refs = " ".join([f"{3 + i*2} 0 R" for i in range(len(self.pages))])
        pdf_objs.append(f"<< /Type /Pages /Kids [{page_refs}] /Count {len(self.pages)} >>")

        # Fonts (F1: Helvetica, F2: Helvetica-Bold, F3: Helvetica-Oblique, F4: Courier-Bold)
        font_obj_idx = 3 + len(self.pages) * 2
        font_objs = [
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold /Encoding /WinAnsiEncoding >>"
        ]

        # For each page: Page Object & Content Stream Object
        for i, p_stream in enumerate(self.pages):
            p_obj_num = 3 + i*2
            c_obj_num = 4 + i*2
            f1_num = font_obj_idx
            f2_num = font_obj_idx + 1
            f3_num = font_obj_idx + 2
            f4_num = font_obj_idx + 3
            # Page Object
            p_obj = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width:.2f} {self.height:.2f}] /Resources << /Font << /F1 {f1_num} 0 R /F2 {f2_num} 0 R /F3 {f3_num} 0 R /F4 {f4_num} 0 R >> >> /Contents {c_obj_num} 0 R >>"
            pdf_objs.append(p_obj)
            # Content Stream
            stream_b = p_stream.encode("latin-1", "replace")
            c_obj = f"<< /Length {len(stream_b)} >>\nstream\n{p_stream}\nendstream"
            pdf_objs.append(c_obj)

        pdf_objs.extend(font_objs)

        # Write PDF with binary xref table
        out = bytearray()
        out.extend(b"%PDF-1.4\n")
        xref_offsets = [0]

        for i, obj in enumerate(pdf_objs, start=1):
            xref_offsets.append(len(out))
            out.extend(f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1", "replace"))

        start_xref = len(out)
        out.extend(f"xref\n0 {len(pdf_objs) + 1}\n".encode("latin-1"))
        out.extend(b"0000000000 65535 f \n")
        for off in xref_offsets[1:]:
            out.extend(f"{off:010d} 00000 n \n".encode("latin-1"))

        out.extend(f"trailer\n<< /Size {len(pdf_objs) + 1} /Root 1 0 R >>\nstartxref\n{start_xref}\n%%EOF\n".encode("latin-1"))

        with open(self.filename, "wb") as f:
            f.write(out)

        print(f"[+] Successfully compiled PDF: {self.filename} ({len(self.pages)} pages)")


# =============================================================================
# BUILD MODULE A PDF
# =============================================================================
def build_module_a_pdf():
    pdf = PDFBuilder(
        filename="/Users/samarth/Documents/SIH 26/MODULE_A_DYNAMIC_OUTLIER_SYSTEM.pdf",
        doc_title="Module A: Dynamic Outlier Detection System",
        doc_subtitle="Full-Curve Morphometry, Robust Dynamic IQR & Isolation Forest ML",
        team_header="Team Drishti • SIH 26170 • Module A Specification"
    )

    pdf.add_title_banner(
        category="Smart India Hackathon 2024 • Problem Statement SIH26170",
        title="MODULE A: DYNAMIC OUTLIER DETECTION SYSTEM",
        subtitle="Full-Curve Morphometry, Robust Dynamic IQR Statistics, 500-Tree Isolation Forest & Dual-Layer Decision Fusion"
    )

    pdf.add_h1("1. Problem Statement & The Latent Defect Dilemma")
    pdf.add_p(
        "In space satellite payloads and defense avionics, semiconductor components (IGBTs, MOSFETs) undergo high-temperature "
        "burn-in screening (125°C). Traditional automated test benches evaluate quality using fixed scalar datasheet limits. "
        "This creates the Latent Defect Blind Spot: a component exhibiting 45 μA in a lot where the nominal mean is 10 μA (σ = 1.2 μA) "
        "is a +29.1σ extreme outlier, yet technically PASSES a static 50 μA catalog ceiling. Module A solves this by ingesting "
        "complete multi-cycle I-V characterization sweep curves and performing dual-layer population-relative anomaly detection."
    )
    pdf.add_callout(
        "THE DUAL-LAYER ADVANTAGE OVER LEGACY SCALAR SCREENING",
        "1. Evaluates full dynamic curve geometry across the operational envelope rather than isolated single-point voltages.\n"
        "2. Extracts 17 non-parametric morphometric & electrical features capturing knee shifts, slopes, and energy integrals.\n"
        "3. Combines Robust Dynamic IQR scoring (Layer 1) with an unsupervised 500-tree Isolation Forest (Layer 2) for fusion scoring."
    )

    pdf.add_h1("2. Mathematical Formulation of the 17 Morphometric Features")
    pdf.add_p(
        "For an input sweep curve consisting of discrete sampled voltage-current coordinate pairs (V_i, I_i) for i = 1 to K, "
        "the engine computes 17 rigorous non-parametric mathematical feature integrals:"
    )

    feat_table = [
        ["1", "min_voltage (V_min)", "min_{1<=i<=K} (V_i)", "Baseline zero-bias contact offset"],
        ["2", "max_voltage (V_max)", "max_{1<=i<=K} (V_i)", "Peak applied electrical stress bias"],
        ["3", "min_current (I_min)", "min_{1<=i<=K} (I_i)", "Sub-threshold leakage noise floor (μA)"],
        ["4", "max_current (I_max)", "max_{1<=i<=K} (I_i)", "Peak saturation / avalanche ceiling (μA)"],
        ["5", "mean_current (I_bar)", "(1/K) ∑_{i=1}^K I_i", "Global thermal dissipation across sweep"],
        ["6", "std_current (σ_I)", "√[ (1/(K-1)) ∑ (I_i - I_bar)² ]", "Curve dispersion and variability"],
        ["7", "max_slope (g_m_max)", "max_i [ (I_i+1 - I_i)/(V_i+1 - V_i) ]", "Peak transconductance / avalanche steepness"],
        ["8", "mean_slope (g_m_bar)", "(1/(K-1)) ∑ [ (I_i+1 - I_i)/(V_i+1 - V_i) ]", "Average channel dynamic conductance"],
        ["9", "knee_voltage (V_knee)", "arg max_{V_i} (dI / dV)", "Avalanche breakdown knee (V_BR) or turn-on (V_th)"],
        ["10", "current_v25 (I_V25)", "I( V_min + 0.25·(V_max - V_min) )", "Low-field ohmic and SRH recombination current"],
        ["11", "current_v50 (I_V50)", "I( V_min + 0.50·(V_max - V_min) )", "Mid-field Poole-Frenkel carrier emission"],
        ["12", "current_v75 (I_V75)", "I( V_min + 0.75·(V_max - V_min) )", "Pre-avalanche impact ionization onset"],
        ["13", "current_v90 (I_V90)", "I( V_min + 0.90·(V_max - V_min) )", "High-field avalanche multiplication leakage"],
        ["14", "voltage_10pct (V_I10)", "V( I_min + 0.10·(I_max - I_min) )", "Sub-threshold conduction boundary voltage"],
        ["15", "voltage_50pct (V_I50)", "V( I_min + 0.50·(I_max - I_min) )", "Conduction transition midpoint voltage"],
        ["16", "voltage_90pct (V_I90)", "V( I_min + 0.90·(I_max - I_min) )", "Hard saturation / avalanche boundary voltage"],
        ["17", "curve_area (A_curve)", "∑ [ (I_i + I_i+1)/2 ] · (V_i+1 - V_i)", "Total integrated energy dissipation (μA·V)"]
    ]
    pdf.add_table(["#", "Feature Symbol", "Mathematical Formula", "Physical Significance"], feat_table, [24, 110, 180, 189])

    pdf.add_h1("3. Layer 1: Robust Dynamic IQR & MAD Anomaly Scoring")
    pdf.add_p(
        "Standard Gaussian statistics (mean and standard deviation) are highly sensitive to contaminated lot samples containing "
        "defective devices. To ensure mathematical resilience, Layer 1 employs robust location and scale estimators:"
    )
    pdf.add_formula_box(
        "ROBUST Z-SCORE & DYNAMIC THRESHOLD FORMULATION",
        "Median_j = median( X_j ),    MAD_j = median( |X_j - Median_j| )\n"
        "Robust_Z_ij = ( X_ij - Median_j ) / [ 1.4826 · max(MAD_j, 10^-9) ]\n"
        "S_dynamic(i) = max_{1 <= j <= 17} |Robust_Z_ij|\n"
        "θ_dynamic = median( {S_dynamic(k)} ) + 3.0 · 1.4826 · MAD( {S_dynamic(k)} )",
        "Where the factor 1.4826 normalizes the Median Absolute Deviation to match the standard normal distribution scale."
    )

    pdf.add_h1("4. Layer 2: 500-Tree Unsupervised Isolation Forest")
    pdf.add_p(
        "To capture non-linear multi-feature interactions across the 17-dimensional space, Layer 2 trains an unsupervised ensemble "
        "of T = 500 Isolation Trees that recursively isolate data points by random attribute partitioning:"
    )
    pdf.add_formula_box(
        "ISOLATION FOREST PATH LENGTH & ANOMALY DEPTH",
        "c(n) = 2 · ln(n - 1) + 0.5772156649 - [ 2 · (n - 1) / n ]\n"
        "s(x, n) = 2^[ -E(h(x)) / c(n) ] in [0, 1]",
        "Where E(h(x)) is the average tree path length. Defective anomalies isolate near tree roots (E(h) -> 0 => s -> 1)."
    )

    pdf.add_h1("5. Dual-Layer Evidence Fusion & Decision Policies")
    pdf.add_formula_box(
        "DUAL-LAYER FUSION FORMULA & NASA EEE-INST-002 CRITERIA",
        "S_norm_dyn = S_dynamic / max(θ_dynamic, 1.0)\n"
        "S_combined = 0.60 · S_norm_dyn + 0.40 · [ s(x, n) / 0.5 ]\n\n"
        "• PASS   : S_combined < 0.70 AND S_dynamic <= θ_dynamic  (Nominal population conformance)\n"
        "• HOLD   : 0.70 <= S_combined < 1.00                    (Subtle drift / inspector review required)\n"
        "• REJECT : S_combined >= 1.00 OR S_dynamic > 2.5·θ_dynamic (Critical curve collapse / avalanche runaway)",
        "Combines dynamic statistical evidence (60% weight) with multi-dimensional isolation structure (40% weight)."
    )

    pdf.add_h1("6. Experimental Validation Matrix on NASA Sweeps")
    val_table = [
        ["Curve 0 (Nominal)", "0.010 μA", "0.000045", "1.28", "8.08", "0.342", "0.38", "PASS", "Ohmic baseline"],
        ["Curve 8 (Moderate)", "0.045 μA", "0.000180", "6.45", "8.08", "0.485", "0.86", "HOLD", "Elevated SRH traps"],
        ["Curve 9 (Defective)", "85.0 μA", "0.001440", "31.12", "8.08", "0.631", "2.20", "REJECT", "Avalanche runaway"],
        ["Curve 2 (Collapse)", "120.0 μA", "0.002890", "809.41", "8.08", "0.718", "42.50", "REJECT", "Junction punch-thru"]
    ]
    pdf.add_table(["Test Curve", "Peak I", "Max Slope", "Dyn Score", "Threshold", "Iso Score", "Combined", "Verdict", "Physical Mode"], val_table, [85, 45, 55, 50, 48, 48, 48, 45, 79])

    pdf.add_h1("7. UI Implementation & REST API Bridge")
    pdf.add_bullet("Segmented Model Selector:", "Instant switching between Breakdown, Leakage IV, and Turn-On sweep datasets.")
    pdf.add_bullet("Sweep Preset Chips:", "Direct testing of Curve 9 (Defective), Curve 8, Curve 2, Curve 0 (PASS), and Custom Injection.")
    pdf.add_bullet("Interactive Visual Canvases:", "Dual Chart.js overlays rendering full Population Bands and 17-Feature Z-Score Deviations.")
    pdf.add_bullet("REST API Endpoints:", "POST /api/anomaly/detect, GET /api/anomaly/population, GET /api/anomaly/features.")

    pdf.build()


# =============================================================================
# BUILD MODULE B PDF
# =============================================================================
def build_module_b_pdf():
    pdf = PDFBuilder(
        filename="/Users/samarth/Documents/SIH 26/MODULE_B_TIME_SERIES_DEGRADATION.pdf",
        doc_title="Module B: Time-Series Environmental Stress Screening",
        doc_subtitle="Degradation Forecasting, Residual Tracking & Physics-of-Failure AI Explainer",
        team_header="Team Drishti • SIH 26170 • Module B Specification"
    )

    pdf.add_title_banner(
        category="Smart India Hackathon 2024 • Problem Statement SIH26170",
        title="MODULE B: TIME-SERIES DEGRADATION & DRIFT PREDICTOR",
        subtitle="Sequential Burn-In Telemetry (N=3,790), Gradient Boosted Regression, Residual Tracking & Groq Llama 3.3 AI Explainer"
    )

    pdf.add_h1("1. Operational Context & Time-Series Burn-In Telemetry")
    pdf.add_p(
        "Module B analyzes chronological semiconductor degradation across N = 3,790 observations recorded at 30-minute intervals "
        "(elapsed time 0 to 113,700 minutes) under high-temperature accelerated burn-in stress (125°C). The objective is to forecast "
        "long-term degradation trajectories, calculate real-time residuals against laboratory test bench measurements, and diagnose "
        "solid-state physical wearout mechanisms before hardware deployment."
    )

    pdf.add_h1("2. Physics of Failure (PoF) Governing Equations")

    pdf.add_h2("2.1 Arrhenius Reaction Rate & Thermal Acceleration Factor")
    pdf.add_formula_box(
        "ARRHENIUS ACCELERATION FACTOR (AF_T)",
        "Reaction Rate k = A · exp[ -E_a / (k_B · T) ]\n"
        "AF_T = exp[ (E_a / k_B) · (1 / T_use - 1 / T_stress) ]\n"
        "AF_T = exp[ (0.8 / 8.61733e-5) · (1/298.15 - 1/398.15) ] ≈ exp(7.823) ≈ 2,498×",
        "For Si junction defects (E_a = 0.8 eV), 100 hrs of 125°C screening simulates ~249,800 operating hours (~28.5 years)."
    )

    pdf.add_h2("2.2 Avalanche Breakdown & Impact Ionization Dynamics")
    pdf.add_formula_box(
        "CHYNOWETH'S LAW & AVALANCHE MULTIPLICATION",
        "Ionization Coefficient: α(E) = A · exp( -B / E )\n"
        "Multiplication Factor:   M = 1 / [ 1 - ∫_0^W α(E) dx ]\n"
        "Breakdown Condition:     ∫_0^W α(E) dx = 1  =>  M -> infinity",
        "Electric field peaks at junction curvature defects trigger premature avalanche knee collapse (V_BR < 520V)."
    )

    pdf.add_h2("2.3 Shockley-Read-Hall (SRH) Generation & Poole-Frenkel Emission")
    pdf.add_formula_box(
        "SRH GENERATION RATE & REVERSE LEAKAGE CURRENT",
        "U_SRH = ( p · n - n_i² ) / [ τ_n(p + p_1) + τ_p(n + n_1) ]\n"
        "I_leak ∝ q · A · W_dep · ( n_i / 2τ_0 ) ∝ q · A · √[ (2ε_s(V_bi + V_R))/(q N_d) ] · ( σ_trap · v_th · N_t · n_i )\n"
        "Poole-Frenkel Barrier Lowering:  ΔΦ_PF = √[ (q³ E) / (π ε_0 ε_r) ]",
        "High defect trap density (N_t) accelerates sub-threshold reverse leakage square-root growth with applied bias."
    )

    pdf.add_h2("2.4 Oxide Degradation & Transconductance Collapse")
    pdf.add_formula_box(
        "THRESHOLD VOLTAGE DRIFT & TRANSCONDUCTANCE (g_m)",
        "V_th(t) = Φ_MS + 2ψ_B + √(4q ε_s N_A ψ_B)/C_ox - [ Q_ox(t) + q ΔN_it(t) ] / C_ox\n"
        "g_m = ∂I_C / ∂V_GE = μ_eff · C_ox · (W / L) · ( V_GE - V_th )\n"
        "μ_eff = μ_0 / [ 1 + α_it · ΔN_it ]",
        "Trapped oxide charge and interface states induce positive threshold voltage shift and channel mobility collapse."
    )

    pdf.add_h1("3. Time-Series Feature Engineering & Machine Learning")
    pdf.add_p(
        "To prevent lookahead data leakage, feature engineering processes the sequence in strict chronological order:"
    )
    pdf.add_bullet("Historical Lags:", "I(t_{k-1}), I(t_{k-2}), V(t_{k-1}) capturing past temporal momentum.")
    pdf.add_bullet("Leakage-Safe Rolling Stats:", "Rolling mean μ_roll and standard deviation σ_roll over 6-hour windows (12 steps).")
    pdf.add_bullet("Power & Resistance Interactions:", "Instantaneous power P(t_k) = V·I and dynamic impedance R_dyn = ΔV / ΔI.")
    pdf.add_bullet("Chronological Train/Test Split:", "Past 80% baseline training and future 20% unseen evaluation without shuffling.")

    pdf.add_h2("3.1 Gradient Boosted Regression (Huber Loss Optimization)")
    pdf.add_formula_box(
        "GRADIENT BOOSTED DECISION ENSEMBLE",
        "Huber Loss: L_δ(y, y_hat) = 0.5(y - y_hat)² for |y - y_hat| <= δ, else δ|y - y_hat| - 0.5δ²\n"
        "Ensemble:   y_hat_M(x) = y_hat_0(x) + ∑_{m=1}^M γ_m · h_m(x)",
        "Minimizes pseudo-residuals across boosting stages with robust tolerance to laboratory measurement noise."
    )

    pdf.add_h2("3.2 Residual Discrepancy & Drift Tracking Metrics")
    pdf.add_formula_box(
        "RESIDUAL ERROR & DRIFT PERCENTAGE",
        "Delta e = I_measured - I_forecast\n"
        "Percentage Drift %_diff = [ |I_measured - I_forecast| / max(|I_forecast|, 10^-6) ] · 100%\n"
        "Drift Ratio R = I_measured / max(I_forecast, 10^-6)\n\n"
        "• PASS   : %_diff <= 15% AND R < 1.5   (Normal degradation trajectory)\n"
        "• HOLD   : 15% < %_diff <= 50%         (Moderate thermal drift requiring re-test)\n"
        "• REJECT : %_diff > 50% OR R >= 2.0    (Accelerated dielectric breakdown / runaway)",
        "Provides scalar screening decisions based on time-series forecasting deviation."
    )

    pdf.add_h1("4. Physics-Grounded Generative AI Diagnostics (Groq Llama 3.3)")
    pdf.add_p(
        "Powered by Groq Llama 3.3 70B Versatile, the system translates mathematical residuals into structured failure physics reports:"
    )
    pdf.add_bullet("Telemetry Residual:", "Quantifies discrepancy (e) and drift percentage against expected baseline.")
    pdf.add_bullet("Root Cause Mechanism:", "Identifies Avalanche Multiplication, SRH Trapping, Poole-Frenkel, or Oxide Degradation.")
    pdf.add_bullet("Flight Action Verdict:", "Renders actionable quality assurance recommendations for NASA EEE-INST-002 screening.")
    pdf.add_bullet("Deterministic Fallback:", "Built-in offline physics expert engine executes with zero external dependencies.")

    pdf.add_h1("5. Fullstack User Interface & Interactive Controls")
    pdf.add_bullet("Time Scrubber (0 to 113,700 min):", "Real-time Auto-Play simulation of multi-day burn-in aging.")
    pdf.add_bullet("Synchronized Voltage/Current Sliders:", "Instantaneous DUT bias testing with bidirectional data binding.")
    pdf.add_bullet("Dual Telemetry Canvases:", "Chart 1 (Leakage vs Time) and Chart 2 (Voltage Profile & Transfer Curves).")
    pdf.add_bullet("AI Diagnostics Window:", "Collision-free 2-row header displaying active model (🟢 Groq LPU • Llama 3.3 70B).")
    pdf.add_bullet("Welcome Dashboard:", "4 interactive quick-start cards for Avalanche, SRH Trapping, Policies, and 17 Features.")

    pdf.build()


if __name__ == "__main__":
    print("[*] Generating Module A and Module B PDFs...")
    build_module_a_pdf()
    build_module_b_pdf()
    print("[+] Done!")
