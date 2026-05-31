from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

class UserRole(str, PyEnum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    RADIOLOGIST = "radiologist"
    RESEARCHER = "researcher"


class PredictionLabel(str, PyEnum):
    NORMAL = "NORMAL"
    PNEUMONIA = "PNEUMONIA"


class SeverityLevel(str, PyEnum):
    NORMAL = "Normal"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"
    CRITICAL = "Critical"


class ModelName(str, PyEnum):
    DENSENET121 = "DenseNet121"
    EFFICIENTNETB3 = "EfficientNetB3"
    RESNET50 = "ResNet50"
    VGG16 = "VGG16"
    ENSEMBLE = "Ensemble"


# ──────────────────────────────────────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.RESEARCHER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    scans = relationship("XRayScan", back_populates="uploaded_by_user")
    reports = relationship("Report", back_populates="generated_by_user")


# ──────────────────────────────────────────────────────────────────────────────
# Patients
# ──────────────────────────────────────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    patient_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    extra_data = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scans = relationship("XRayScan", back_populates="patient")


# ──────────────────────────────────────────────────────────────────────────────
# X-Ray Scans
# ──────────────────────────────────────────────────────────────────────────────

class XRayScan(Base):
    __tablename__ = "xray_scans"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    patient_id = Column(UUID(as_uuid=False), ForeignKey("patients.id"), nullable=True)
    uploaded_by = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_format = Column(String(20), nullable=False)  # png, jpg, dicom
    file_size_bytes = Column(Integer, nullable=True)
    is_dicom = Column(Boolean, default=False)
    dicom_metadata = Column(JSON, nullable=True)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="scans")
    uploaded_by_user = relationship("User", back_populates="scans")
    predictions = relationship("Prediction", back_populates="scan")
    segmentations = relationship("Segmentation", back_populates="scan")


# ──────────────────────────────────────────────────────────────────────────────
# Predictions
# ──────────────────────────────────────────────────────────────────────────────

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    scan_id = Column(UUID(as_uuid=False), ForeignKey("xray_scans.id"), nullable=False)
    model_used = Column(Enum(ModelName), nullable=False)
    label = Column(Enum(PredictionLabel), nullable=False)
    confidence = Column(Float, nullable=False)
    pneumonia_probability = Column(Float, nullable=False)
    normal_probability = Column(Float, nullable=False)
    severity_level = Column(Enum(SeverityLevel), nullable=True)
    severity_score = Column(Float, nullable=True)
    uncertainty = Column(Float, nullable=True)
    inference_time_ms = Column(Float, nullable=True)
    all_model_scores = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("XRayScan", back_populates="predictions")
    heatmaps = relationship("Heatmap", back_populates="prediction")
    reports = relationship("Report", back_populates="prediction")


# ──────────────────────────────────────────────────────────────────────────────
# Segmentations
# ──────────────────────────────────────────────────────────────────────────────

class Segmentation(Base):
    __tablename__ = "segmentations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    scan_id = Column(UUID(as_uuid=False), ForeignKey("xray_scans.id"), nullable=False)
    mask_path = Column(String(500), nullable=False)
    overlay_path = Column(String(500), nullable=True)
    roi_path = Column(String(500), nullable=True)
    dice_score = Column(Float, nullable=True)
    iou_score = Column(Float, nullable=True)
    lung_area_pixels = Column(Integer, nullable=True)
    lung_area_percentage = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("XRayScan", back_populates="segmentations")


# ──────────────────────────────────────────────────────────────────────────────
# Heatmaps
# ──────────────────────────────────────────────────────────────────────────────

class Heatmap(Base):
    __tablename__ = "heatmaps"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    prediction_id = Column(UUID(as_uuid=False), ForeignKey("predictions.id"), nullable=False)
    method = Column(String(50), nullable=False)  # gradcam, gradcam++, saliency, ig
    heatmap_path = Column(String(500), nullable=False)
    overlay_path = Column(String(500), nullable=True)
    bounding_box = Column(JSON, nullable=True)
    activation_coverage = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prediction = relationship("Prediction", back_populates="heatmaps")


# ──────────────────────────────────────────────────────────────────────────────
# Reports
# ──────────────────────────────────────────────────────────────────────────────

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    prediction_id = Column(UUID(as_uuid=False), ForeignKey("predictions.id"), nullable=False)
    generated_by = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    pdf_path = Column(String(500), nullable=False)
    doctor_notes = Column(Text, nullable=True)
    clinical_summary = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prediction = relationship("Prediction", back_populates="reports")
    generated_by_user = relationship("User", back_populates="reports")


# ──────────────────────────────────────────────────────────────────────────────
# Model Benchmarks
# ──────────────────────────────────────────────────────────────────────────────

class ModelBenchmark(Base):
    __tablename__ = "model_benchmarks"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    model_name = Column(Enum(ModelName), nullable=False)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    roc_auc = Column(Float, nullable=True)
    pr_auc = Column(Float, nullable=True)
    avg_inference_time_ms = Column(Float, nullable=True)
    model_size_mb = Column(Float, nullable=True)
    parameter_count = Column(Integer, nullable=True)
    flops = Column(Float, nullable=True)
    test_samples = Column(Integer, nullable=True)
    confusion_matrix = Column(JSON, nullable=True)
    benchmark_date = Column(DateTime(timezone=True), server_default=func.now())
    extra_metrics = Column(JSON, nullable=True)


# ──────────────────────────────────────────────────────────────────────────────
# Audit Logs
# ──────────────────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
