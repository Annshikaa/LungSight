"""
Core prediction service — orchestrates preprocessing, segmentation,
classification, explainability, severity, and uncertainty.
"""
from __future__ import annotations

import base64
import io
import uuid
from datetime import datetime, timezone
from typing import Optional

import torch
import numpy as np
from PIL import Image

from app.config import settings
from app.ml.preprocessing import XRayPreprocessor
from app.ml.segmentation import get_segmentation_engine
from app.ml.models import get_model_registry
from app.ml.explainability import ExplainabilityEngine
from app.ml.severity import get_severity_assessor
from app.ml.uncertainty import MCDropoutEstimator
from app.ml.ensemble import EnsemblePredictor
from app.schemas.prediction import (
    BoundingBox,
    HeatmapInfo,
    PredictionResponse,
    SegmentationInfo,
    SeverityInfo,
    UncertaintyInfo,
)
from app.utils.dicom import DICOMReader, is_dicom


IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

def _to_model_tensor(image_bytes: bytes) -> np.ndarray:
    """Exactly match val_transforms: PIL BILINEAR resize → /255 → ImageNet normalize."""
    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pil = pil.resize((224, 224), Image.BILINEAR)
    x = np.array(pil, dtype=np.float32) / 255.0
    x = (x - IMAGENET_MEAN) / IMAGENET_STD
    return x.transpose(2, 0, 1)[np.newaxis, ...]  # 1×3×224×224


