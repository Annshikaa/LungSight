"""
PDF diagnostic report generator using fpdf2 (pure Python, Windows compatible).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List

from fpdf import FPDF


def _safe(text: str) -> str:
    """Replace non-Latin-1 characters so Helvetica doesn't crash."""
    return (
        text.replace("—", "-").replace("–", "-")
            .replace("₂", "2").replace("²", "2")
            .replace("’", "'").replace("‘", "'")
            .replace("“", '"').replace("”", '"')
            .encode("latin-1", errors="replace").decode("latin-1")
    )


@dataclass
class ReportData:
    patient_name:        str   = "Anonymous"
    patient_id:          str   = "N/A"
    patient_age:         str   = "N/A"
    patient_sex:         str   = "N/A"
    referring_doctor:    str   = "N/A"
    prediction:          str   = "NORMAL"
    confidence:          float = 0.0
    severity_level:      str   = "Normal"
    severity_score:      float = 0.0
    model_used:          str   = "Ensemble"
    inference_time_ms:   float = 0.0
    uncertainty_percent: float = 0.0
    reliability:         str   = "High"
    clinical_summary:    str   = ""
    recommendations:     List[str] = field(default_factory=list)
    doctor_notes:        str   = ""
    hospital_name:       str   = "LungSight Medical Center"
    report_id:           str   = ""
    generated_at:        str   = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        if not self.report_id:
            self.report_id = str(uuid.uuid4())[:8].upper()


