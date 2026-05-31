"""
POST /predict  — main prediction endpoint.
Accepts image upload (PNG, JPG, JPEG, DICOM), runs full pipeline.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.prediction import PredictionResponse
from app.services.prediction_service import get_prediction_service

router = APIRouter(prefix="/predict", tags=["Prediction"])

ALLOWED_MIME = {
    "image/png", "image/jpeg", "image/jpg",
    "application/dicom", "application/octet-stream",
}
MAX_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post(
    "",
    response_model=PredictionResponse,
    summary="Run full AI diagnostic pipeline on a chest X-ray",
    response_description="Full prediction with heatmaps, severity, uncertainty, and segmentation",
)
async def predict(
    file: UploadFile = File(..., description="Chest X-ray image (PNG/JPG/JPEG/DICOM)"),
    model: str = Form(
        default="Ensemble",
        description="Model to use: DenseNet121 | EfficientNetB3 | ResNet50 | VGG16 | Ensemble",
    ),
    run_segmentation: bool = Form(default=True, description="Include lung segmentation"),
    xai_methods: Optional[str] = Form(
        default="gradcam,gradcam_pp,saliency",
        description="Comma-separated XAI methods: gradcam, gradcam_pp, saliency, integrated_gradients",
    ),
):
    # ── Validate ──────────────────────────────────────────────────────
    valid_models = {"DenseNet121", "EfficientNetB3", "ResNet50", "VGG16", "Ensemble"}
    if model not in valid_models:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid model '{model}'. Choose from: {', '.join(sorted(valid_models))}",
        )

    content_type = file.content_type or ""
    filename     = file.filename or "upload.png"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if content_type not in ALLOWED_MIME and ext not in {"png", "jpg", "jpeg", "dcm", "dicom"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Upload PNG, JPG, JPEG, or DICOM.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum allowed size is {MAX_BYTES // 1024 // 1024} MB.",
        )
    if len(image_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file uploaded.")

    # ── Parse XAI methods ─────────────────────────────────────────────
    methods_list = None
    if xai_methods:
        methods_list = [m.strip() for m in xai_methods.split(",") if m.strip()]

    # ── Run pipeline ──────────────────────────────────────────────────
    try:
        service  = get_prediction_service()
        response = await service.predict(
            image_bytes=image_bytes,
            filename=filename,
            model_name=model,
            run_segmentation=run_segmentation,
            xai_methods=methods_list,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction pipeline error: {str(exc)}",
        ) from exc

    return response
