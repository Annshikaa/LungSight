"""
Report generation routes.
POST /generate-report  →  generates PDF and returns as download.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.schemas.prediction import ReportRequest
from app.utils.report_generator import PDFReportGenerator, ReportData
from app.config import settings

router = APIRouter(prefix="/generate-report", tags=["Reports"])


@router.post(
    "",
    summary="Generate a professional PDF diagnostic report",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF diagnostic report",
        }
    },
)
async def generate_report(payload: ReportRequest):
    """
    Generate a professional PDF diagnostic report for a prediction.
    In production this would fetch the stored prediction from the database;
    here it constructs the report from the supplied metadata.
    """
    try:
        data = ReportData(
            patient_name=payload.patient_name,
            patient_id=payload.patient_id,
            patient_age=payload.patient_age,
            patient_sex=payload.patient_sex,
            referring_doctor=payload.referring_doctor,
            doctor_notes=payload.doctor_notes,
            hospital_name=settings.HOSPITAL_NAME,
            prediction=payload.label,
            confidence=payload.confidence,
            severity_level=payload.severity_level,
            severity_score=payload.severity_score,
            model_used=payload.model_used,
            inference_time_ms=payload.inference_time_ms,
            uncertainty_percent=payload.uncertainty_percent,
            reliability=payload.reliability,
            clinical_summary=payload.clinical_summary,
            recommendations=payload.recommendations,
        )

        generator = PDFReportGenerator(reports_dir=settings.REPORTS_DIR)
        pdf_bytes  = generator.generate(data)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="lungsight_report_{data.report_id}.pdf"'
            },
        )
    except Exception as exc:
        from loguru import logger
        logger.exception(f"Report generation error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(exc)}",
        ) from exc
