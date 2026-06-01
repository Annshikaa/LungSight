<div align="center">

<br/>

<!-- ═══════════════════════════════════════════════════════════ -->
<!--           REPLACE THIS WITH YOUR BANNER IMAGE             -->
<!--   Recommended: 1280×400px, dark background, project logo  -->
<!-- ═══════════════════════════════════════════════════════════ -->
<!-- ![LungSight Banner](./docs/assets/banner.png) -->

# 🫁 LungSight AI

### *Explainable Deep Learning for Clinical Chest X-Ray Diagnostics*

<p>
  <a href="#"><img src="https://img.shields.io/badge/version-1.0.0-0ea5e9?style=flat-square" /></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-22c55e?style=flat-square" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.12+-3b82f6?style=flat-square&logo=python&logoColor=white" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Node.js-18+-84cc16?style=flat-square&logo=node.js&logoColor=white" /></a>
  <a href="#"><img src="https://img.shields.io/badge/PyTorch-2.5-EE4C2C?style=flat-square&logo=pytorch&logoColor=white" /></a>
  <a href="#"><img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js&logoColor=white" /></a>
</p>

<p>
  <a href="#-overview">Overview</a> ·
  <a href="#-key-features">Features</a> ·
  <a href="#-model-performance">Performance</a> ·
  <a href="#%EF%B8%8F-quick-start">Quick Start</a> ·
  <a href="#-api-reference">API</a> ·
  <a href="#-security">Security</a>
</p>

<br/>

</div>

---

## 📋 Overview

**LungSight AI** is a production-grade, end-to-end diagnostic support system that bridges advanced deep learning with real-world clinical workflows. It is not a simple classifier — it's a full workstation.

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--              REPLACE WITH YOUR DEMO SCREENSHOT               -->
<!--      Recommended: Full dashboard screenshot at 1440×900      -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- ![LungSight Dashboard](./docs/assets/dashboard-preview.png) -->

**What makes LungSight different:**

- **Multi-architecture ensemble** — DenseNet121, EfficientNetB3, ResNet50, and VGG16 vote together with weighted confidence to minimize individual model error.
- **Explainability-first** — Every prediction is backed by Grad-CAM, Grad-CAM++, Saliency Maps, and Integrated Gradients so clinicians can see *why* the model flagged a finding.
- **Uncertainty-aware** — Monte Carlo Dropout (T=20 forward passes) quantifies model confidence as High / Medium / Low — critical for safe clinical use.
- **Role-isolated portals** — Cryptographically enforced Doctor and Patient interfaces with strict data segregation.
- **One-click certified PDFs** — Clinical-grade reports stamped with physician name, AI predictions, heatmaps, and severity scoring.

> ⚠️ **Disclaimer:** LungSight AI is a **research and educational tool**. It is NOT a certified medical device and must NOT be used as a standalone clinical diagnostic tool.

---

## ✨ Key Features

### 👨‍⚕️ Clinician & Patient Portals

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--          REPLACE WITH SIDE-BY-SIDE PORTAL SCREENSHOTS        -->
<!--      Left: Doctor dashboard  |  Right: Patient portal        -->
<!-- ═══════════════════════════════════════════════════════════════ -->
<!-- ![Role-Based Portals](./docs/assets/rbac-portals.png) -->

| Feature | Description |
|---|---|
| **Dual-Persona Workflows** | Distinct interfaces for Clinicians (upload, infer, annotate) and Patients (view history, read advice) |
| **Strict Data Isolation** | Scan histories are cryptographically bound to the authenticated user — patients can never access others' records |
| **Identity Automation** | Auto-generated clinic-compliant `Patient IDs` and `Scan IDs` for perfect database normalization |
| **Live Clinical Notes** | Doctors append observations post-AI-analysis; notes sync instantly to the patient record |

---

### 🧠 Computer Vision Pipeline

<!-- ═══════════════════════════════════════════════════════════════════ -->
<!--            REPLACE WITH PREPROCESSING PIPELINE VISUAL           -->
<!--   Suggested: side-by-side of raw vs CLAHE vs segmented X-ray   -->
<!-- ═════════════════════════════════════════════════════════════════ -->
<!-- ![CV Pipeline](./docs/assets/cv-pipeline.png) -->

