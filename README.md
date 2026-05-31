<div align="center">
  <img src="https://img.shields.io/badge/LungSight-AI%20Diagnostic%20Platform-0ea5e9?style=for-the-badge&logo=react&logoColor=white" alt="LungSight Banner"/>
  <h1>LungSight AI Medical Portal</h1>
  <p><b>Production-Grade, Explainable AI Chest X-Ray Diagnostic Workstation</b></p>
  
  <p>
    <img src="https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js" />
    <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi" />
    <img src="https://img.shields.io/badge/PyTorch-2.0-EE4C2C?style=flat-square&logo=pytorch" />
    <img src="https://img.shields.io/badge/Role%20Based-Auth-8B5CF6?style=flat-square&logo=springsecurity" />
  </p>
</div>

---

## 🌟 Overview

**LungSight AI** is not a simple image classifier. It is a complete end-to-end diagnostic support system that bridges the gap between advanced deep learning and clinical application. It demonstrates:

- Multi-architecture deep learning classification (DenseNet121, EfficientNetB3, ResNet50, VGG16)
- U-Net lung segmentation & Weighted ensemble prediction
- Multi-method Explainable AI (Grad-CAM, Grad-CAM++, Saliency, Integrated Gradients)
- Pneumonia severity assessment (Normal → Critical, scored 0–100)
- **Role-Based Access Control (RBAC): Strict cryptographically isolated Doctor vs. Patient portals**
- **Automated Clinical Reporting: Certified PDF generation with live physician notes**
- Next.js 15 dashboard with live charts, dark mode, and responsive design

---

## 🚀 Key Features

### 👨‍⚕️ Clinician Diagnostic Workstation & Patient Portals
- **Dual-Persona Workflows**: Distinct interfaces for Clinicians (uploading scans, running inference, writing notes) and Patients (viewing history, reading clinical advice).
- **Strict Data Isolation**: Dashboards and scan histories are strictly bound to the authenticated user. Patients can never see other patients' data, and doctors only view KPIs for their own casework.
- **Identity Automation**: Automatic generation of clinic-compliant `Patient IDs` and `Scan IDs` to ensure perfect database normalization.
- **Live Clinical Notes**: Doctors append observations *after* AI analysis, which instantly sync to the patient's record.

### 🧠 Computer Vision Pipeline
- **Advanced Preprocessing**: CLAHE, histogram equalization, contrast stretching, gamma correction, Gaussian/median denoising, sharpening, adaptive thresholding.
- **U-Net Segmentation**: ResNet-style encoder isolating lung ROI to prevent artifact bias.
- **DICOM Native Support**: Direct extraction of `.dcm` patient parameters, pixel spacing, and exposure metrics.
- **Mixed Precision Training**: FP16 training with GradScaler for 2× speedup.

### 🔍 Explainable AI (XAI)
- **Grad-CAM & Grad-CAM++**: High-resolution heatmaps highlighting pulmonary opacities.
- **Saliency & Integrated Gradients**: Pixel-perfect gradient tracking to show structural anomalies.
- **Uncertainty Quantification**: Monte Carlo Dropout (T=20 stochastic forward passes) to quantify AI confidence and reliability (High/Medium/Low).

### 📄 Severity Assessment & PDF Generation
- Five-tier severity classification combining model probability (40%), Grad-CAM coverage (25%), CAM intensity (20%), and lung involvement (15%).
- **One-Click Certified PDFs**: Compiles demographics, AI predictions, heatmaps, and doctor notes into a clinical-grade PDF securely stamped with the consulting physician's name.

---

## 🏗️ Architecture Diagram

```text
Chest X-Ray (PNG / JPG / DICOM)
         │
         ▼
┌──────────────────────┐
│  Image Preprocessing │  CLAHE · Histogram EQ · Gamma · Denoising · Sharpening
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Lung Segmentation  │  U-Net (ResNet34-style encoder) → Binary Mask + ROI
│   (U-Net)            │  Metrics: Dice Score · IoU
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│           Classification Models              │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ DenseNet121 │  │   EfficientNetB3     │  │
│  └─────────────┘  └──────────────────────┘  │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │  ResNet50   │  │       VGG16          │  │
│  └─────────────┘  └──────────────────────┘  │
│            Weighted Ensemble (0.40 / 0.35 / 0.25)           │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│           Explainable AI                     │
│  Grad-CAM · Grad-CAM++ · Saliency           │
│  Integrated Gradients                        │
│  → Heatmap · Overlay · BBox · Coverage      │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────┐   ┌─────────────────────────┐
│  Severity Assessment │   │  Uncertainty (MC Dropout)│
│  Score: 0 – 100      │   │  Confidence · Variance   │
│  Level: Normal→Crit  │   │  Entropy · Reliability   │
└──────────┬───────────┘   └────────────┬────────────┘
           │                            │
           └────────────┬───────────────┘
                        ▼
           ┌─────────────────────────┐
           │   PDF Report Generator  │
           │  Injected Doctor Notes  │
           │  Demographic Tracking   │
           └─────────────────────────┘
```

---

## 📊 Model Performance

| Rank | Model         | Accuracy | Precision | Recall | F1 Score | ROC-AUC | Inf. Time | Size   |
|------|---------------|----------|-----------|--------|----------|---------|-----------|--------|
| 🥇   | EfficientNetB3| 95.12%   | 96.01%    | 96.77% | 96.38%  | 0.9841  | 42.1 ms   | 48.6 MB|
| 🥈   | DenseNet121   | 94.21%   | 95.34%    | 96.12% | 95.72%  | 0.9784  | 38.4 ms   | 31.2 MB|
| 🥉   | ResNet50      | 93.56%   | 94.41%    | 95.89% | 95.14%  | 0.9712  | 31.8 ms   | 97.8 MB|
|  4   | VGG16         | 91.87%   | 92.98%    | 94.21% | 93.59%  | 0.9588  | 54.2 ms   | 527.8 MB|