def _arr_to_b64(arr: np.ndarray) -> str:
    img = Image.fromarray(arr.astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


class PredictionService:
    def __init__(self):
        self.preprocessor = XRayPreprocessor()
        self.seg_engine   = None   # lazy
        self.model_reg    = None   # lazy
        self.severity_assessor = None
        self.ensemble: Optional[EnsemblePredictor] = None

    # ------------------------------------------------------------------
    def _init(self):
        if self.model_reg is None:
            self.model_reg       = get_model_registry()
            self.seg_engine      = get_segmentation_engine()
            self.severity_assessor = get_severity_assessor()
            self.ensemble = EnsemblePredictor(self.model_reg)

    # ------------------------------------------------------------------
    async def predict(
        self,
        image_bytes: bytes,
        filename: str,
        model_name: str = "Ensemble",
        run_segmentation: bool = True,
        xai_methods: Optional[list] = None,
    ) -> PredictionResponse:
        self._init()

        _device = torch.device(
            settings.DEVICE if settings.DEVICE == "cpu" or torch.cuda.is_available() else "cpu"
        )

        # ── 1. DICOM or image load ────────────────────────────────────
        dicom_meta = None
        if is_dicom(filename):
            image_bytes, dicom_meta_obj = DICOMReader.to_png_bytes(image_bytes)
            dicom_meta = dicom_meta_obj.raw

        # ── 2. Preprocess ─────────────────────────────────────────────
        preprocessed = self.preprocessor.process(image_bytes)

        # ── 3. Segmentation ───────────────────────────────────────────
        seg_result = None
        seg_info: Optional[SegmentationInfo] = None
        if run_segmentation:
            seg_result = self.seg_engine.segment(preprocessed.original)
            seg_info = SegmentationInfo(
                mask_b64   = _arr_to_b64(np.stack([seg_result.mask]*3, axis=-1)),
                overlay_b64= _arr_to_b64(seg_result.overlay),
                roi_b64    = _arr_to_b64(seg_result.roi),
                lung_area_pixels=seg_result.lung_area_pixels,
                lung_area_percentage=seg_result.lung_area_percentage,
                dice_score=seg_result.dice_score,
                iou_score=seg_result.iou_score,
            )

        # ── 4. Classification ─────────────────────────────────────────
        # Use PIL BILINEAR resize to exactly match training val_transforms
        tensor = _to_model_tensor(image_bytes)

        individual_preds = None
        agreement = None

        if model_name == "Ensemble":
            ens_result = self.ensemble.predict(tensor)
            label      = ens_result.label
            confidence = ens_result.confidence
            pneu_prob  = ens_result.pneumonia_probability
            norm_prob  = ens_result.normal_probability
            inf_time   = ens_result.total_inference_time_ms
            individual_preds = ens_result.individual_predictions
            agreement  = ens_result.agreement_score
        else:
            cls_result = self.model_reg.predict(tensor, model_name)
            label      = cls_result.label
            confidence = cls_result.confidence
            pneu_prob  = cls_result.pneumonia_probability
            norm_prob  = cls_result.normal_probability
            inf_time   = cls_result.inference_time_ms

        # ── 5. Uncertainty ────────────────────────────────────────────
        chosen_model = (
            "DenseNet121" if model_name == "Ensemble" else model_name
        )
        raw_model = self.model_reg.get_raw_model(chosen_model)
        mc = MCDropoutEstimator(raw_model, _device, n_samples=15)
        unc_result = mc.estimate(tensor)
        unc_info = UncertaintyInfo(
            confidence_percent=unc_result.confidence_percent,
            uncertainty_percent=unc_result.uncertainty_percent,
            variance=unc_result.variance,
            entropy=unc_result.entropy,
            reliability=unc_result.reliability,
            reliability_color=unc_result.reliability_color,
        )

        # ── 6. Explainability (Grad-CAM + family) ─────────────────────
        target_layer = self.model_reg.get_target_layer(chosen_model)
        xai_engine   = ExplainabilityEngine(raw_model, target_layer, _device)
        methods = xai_methods or ["gradcam", "gradcam_pp", "saliency"]
        xai_results = xai_engine.explain(tensor, preprocessed.original, methods=methods)

        heatmaps: dict = {}
        for method, xai in xai_results.items():
            bbox = None
            if xai.bounding_box:
                x, y, w, h = xai.bounding_box
                bbox = BoundingBox(x=x, y=y, w=w, h=h)
            heatmaps[method] = HeatmapInfo(
                method=method,
                heatmap_b64=_arr_to_b64(xai.heatmap_colored),
                overlay_b64=_arr_to_b64(xai.overlay),
                bounding_box=bbox,
                activation_coverage=xai.activation_coverage,
            )

        # ── 7. Severity ───────────────────────────────────────────────
        gradcam_coverage = xai_results.get("gradcam", xai_results.get("saliency"))
        act_coverage = gradcam_coverage.activation_coverage if gradcam_coverage else 0.0
        cam_intensity = float(gradcam_coverage.heatmap.mean()) if gradcam_coverage else 0.0

        lung_inv = (seg_result.lung_area_percentage / 100.0) if seg_result else 0.0

        sev_result = self.severity_assessor.assess(
            pneumonia_probability=pneu_prob,
            activation_coverage=act_coverage,
            gradcam_intensity=cam_intensity,
            lung_involvement=lung_inv,
            is_pneumonia=label == "PNEUMONIA",
        )
        sev_info = SeverityInfo(
            score=sev_result.score,
            level=sev_result.level,
            color=sev_result.color,
            recommendations=sev_result.recommendations,
            clinical_summary=sev_result.clinical_summary,
        )

        # ── 8. Build response ─────────────────────────────────────────
        scan_id = str(uuid.uuid4())
        pred_id = str(uuid.uuid4())

        return PredictionResponse(
            scan_id=scan_id,
            prediction_id=pred_id,
            label=label,
            confidence=confidence,
            pneumonia_probability=pneu_prob,
            normal_probability=norm_prob,
            model_used=model_name,
            inference_time_ms=round(inf_time, 2),
            individual_predictions=individual_preds,
            ensemble_agreement=agreement,
            severity=sev_info,
            uncertainty=unc_info,
            heatmaps=heatmaps,
            segmentation=seg_info,
            original_image_b64=_arr_to_b64(preprocessed.original),
            enhanced_image_b64=_arr_to_b64(preprocessed.enhanced),
            dicom_metadata=dicom_meta,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
        )


_service: Optional[PredictionService] = None


def get_prediction_service() -> PredictionService:
    global _service
    if _service is None:
        _service = PredictionService()
    return _service