**Advanced Preprocessing**
> CLAHE · Histogram Equalization · Contrast Stretching · Gamma Correction · Gaussian/Median Denoising · Sharpening · Adaptive Thresholding

**U-Net Segmentation**
> ResNet-style encoder isolates the lung ROI, preventing background artifacts from biasing classification. Evaluated on Dice Score and IoU.

**DICOM Native Support**
> Direct extraction of `.dcm` patient parameters, pixel spacing, and exposure metrics — no manual conversion required.

**Mixed Precision Training**
> FP16 training with `GradScaler` for ~2× training speedup without accuracy loss.

---

### 🔍 Explainable AI (XAI)

<!-- ═══════════════════════════════════════════════════════════════════ -->
<!--           REPLACE WITH XAI HEATMAP COMPARISON GRID            -->
<!--  Suggested: 2×2 grid — Grad-CAM, Grad-CAM++, Saliency, IG    -->
<!-- ═════════════════════════════════════════════════════════════════ -->
<!-- ![XAI Heatmaps](./docs/assets/xai-heatmaps.png) -->

| Method | What It Shows |
|---|---|
| **Grad-CAM** | Class-discriminative coarse activation maps over lung regions |
| **Grad-CAM++** | Higher-resolution heatmaps highlighting pulmonary opacities |
| **Saliency Maps** | Per-pixel gradient magnitude tracking structural anomalies |
| **Integrated Gradients** | Attribution along gradient path from baseline to input |
| **MC Dropout (T=20)** | Stochastic confidence estimation: variance, entropy, reliability |

---

### 📊 Severity Assessment

A **five-tier severity engine** combines four signals into a 0–100 score:

```
Severity Score = (Model Probability × 0.40)
               + (Grad-CAM Coverage  × 0.25)
               + (CAM Intensity      × 0.20)
               + (Lung Involvement   × 0.15)
```

| Score Range | Level | Colour |
|---|---|---|
| 0 – 20 | Normal | 🟢 Green |
| 21 – 40 | Mild | 🟡 Yellow |
| 41 – 60 | Moderate | 🟠 Orange |
| 61 – 80 | Severe | 🔴 Red |
| 81 – 100 | Critical | 🟣 Purple |

---

### 📄 Automated PDF Reports

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--         REPLACE WITH SAMPLE PDF REPORT SCREENSHOT            -->
<!--    Suggested: cropped preview showing layout + heatmap       -->
<!-- ═════════════════════════════════════════════════════════════ -->
<!-- ![PDF Report Sample](./docs/assets/pdf-report-sample.png) -->

One-click certified PDF generation includes:
- Patient demographics and Scan ID
- AI predictions with confidence scores
- Grad-CAM heatmap overlays
- Five-tier severity classification
- Physician notes, dynamically stamped with the consulting doctor's name

---

## 🏗️ System Architecture

```
Chest X-Ray  (PNG · JPG · DICOM)
       │
       ▼
┌────────────────────────┐
│   Image Preprocessing  │  CLAHE · Histogram EQ · Gamma · Denoising · Sharpening
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│   Lung Segmentation    │  U-Net (ResNet34-style encoder)
│   (U-Net)              │  → Binary Mask + ROI Crop
│                        │  Metrics: Dice Score · IoU
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────────────────────────────────┐
│               Classification Ensemble              │
│                                                    │
│   ┌─────────────┐        ┌──────────────────────┐  │
│   │ DenseNet121 │        │   EfficientNetB3     │  │
│   └─────────────┘        └──────────────────────┘  │
│   ┌─────────────┐        ┌──────────────────────┐  │
│   │  ResNet50   │        │       VGG16          │  │
│   └─────────────┘        └──────────────────────┘  │
│                                                    │
│         Weighted Ensemble  (0.40 / 0.35 / 0.25)   │
└──────────┬─────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────────┐
│                 Explainable AI                     │
│   Grad-CAM · Grad-CAM++ · Saliency                │
│   Integrated Gradients                             │
│   → Heatmap · Overlay · BBox · Coverage %         │
└──────────┬─────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐    ┌───────────────────────────┐
│  Severity Assessment │    │  Uncertainty (MC Dropout)  │
│  Score: 0 – 100      │    │  Confidence · Variance     │
│  Level: Normal→Crit  │    │  Entropy · Reliability     │
└──────────┬───────────┘    └─────────────┬─────────────┘
           │                              │
           └──────────────┬───────────────┘
                          ▼
             ┌────────────────────────┐
             │   PDF Report Generator  │
             │   Physician Notes       │
             │   Demographic Tracking  │
             └────────────────────────┘
```