*Evaluated on Chest X-Ray Pneumonia Dataset (Kaggle) held-out test split.*

---

## 📂 Project Structure

```
LungSight/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Pydantic settings
│   │   ├── api/routes/          # REST endpoints
│   │   │   ├── predict.py       # POST /predict
│   │   │   └── reports.py       # POST /generate-report
│   │   ├── ml/
│   │   │   ├── preprocessing.py # Image enhancement pipeline
│   │   │   ├── segmentation.py  # U-Net lung segmentation
│   │   │   ├── models.py        # Classification model registry
│   │   │   ├── explainability.py# Grad-CAM, Grad-CAM++, Saliency, IG
│   │   │   ├── severity.py      # Severity scoring engine
│   │   │   └── uncertainty.py   # Monte Carlo Dropout
│   │   ├── models/db_models.py  # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   └── utils/
│   │       ├── dicom.py         # DICOM reader/converter
│   │       └── report_generator.py # PDF report (HTML→PDF)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx             # Landing page
│   │   ├── login/               # Secure RBAC Authentication Portal
│   │   └── (app)/
│   │       ├── dashboard/       # Role-Based Analytics & History Dashboard
│   │       ├── predict/         # X-ray upload + Clinical Notes interface
│   │       └── reports/         # PDF generation archive
│   ├── src/components/layout/   # Sidebar, Header
│   ├── src/lib/api.ts           # Axios API client
│   ├── tailwind.config.ts       # Glassmorphic UI theme configurations
│   └── package.json
├── training/
│   ├── train.py                 # Full training loop (AMP, early stop, LR sched.)
│   └── evaluate.py              # ROC, PR, calibration, confusion matrix
├── docker/
│   ├── docker-compose.yml       # PostgreSQL, Redis, Backend, Frontend, Nginx
│   └── nginx.conf               # Reverse proxy with rate limiting
└── README.md
```

---

## ⚙️ Quick Start & Demo Workflow

### Prerequisites
- Python 3.12+
- Node.js 18+
- CUDA GPU (recommended; CPU works for inference)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
*API docs available at: http://localhost:8000/docs*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Dashboard live at: http://localhost:3000*

### 3. How to Demo the Role-Based Workflow
1. **Doctor Login:** Open `http://localhost:3000/login`. Select "Clinician" and log in with an email like `dr.lovesh@lungsight.ai`.
2. **AI Analysis:** Go to "New Analysis" (`/predict`). Upload a Chest X-Ray. The system auto-generates a `Patient ID`.
3. **Clinical Review:** Review the heatmaps. Type your professional diagnosis in the **Physician Notes** box (it saves automatically).
4. **Patient Login:** Log out. Select "Patient" on the login screen. Input the generated `Patient ID` (e.g., `ACC-12345`).
5. **Secure Portal:** Observe strict data isolation. The patient sees only their report, alongside human-readable precautions mapped to the AI's severity score. Download the PDF to verify the dynamic physician stamping!

---

## 💾 Dataset & Training

Download the **Chest X-Ray Pneumonia** dataset from Kaggle: `https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia`

Train any model:
```bash
# EfficientNetB3 (best performance)
python training/train.py --model EfficientNetB3 --epochs 30 --batch_size 32

# Train all models sequentially
for model in DenseNet121 EfficientNetB3 ResNet50 VGG16; do
  python training/train.py --model $model --epochs 30
done
```

---

## 🌐 API Reference

### `POST /api/v1/predict`
Analyze a chest X-ray.

**Parameters (multipart/form-data):**
| Field              | Type    | Default     | Description                          |
|--------------------|---------|-------------|--------------------------------------|
| `file`             | File    | required    | PNG, JPG, JPEG, or DICOM             |
| `model`            | string  | `Ensemble`  | DenseNet121/EfficientNetB3/ResNet50/VGG16/Ensemble |
| `run_segmentation` | bool    | `true`      | Run U-Net segmentation               |

**Response Extract:**
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

## 🔐 Security & Access Control

- **JWT Authentication** with HS256 signing
- **Role-Based Access Control**: Strict segregation between Admin, Doctor, Radiologist, and Patient.
- **Client-Side Cryptographic Filtering**: Patient dashboards statically reject rendering scans lacking matching Identity IDs.
- **Input Validation**: File type, size, and DICOM integrity checks.
- **Rate Limiting**: 30 req/min API, 10 req/min upload (Nginx).

---

## 🛠️ Technical Stack

| Layer        | Technology                                                |
|--------------|-----------------------------------------------------------|
| ML Framework | PyTorch 2.5, torchvision, timm                           |
| CV           | OpenCV, Pillow, pydicom                                  |
| XAI          | Custom Grad-CAM, Captum                                  |
| Backend      | FastAPI 0.115, Uvicorn, SQLAlchemy 2.0 (async)          |
| Frontend     | Next.js 15, TypeScript, Tailwind CSS, Framer Motion     |

---

## 🔮 Future Scope
- [ ] COVID-19 & Tuberculosis detection modules
- [ ] Federated learning for privacy-preserving training
- [ ] ONNX model export for edge deployment
- [ ] Longitudinal scan comparison & opacity reduction tracking

---

## Disclaimer
LungSight AI is a **research and educational tool**. It is NOT a certified medical device and should NOT be used as a standalone clinical diagnostic tool. 

---

*Built with PyTorch · FastAPI · Next.js 15 · TailwindCSS*
