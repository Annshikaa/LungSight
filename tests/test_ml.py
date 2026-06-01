"""
LungSight AI — ML Unit Tests
"""
import io
import numpy as np
from PIL import Image


def _make_rgb(h=224, w=224) -> np.ndarray:
    return np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)


def _make_bytes(h=224, w=224) -> bytes:
    arr = _make_rgb(h, w)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


# ── Preprocessing ──────────────────────────────────────────────────────────────

def test_preprocessor_output_shape():
    from app.ml.preprocessing import XRayPreprocessor
    pp = XRayPreprocessor()
    result = pp.process(_make_bytes())
    assert result.original.shape == (224, 224, 3)
    assert result.enhanced.shape == (224, 224, 3)
    assert result.tensor_input.shape == (1, 3, 224, 224)
    assert result.tensor_input.dtype == np.float32


def test_preprocessor_stages():
    from app.ml.preprocessing import XRayPreprocessor
    pp = XRayPreprocessor()
    result = pp.process(_make_bytes())
    assert "original" in result.intermediate
    assert "enhanced" in result.intermediate


def test_clahe():
    from app.ml.preprocessing import apply_clahe
    img = _make_rgb()
    out = apply_clahe(img)
    assert out.shape == img.shape
    assert out.dtype == np.uint8


def test_contrast_stretching():
    from app.ml.preprocessing import apply_contrast_stretching
    img = _make_rgb()
    out = apply_contrast_stretching(img)
    assert out.shape == img.shape


# ── Segmentation ────────────────────────────────────────────────────────────────

def test_segmentation_engine():
    from app.ml.segmentation import LungSegmentationEngine
    engine = LungSegmentationEngine(weights_path=None, device="cpu")
    img = _make_rgb()
    result = engine.segment(img)
    assert result.mask.shape == img.shape[:2]
    assert result.overlay.shape == img.shape
    assert result.roi.shape == img.shape
    assert 0.0 <= result.lung_area_percentage <= 100.0


def test_dice_iou():
    from app.ml.segmentation import dice_score, iou_score
    pred   = np.ones((100, 100), dtype=np.uint8) * 255
    target = np.ones((100, 100), dtype=np.uint8) * 255
    assert abs(dice_score(pred, target) - 1.0) < 1e-5
    assert abs(iou_score(pred, target) - 1.0) < 1e-5

    empty  = np.zeros((100, 100), dtype=np.uint8)
    assert dice_score(empty, target) < 0.01


# ── Classification models ────────────────────────────────────────────────────────

def test_model_registry():
    import tempfile
    from app.ml.models import ClassificationModelRegistry
    with tempfile.TemporaryDirectory() as tmp:
        reg = ClassificationModelRegistry(weights_dir=tmp, device="cpu")
        result = reg.predict(
            np.zeros((1, 3, 224, 224), dtype=np.float32),
            model_name="DenseNet121",
        )
        assert result.label in ("NORMAL", "PNEUMONIA")
        assert 0.0 <= result.confidence <= 1.0
        assert result.inference_time_ms >= 0


# ── Severity ────────────────────────────────────────────────────────────────────

def test_severity_normal():
    from app.ml.severity import SeverityAssessor
    a = SeverityAssessor()
    r = a.assess(pneumonia_probability=0.05, is_pneumonia=False)
    assert r.level == "Normal"
    assert r.score <= 10


def test_severity_critical():
    from app.ml.severity import SeverityAssessor
    a = SeverityAssessor()
    r = a.assess(
        pneumonia_probability=0.98,
        activation_coverage=0.90,
        gradcam_intensity=0.88,
        lung_involvement=0.85,
        is_pneumonia=True,
    )
    assert r.level in ("Severe", "Critical")
    assert r.score >= 60


# ── Uncertainty ────────────────────────────────────────────────────────────────

def test_uncertainty_estimator():
    import tempfile
    import torch
    from app.ml.models import ClassificationModelRegistry
    from app.ml.uncertainty import MCDropoutEstimator
    device = torch.device("cpu")
    with tempfile.TemporaryDirectory() as tmp:
        reg = ClassificationModelRegistry(weights_dir=tmp, device="cpu")
        model = reg.get_raw_model("DenseNet121")
        mc = MCDropoutEstimator(model, device, n_samples=5)
        result = mc.estimate(np.zeros((1, 3, 224, 224), dtype=np.float32))
        assert 0.0 <= result.confidence_percent <= 100.0
        assert 0.0 <= result.uncertainty_percent <= 100.0
        assert result.reliability in ("High", "Medium", "Low")