---

## 📊 Model Performance

*Evaluated on the [Chest X-Ray Pneumonia Dataset](https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia) (Kaggle) held-out test split.*

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--       OPTIONAL: REPLACE WITH ROC CURVE COMPARISON PLOT       -->
<!--           Suggested: all 4 models overlaid on one chart      -->
<!-- ═════════════════════════════════════════════════════════════ -->
<!-- ![ROC Curves](./docs/assets/roc-curves.png) -->

| Rank | Model | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Inf. Time | Size |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 🥇 | **EfficientNetB3** | 95.12% | 96.01% | 96.77% | 96.38% | 0.9841 | 42.1 ms | 48.6 MB |
| 🥈 | **DenseNet121** | 94.21% | 95.34% | 96.12% | 95.72% | 0.9784 | 38.4 ms | 31.2 MB |
| 🥉 | **ResNet50** | 93.56% | 94.41% | 95.89% | 95.14% | 0.9712 | 31.8 ms | 97.8 MB |
| 4 | **VGG16** | 91.87% | 92.98% | 94.21% | 93.59% | 0.9588 | 54.2 ms | 527.8 MB |

---

## 📂 Project Structure

```
LungSight/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI application entry point
│   │   ├── config.py                 # Pydantic settings & environment config
│   │   ├── api/routes/
│   │   │   ├── predict.py            # POST /predict
│   │   │   └── reports.py            # POST /generate-report
│   │   ├── ml/
│   │   │   ├── preprocessing.py      # Image enhancement pipeline
│   │   │   ├── segmentation.py       # U-Net lung segmentation
│   │   │   ├── models.py             # Classification model registry
│   │   │   ├── explainability.py     # Grad-CAM, Grad-CAM++, Saliency, IG
│   │   │   ├── severity.py           # Severity scoring engine
│   │   │   └── uncertainty.py        # Monte Carlo Dropout
│   │   ├── models/db_models.py       # SQLAlchemy ORM models
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   └── utils/
│   │       ├── dicom.py              # DICOM reader/converter
│   │       └── report_generator.py   # PDF report (HTML → PDF)
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                  # Landing page
│   │   ├── login/                    # RBAC Authentication portal
│   │   └── (app)/
│   │       ├── dashboard/            # Role-based analytics & history
│   │       ├── predict/              # X-ray upload + clinical notes
│   │       └── reports/              # PDF archive
│   ├── src/components/layout/        # Sidebar, Header
│   ├── src/lib/api.ts                # Axios API client
│   ├── tailwind.config.ts            # Glassmorphic UI theme
│   └── package.json
│
├── training/
│   ├── train.py                      # Full training loop (AMP, early stop, LR sched.)
│   └── evaluate.py                   # ROC, PR, calibration, confusion matrix
│
├── docker/
│   ├── docker-compose.yml            # PostgreSQL · Redis · Backend · Frontend · Nginx
│   └── nginx.conf                    # Reverse proxy with rate limiting
│
└── docs/
    └── assets/                       # ← Place your screenshots here
        ├── banner.png
        ├── dashboard-preview.png
        ├── rbac-portals.png
        ├── cv-pipeline.png
        ├── xai-heatmaps.png
        ├── pdf-report-sample.png
        └── roc-curves.png
```

---

## ⚙️ Quick Start

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.12+ |
| Node.js | 18+ |
| CUDA GPU | Recommended (CPU works for inference) |

### 1 · Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

