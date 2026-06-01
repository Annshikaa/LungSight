from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class BoundingBox(BaseModel):
    x: int
    y: int
    w: int
    h: int


class HeatmapInfo(BaseModel):
    method: str
    heatmap_b64: str
    overlay_b64: str
    bounding_box: Optional[BoundingBox] = None
    activation_coverage: float


class SegmentationInfo(BaseModel):
    mask_b64: str
    overlay_b64: str
    roi_b64: str
    lung_area_pixels: int
    lung_area_percentage: float
    dice_score: Optional[float] = None
    iou_score: Optional[float] = None


class SeverityInfo(BaseModel):
    score: float
    level: str
    color: str
    recommendations: List[str]
    clinical_summary: str


class UncertaintyInfo(BaseModel):
    confidence_percent: float
    uncertainty_percent: float
    variance: float
    entropy: float
    reliability: str
    reliability_color: str


class IndividualModelScore(BaseModel):
    model: str
    pneumonia_probability: float
    label: str


class PredictionResponse(BaseModel):
    scan_id: str
    prediction_id: str

    # Core prediction
    label: str
    confidence: float
    pneumonia_probability: float
    normal_probability: float
    model_used: str
    inference_time_ms: float

    # Ensemble
    individual_predictions: Optional[Dict[str, float]] = None
    ensemble_agreement: Optional[float] = None

    # Severity
    severity: SeverityInfo

    # Uncertainty
    uncertainty: UncertaintyInfo

    # Explainability
    heatmaps: Dict[str, HeatmapInfo]

    # Segmentation
    segmentation: Optional[SegmentationInfo] = None

    # Images (base64 PNG)
    original_image_b64: str
    enhanced_image_b64: str

    # DICOM metadata
    dicom_metadata: Optional[Dict[str, Any]] = None

    # Timestamp
    created_at: str


class PredictionHistoryItem(BaseModel):
    prediction_id: str
    scan_id: str
    label: str
    confidence: float
    severity_level: str
    severity_score: float
    model_used: str
    inference_time_ms: float
    created_at: datetime


class AnalyticsResponse(BaseModel):
    total_scans: int
    pneumonia_cases: int
    normal_cases: int
    average_confidence: float
    average_severity_score: float
    model_accuracy_estimate: float
    severity_distribution: Dict[str, int]
    prediction_trend: List[Dict[str, Any]]
    model_usage: Dict[str, int]


class BenchmarkResponse(BaseModel):
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    pr_auc: float
    avg_inference_time_ms: float
    model_size_mb: float
    parameter_count: int
    confusion_matrix: List[List[int]]


class LeaderboardEntry(BaseModel):
    rank: int
    model: str
    accuracy: float
    f1: float
    roc_auc: float
    inference_ms: float
    size_mb: float


class ReportRequest(BaseModel):
    prediction_id: str
    patient_name: str = "Anonymous"
    patient_id: str = "N/A"
    patient_age: str = "N/A"
    patient_sex: str = "N/A"
    referring_doctor: str = "N/A"
    doctor_notes: str = ""
    # Prediction data (sent from frontend after analysis)
    label: str = "NORMAL"
    confidence: float = 0.0
    severity_level: str = "Normal"
    severity_score: float = 0.0
    model_used: str = "Ensemble"
    inference_time_ms: float = 0.0
    uncertainty_percent: float = 0.0
    reliability: str = "High"
    clinical_summary: str = ""
    recommendations: List[str] = []
