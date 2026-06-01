"""
LungSight AI — API Integration Tests
"""
import io
import pytest
import numpy as np
from PIL import Image
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def sample_xray_bytes():
    """Generate a synthetic 224x224 grayscale image as PNG bytes."""
    arr = np.random.randint(0, 255, (224, 224), dtype=np.uint8)
    img = Image.fromarray(arr, mode="L").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_health():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["service"] == "LungSight AI"


@pytest.mark.asyncio
async def test_analytics():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/analytics")
    assert r.status_code == 200
    data = r.json()
    assert "total_scans" in data
    assert "pneumonia_cases" in data
    assert data["total_scans"] > 0


@pytest.mark.asyncio
async def test_benchmark():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/benchmark")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 3
    model_names = [d["model_name"] for d in data]
    assert "DenseNet121" in model_names


@pytest.mark.asyncio
async def test_leaderboard():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/benchmark/leaderboard")
    assert r.status_code == 200
    data = r.json()
    assert data[0]["rank"] == 1
    # Sorted by ROC-AUC
    roc_aucs = [d["roc_auc"] for d in data]
    assert roc_aucs == sorted(roc_aucs, reverse=True)


@pytest.mark.asyncio
async def test_models_list():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/models")
    assert r.status_code == 200
    data = r.json()
    assert "models" in data
    names = [m["name"] for m in data["models"]]
    assert "Ensemble" in names


@pytest.mark.asyncio
async def test_predict_invalid_file():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/predict",
            files={"file": ("test.txt", b"not an image", "text/plain")},
            data={"model": "DenseNet121"},
        )
    assert r.status_code in (415, 500)


@pytest.mark.asyncio
async def test_predict_empty_file():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/predict",
            files={"file": ("empty.png", b"", "image/png")},
            data={"model": "DenseNet121"},
        )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_predict_valid_image(sample_xray_bytes):
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", timeout=60.0
    ) as client:
        r = await client.post(
            "/api/v1/predict",
            files={"file": ("xray.png", sample_xray_bytes, "image/png")},
            data={
                "model": "DenseNet121",
                "run_segmentation": "true",
                "xai_methods": "gradcam,saliency",
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["label"] in ("NORMAL", "PNEUMONIA")
    assert 0.0 <= data["confidence"] <= 1.0
    assert "severity" in data
    assert "uncertainty" in data
    assert "heatmaps" in data
    assert len(data["heatmaps"]) > 0
    assert data["original_image_b64"]
    assert data["enhanced_image_b64"]