> Interactive API docs → [http://localhost:8000/docs](http://localhost:8000/docs)

### 2 · Frontend

```bash
cd frontend
npm install
npm run dev
```

> Dashboard → [http://localhost:3000](http://localhost:3000)

### 3 · Docker (Full Stack)

```bash
docker-compose -f docker/docker-compose.yml up --build
```

This spins up PostgreSQL, Redis, the FastAPI backend, Next.js frontend, and Nginx as a reverse proxy.

---

## 🎬 Demo Workflow

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--            OPTIONAL: REPLACE WITH A GIF WALKTHROUGH          -->
<!--   Suggested: screen recording of the full login → predict    -->
<!--              → notes → patient portal workflow               -->
<!-- ═════════════════════════════════════════════════════════════ -->
<!-- ![Demo Walkthrough](./docs/assets/demo.gif) -->

Follow these steps to demo the full role-based workflow:

1. **Doctor Login** — Open `http://localhost:3000/login`. Select **Clinician** and log in with `dr.lovesh@lungsight.ai`.
2. **AI Analysis** — Navigate to **New Analysis** (`/predict`). Upload a chest X-ray. The system auto-generates a `Patient ID`.
3. **Clinical Review** — Inspect the heatmaps. Enter your professional diagnosis in the **Physician Notes** box (auto-saved).
4. **Patient Login** — Log out. Select **Patient**. Enter the generated `Patient ID` (e.g., `ACC-12345`).
5. **Secure Portal** — Verify strict data isolation. The patient sees only their report and severity-mapped precautions. Download the PDF to confirm dynamic physician stamping.

---

## 💾 Dataset & Training

Download the dataset from Kaggle:

```
https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia
```

**Train a single model:**
```bash
python training/train.py --model EfficientNetB3 --epochs 30 --batch_size 32
```

**Train all models sequentially:**
```bash
for model in DenseNet121 EfficientNetB3 ResNet50 VGG16; do
  python training/train.py --model $model --epochs 30
done
```

---

## 🌐 API Reference

### `POST /api/v1/predict`

Analyze a chest X-ray image.

**Parameters — `multipart/form-data`**

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | File | *required* | PNG, JPG, JPEG, or DICOM |
| `model` | string | `Ensemble` | `DenseNet121` · `EfficientNetB3` · `ResNet50` · `VGG16` · `Ensemble` |
| `run_segmentation` | bool | `true` | Run U-Net segmentation before classification |

**Response (abridged)**

```json
{
  "label": "PNEUMONIA",
  "confidence": 0.962,
  "severity": {
    "score": 63.2,
    "level": "Moderate",
    "recommendations": ["Prompt clinical evaluation required"]
  },
  "uncertainty": {
    "reliability": "High"
  },
  "heatmaps": {
    "gradcam": { "heatmap_b64": "..." }
  }
}
```

---

## 🔐 Security

| Layer | Implementation |
|---|---|
| **Authentication** | JWT with HS256 signing |
| **Access Control** | RBAC — Admin, Doctor, Radiologist, Patient |
| **Data Isolation** | Client-side cryptographic filtering; dashboards reject mismatched Identity IDs |
| **Input Validation** | File type, size, and DICOM integrity checks |
| **Rate Limiting** | 30 req/min API · 10 req/min upload (Nginx) |

---

## 🛠️ Technical Stack

| Layer | Technology |
|---|---|
| **ML Framework** | PyTorch 2.5 · torchvision · timm |
| **Computer Vision** | OpenCV · Pillow · pydicom |
| **XAI** | Custom Grad-CAM · Captum |
| **Backend** | FastAPI 0.115 · Uvicorn · SQLAlchemy 2.0 (async) |
| **Frontend** | Next.js 15 · TypeScript · Tailwind CSS · Framer Motion |
| **Infrastructure** | PostgreSQL · Redis · Nginx · Docker |

---

## 🔮 Roadmap

- [ ] COVID-19 & Tuberculosis detection modules
- [ ] Federated learning for privacy-preserving multi-site training
- [ ] ONNX export for edge deployment
- [ ] Longitudinal scan comparison & opacity reduction tracking
- [ ] FHIR-compliant data exchange

---

## 🤝 Contributing

Contributions are welcome! Please open an issue to discuss changes before submitting a pull request. Make sure tests pass and code follows the existing style conventions.

---

## 📜 License

This project is licensed under the MIT License — see [LICENSE](./LICENSE) for details.

---

<div align="center">
  <br/>
  <sub>Built with ❤️ using PyTorch · FastAPI · Next.js 15 · TailwindCSS</sub>
  <br/><br/>
  <sub>⚠️ Not a certified medical device. For research and educational use only.</sub>
  <br/><br/>
</div>