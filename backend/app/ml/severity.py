"""
Pneumonia severity assessment module for LungSight AI.
Combines segmentation area, Grad-CAM intensity, activation coverage,
and model confidence to produce a 0-100 severity score.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


# ──────────────────────────────────────────────────────────────────────────────
# Severity levels
# ──────────────────────────────────────────────────────────────────────────────

SEVERITY_THRESHOLDS = {
    "Normal":   (0, 10),
    "Mild":     (10, 35),
    "Moderate": (35, 60),
    "Severe":   (60, 80),
    "Critical": (80, 100),
}

SEVERITY_COLORS = {
    "Normal":   "#22c55e",  # green
    "Mild":     "#84cc16",  # lime
    "Moderate": "#f59e0b",  # amber
    "Severe":   "#ef4444",  # red
    "Critical": "#7f1d1d",  # dark-red
}

SEVERITY_RECOMMENDATIONS = {
    "Normal": [
        "No signs of pneumonia detected.",
        "Routine follow-up recommended.",
        "Maintain healthy respiratory hygiene.",
    ],
    "Mild": [
        "Mild indicators present; clinical correlation advised.",
        "Consider repeat imaging in 7-10 days.",
        "Initiate conservative management per clinical guidelines.",
        "Monitor oxygen saturation and temperature.",
    ],
    "Moderate": [
        "Moderate pneumonia involvement detected.",
        "Prompt clinical evaluation required.",
        "Consider antibiotic therapy per local sensitivity patterns.",
        "Chest physiotherapy may be beneficial.",
        "Daily monitoring of respiratory rate and SpO₂.",
    ],
    "Severe": [
        "Significant bilateral involvement detected.",
        "Urgent specialist evaluation required.",
        "Consider hospital admission for IV antibiotics.",
        "Supplemental oxygen may be required.",
        "Monitor for respiratory failure signs.",
        "Blood cultures and inflammatory markers recommended.",
    ],
    "Critical": [
        "Critical pneumonia detected — immediate intervention required.",
        "ICU admission may be necessary.",
        "Mechanical ventilation risk assessment.",
        "Immediate specialist consultation.",
        "Consider broad-spectrum IV antibiotics.",
        "Continuous cardiac and respiratory monitoring.",
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
# Result
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class SeverityResult:
    score: float              # 0.0 – 100.0
    level: str                # Normal | Mild | Moderate | Severe | Critical
    color: str                # hex color for UI gauge
    confidence_factor: float
    activation_factor: float
    lung_involvement_factor: float
    recommendations: list[str]
    clinical_summary: str


# ──────────────────────────────────────────────────────────────────────────────
# Engine
# ──────────────────────────────────────────────────────────────────────────────

class SeverityAssessor:
    """
    Computes severity from:
      - pneumonia_probability  (0–1) from classifier
      - activation_coverage    (0–1) from Grad-CAM
      - gradcam_intensity      (0–1) mean of high-activation pixels
      - lung_involvement       (0–1) affected-lung fraction (from segmentation)
    """

    # Weight each factor's contribution to the raw score
    WEIGHTS = {
        "probability":   0.40,
        "activation":    0.25,
        "intensity":     0.20,
        "involvement":   0.15,
    }

    # ------------------------------------------------------------------
    def assess(
        self,
        pneumonia_probability: float,
        activation_coverage: float = 0.0,
        gradcam_intensity: float = 0.0,
        lung_involvement: float = 0.0,
        is_pneumonia: bool = True,
    ) -> SeverityResult:

        if not is_pneumonia:
            return self._normal_result(pneumonia_probability, activation_coverage, lung_involvement)

        # ── Weighted raw score ──────────────────────────────────────────
        raw = (
            self.WEIGHTS["probability"] * pneumonia_probability
            + self.WEIGHTS["activation"] * activation_coverage
            + self.WEIGHTS["intensity"]  * gradcam_intensity
            + self.WEIGHTS["involvement"] * lung_involvement
        )
        score = round(float(np.clip(raw * 100, 0, 100)), 1)

        level = self._score_to_level(score)
        return SeverityResult(
            score=score,
            level=level,
            color=SEVERITY_COLORS[level],
            confidence_factor=round(pneumonia_probability, 4),
            activation_factor=round(activation_coverage, 4),
            lung_involvement_factor=round(lung_involvement, 4),
            recommendations=SEVERITY_RECOMMENDATIONS[level],
            clinical_summary=self._clinical_summary(level, score, pneumonia_probability),
        )

    # ------------------------------------------------------------------
    def _normal_result(self, prob: float, act: float, inv: float) -> SeverityResult:
        return SeverityResult(
            score=round(prob * 10, 1),    # at most 10 for normal cases
            level="Normal",
            color=SEVERITY_COLORS["Normal"],
            confidence_factor=round(prob, 4),
            activation_factor=round(act, 4),
            lung_involvement_factor=round(inv, 4),
            recommendations=SEVERITY_RECOMMENDATIONS["Normal"],
            clinical_summary=(
                "AI analysis indicates no signs of pneumonia. "
                "Lung fields appear clear. Routine follow-up is advised."
            ),
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _score_to_level(score: float) -> str:
        for level, (lo, hi) in SEVERITY_THRESHOLDS.items():
            if lo <= score < hi:
                return level
        return "Critical"

    # ------------------------------------------------------------------
    @staticmethod
    def _clinical_summary(level: str, score: float, prob: float) -> str:
        pct = round(prob * 100, 1)
        summaries = {
            "Normal": (
                f"AI analysis indicates no significant pneumonia findings "
                f"(score: {score}/100, confidence: {pct}%). "
                "Lung fields appear within normal limits."
            ),
            "Mild": (
                f"Mild pneumonia indicators detected (score: {score}/100, "
                f"confidence: {pct}%). Focal consolidation or early infiltrates "
                "may be present. Clinical correlation is advised."
            ),
            "Moderate": (
                f"Moderate pneumonia involvement identified (score: {score}/100, "
                f"confidence: {pct}%). Multi-focal infiltrates present. "
                "Prompt clinical evaluation and treatment initiation recommended."
            ),
            "Severe": (
                f"Severe pneumonia detected (score: {score}/100, confidence: {pct}%). "
                "Extensive bilateral involvement noted. Urgent evaluation and "
                "hospital admission should be considered."
            ),
            "Critical": (
                f"Critical-level pneumonia identified (score: {score}/100, "
                f"confidence: {pct}%). Near-complete lung involvement suspected. "
                "Immediate intensive care evaluation is strongly recommended."
            ),
        }
        return summaries.get(level, "")


# Global singleton
_assessor: Optional[SeverityAssessor] = None


def get_severity_assessor() -> SeverityAssessor:
    global _assessor
    if _assessor is None:
        _assessor = SeverityAssessor()
    return _assessor
