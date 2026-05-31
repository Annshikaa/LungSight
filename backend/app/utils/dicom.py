"""
DICOM support module for LungSight AI.
Handles DICOM file reading, metadata extraction, window-level adjustment,
pixel normalisation, and conversion to PNG/numpy.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
from PIL import Image


# ──────────────────────────────────────────────────────────────────────────────
# Metadata container
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class DICOMMetadata:
    patient_name:   Optional[str] = None
    patient_id:     Optional[str] = None
    patient_age:    Optional[str] = None
    patient_sex:    Optional[str] = None
    patient_dob:    Optional[str] = None
    study_date:     Optional[str] = None
    study_time:     Optional[str] = None
    modality:       Optional[str] = None
    body_part:      Optional[str] = None
    institution:    Optional[str] = None
    manufacturer:   Optional[str] = None
    rows:           Optional[int] = None
    columns:        Optional[int] = None
    pixel_spacing:  Optional[str] = None
    window_center:  Optional[float] = None
    window_width:   Optional[float] = None
    bits_allocated: Optional[int] = None
    raw:            Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# DICOM Reader
# ──────────────────────────────────────────────────────────────────────────────

class DICOMReader:
    """Read DICOM files, extract metadata, and convert to uint8 RGB arrays."""

    # ------------------------------------------------------------------
    @staticmethod
    def _try_import_pydicom():
        try:
            import pydicom
            return pydicom
        except ImportError as exc:
            raise RuntimeError(
                "pydicom is required to process DICOM files. "
                "Install it with: pip install pydicom"
            ) from exc

    # ------------------------------------------------------------------
    @classmethod
    def read(cls, source) -> tuple[np.ndarray, DICOMMetadata]:
        """
        Read a DICOM file.
        source: file path (str | Path) or bytes.
        Returns (uint8 H×W×3 RGB array, DICOMMetadata).
        """
        pydicom = cls._try_import_pydicom()

        if isinstance(source, (bytes, bytearray)):
            ds = pydicom.dcmread(io.BytesIO(source))
        else:
            ds = pydicom.dcmread(str(source))

        meta = cls._extract_metadata(ds)
        pixels = cls._to_uint8_rgb(ds, meta)
        return pixels, meta

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_metadata(ds) -> DICOMMetadata:
        def _get(tag: str, default=None):
            try:
                val = getattr(ds, tag, default)
                return str(val) if val is not None else default
            except Exception:
                return default

        raw: Dict[str, Any] = {}
        for elem in ds:
            try:
                if elem.VR not in ("SQ", "OB", "OW", "OF", "UN"):
                    raw[str(elem.keyword)] = str(elem.value)
            except Exception:
                pass

        wc = None
        ww = None
        try:
            wc_val = ds.WindowCenter
            ww_val = ds.WindowWidth
            wc = float(wc_val[0]) if hasattr(wc_val, "__iter__") else float(wc_val)
            ww = float(ww_val[0]) if hasattr(ww_val, "__iter__") else float(ww_val)
        except Exception:
            pass

        return DICOMMetadata(
            patient_name=_get("PatientName"),
            patient_id=_get("PatientID"),
            patient_age=_get("PatientAge"),
            patient_sex=_get("PatientSex"),
            patient_dob=_get("PatientBirthDate"),
            study_date=_get("StudyDate"),
            study_time=_get("StudyTime"),
            modality=_get("Modality"),
            body_part=_get("BodyPartExamined"),
            institution=_get("InstitutionName"),
            manufacturer=_get("Manufacturer"),
            rows=int(_get("Rows") or 0) or None,
            columns=int(_get("Columns") or 0) or None,
            pixel_spacing=_get("PixelSpacing"),
            window_center=wc,
            window_width=ww,
            bits_allocated=int(_get("BitsAllocated") or 0) or None,
            raw=raw,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _apply_window(
        pixels: np.ndarray,
        window_center: Optional[float],
        window_width: Optional[float],
    ) -> np.ndarray:
        """Apply DICOM window-level adjustment."""
        pixels = pixels.astype(np.float32)
        if window_center is not None and window_width is not None:
            lo = window_center - window_width / 2
            hi = window_center + window_width / 2
        else:
            lo, hi = float(pixels.min()), float(pixels.max())

        pixels = np.clip((pixels - lo) / (hi - lo + 1e-7), 0, 1)
        return (pixels * 255).astype(np.uint8)

    # ------------------------------------------------------------------
    @classmethod
    def _to_uint8_rgb(cls, ds, meta: DICOMMetadata) -> np.ndarray:
        """Convert DICOM pixel array to uint8 H×W×3 RGB."""
        try:
            pixels = ds.pixel_array
        except Exception as exc:
            raise ValueError(f"Cannot read DICOM pixel data: {exc}") from exc

        # Handle multi-frame (use first frame)
        if pixels.ndim == 3 and pixels.shape[0] < 10:
            pixels = pixels[0]
        elif pixels.ndim == 3 and pixels.shape[-1] == 3:
            pass  # already RGB

        if pixels.ndim == 2:
            pixels = cls._apply_window(pixels, meta.window_center, meta.window_width)
            pixels = np.stack([pixels, pixels, pixels], axis=-1)
        else:
            lo, hi = pixels.min(), pixels.max()
            pixels = ((pixels.astype(np.float32) - lo) / (hi - lo + 1e-7) * 255).astype(np.uint8)

        # Photometric interpretation (some DICOMs store inverted)
        try:
            if "MONOCHROME1" in str(getattr(ds, "PhotometricInterpretation", "")):
                pixels = 255 - pixels
        except Exception:
            pass

        return pixels

    # ------------------------------------------------------------------
    @classmethod
    def to_pil(cls, source) -> tuple[Image.Image, DICOMMetadata]:
        pixels, meta = cls.read(source)
        return Image.fromarray(pixels), meta

    # ------------------------------------------------------------------
    @classmethod
    def to_png_bytes(cls, source) -> tuple[bytes, DICOMMetadata]:
        pil, meta = cls.to_pil(source)
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        return buf.getvalue(), meta


def is_dicom(filename: str) -> bool:
    return Path(filename).suffix.lower() in {".dcm", ".dicom", ""}