class PDFReportGenerator:

    def __init__(self, reports_dir: str | Path = "./reports/generated"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, data: ReportData) -> bytes:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        self._draw_header(pdf, data)
        self._draw_patient(pdf, data)
        self._draw_prediction(pdf, data)
        self._draw_severity(pdf, data)
        self._draw_summary(pdf, data)
        self._draw_recommendations(pdf, data)
        self._draw_notes(pdf, data)
        self._draw_disclaimer(pdf)
        self._draw_footer(pdf, data)

        raw = pdf.output()
        return bytes(raw)

    def save(self, data: ReportData) -> Path:
        pdf_bytes = self.generate(data)
        fname = f"report_{data.report_id}.pdf"
        path = self.reports_dir / fname
        path.write_bytes(pdf_bytes)
        return path

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _draw_header(self, pdf: FPDF, d: ReportData):
        pdf.set_fill_color(14, 165, 233)
        pdf.rect(10, 10, 190, 2, style="F")

        pdf.set_xy(10, 15)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(14, 165, 233)
        pdf.cell(130, 8, d.hospital_name, ln=0)

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.set_xy(140, 15)
        pdf.cell(60, 4, f"Report ID: {d.report_id}", align="R", ln=1)
        pdf.set_xy(140, 19)
        pdf.cell(60, 4, d.generated_at, align="R", ln=1)

        pdf.set_xy(10, 24)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5, "AI-Powered Chest X-Ray Diagnostic Report  |  LungSight AI v1.0", ln=1)

        pdf.set_xy(10, 30)
        pdf.set_fill_color(226, 232, 240)
        pdf.rect(10, 30, 190, 0.5, style="F")
        pdf.ln(5)

    def _section(self, pdf: FPDF, title: str):
        pdf.set_fill_color(14, 165, 233)
        pdf.rect(10, pdf.get_y(), 3, 6, style="F")
        pdf.set_x(15)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, title, ln=1)
        pdf.ln(2)

    def _draw_patient(self, pdf: FPDF, d: ReportData):
        self._section(pdf, "Patient Information")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(15, 23, 42)

        fields = [
            ("Name", d.patient_name), ("ID", d.patient_id),
            ("Age", d.patient_age),   ("Sex", d.patient_sex),
            ("Physician", d.referring_doctor), ("Model", d.model_used),
        ]
        x_start, y = 10, pdf.get_y()
        col_w = 63
        for i, (label, val) in enumerate(fields):
            col = i % 3
            row = i // 3
            x = x_start + col * col_w
            cy = y + row * 14
            pdf.set_fill_color(248, 250, 252)
            pdf.set_draw_color(226, 232, 240)
            pdf.rect(x, cy, col_w - 2, 12, style="FD")
            pdf.set_xy(x + 2, cy + 1)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(col_w - 4, 4, label, ln=1)
            pdf.set_x(x + 2)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(col_w - 4, 5, str(val)[:26], ln=0)

        pdf.set_xy(10, y + 30)
        pdf.ln(4)

    def _draw_prediction(self, pdf: FPDF, d: ReportData):
        self._section(pdf, "AI Diagnostic Prediction")
        y = pdf.get_y()

        # Badge
        r, g, b = (34, 197, 94) if d.prediction == "NORMAL" else (239, 68, 68)
        pdf.set_fill_color(r, g, b)
        pdf.rect(10, y, 50, 18, style="F")
        pdf.set_xy(10, y + 3)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(50, 12, d.prediction, align="C", ln=0)

        # Stats
        stats = [
            ("Confidence",  f"{d.confidence * 100:.1f}%"),
            ("Uncertainty", f"{d.uncertainty_percent:.1f}%"),
            ("Reliability", d.reliability),
            ("Time",        f"{d.inference_time_ms:.0f}ms"),
        ]
        for i, (lbl, val) in enumerate(stats):
            x = 65 + i * 34
            pdf.set_xy(x, y)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(32, 5, lbl, ln=0)
            pdf.set_xy(x, y + 5)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(32, 8, val, ln=0)

        pdf.set_xy(10, y + 22)
        pdf.ln(2)

    def _draw_severity(self, pdf: FPDF, d: ReportData):
        sev_colors = {
            "Normal": (34,197,94), "Mild": (132,204,22),
            "Moderate": (245,158,11), "Severe": (239,68,68), "Critical": (127,29,29),
        }
        r, g, b = sev_colors.get(d.severity_level, (100, 116, 139))

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(60, 5, "Severity:", ln=0)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(r, g, b)
        pdf.cell(30, 5, d.severity_level, ln=0)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 5, f"{d.severity_score:.0f}/100", align="R", ln=1)

        y = pdf.get_y()
        pdf.set_fill_color(226, 232, 240)
        pdf.rect(10, y, 190, 6, style="F")
        fill_w = max(1, 190 * (min(d.severity_score, 100) / 100))
        pdf.set_fill_color(r, g, b)
        pdf.rect(10, y, fill_w, 6, style="F")
        pdf.set_y(y + 8)

        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(100, 116, 139)
        for i, lbl in enumerate(["Normal", "Mild", "Moderate", "Severe", "Critical"]):
            pdf.set_x(10 + i * 47)
            pdf.cell(45, 5, lbl, ln=0)
        pdf.ln(8)

    def _draw_summary(self, pdf: FPDF, d: ReportData):
        self._section(pdf, "Clinical Summary")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(51, 65, 85)
        pdf.set_x(10)
        pdf.multi_cell(190, 5, _safe(d.clinical_summary or "No clinical summary available."))
        pdf.ln(4)

    def _draw_recommendations(self, pdf: FPDF, d: ReportData):
        self._section(pdf, "Clinical Recommendations")
        recs = d.recommendations or ["No specific recommendations available."]
        for i, rec in enumerate(recs, 1):
            pdf.set_x(10)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(14, 165, 233)
            pdf.cell(8, 6, f"{i}.", ln=0)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(182, 6, _safe(rec))
        pdf.ln(4)

    def _draw_notes(self, pdf: FPDF, d: ReportData):
        self._section(pdf, "Physician Notes")
        notes = d.doctor_notes or "No physician notes added."
        y = pdf.get_y()
        lines = max(3, len(notes) // 85 + 1)
        box_h = lines * 6 + 6
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(203, 213, 225)
        pdf.rect(10, y, 190, box_h, style="FD")
        pdf.set_xy(13, y + 3)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(184, 6, _safe(notes))
        pdf.set_y(y + box_h + 4)

    def _draw_disclaimer(self, pdf: FPDF):
        pdf.ln(4)
        y = pdf.get_y()
        pdf.set_fill_color(255, 247, 237)
        pdf.set_draw_color(254, 215, 170)
        pdf.rect(10, y, 190, 18, style="FD")
        pdf.set_xy(13, y + 2)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(146, 64, 14)
        pdf.cell(0, 5, "Important Notice:", ln=1)
        pdf.set_x(13)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.multi_cell(184, 4,
            "This report is generated by an AI system and is intended to assist - not replace - "
            "qualified medical professionals. All findings must be reviewed and verified by a "
            "licensed radiologist or physician before any clinical decisions are made.")

    def _draw_footer(self, pdf: FPDF, d: ReportData):
        pdf.ln(6)
        pdf.set_fill_color(14, 165, 233)
        pdf.rect(10, pdf.get_y(), 190, 0.5, style="F")
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5,
            f"{d.hospital_name}  |  LungSight AI v1.0  |  Report {d.report_id}  |  {d.generated_at}",
            align="C", ln=1)
