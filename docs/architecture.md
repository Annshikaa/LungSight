# LungSight AI — Architecture Documentation

## System Architecture

```
                    ┌──────────────────────────────────────┐
                    │         User / Radiologist           │
                    └────────────────┬─────────────────────┘
                                     │  HTTPS
                    ┌────────────────▼─────────────────────┐
                    │        Nginx Reverse Proxy           │
                    │   Rate Limiting · SSL Termination    │
                    └──────┬────────────────────┬──────────┘
                           │                    │
               ┌───────────▼──────┐  ┌──────────▼──────────┐
               │  Next.js 15      │  │    FastAPI Backend   │
               │  Frontend        │  │    (8000)           │
               │  (3000)          │  │                     │
               └──────────────────┘  └──────────┬──────────┘
                                                 │
                    ┌────────────────────────────┼────────────┐
                    │                            │            │
         ┌──────────▼──────┐        ┌───────────▼──┐   ┌────▼──────┐
         │   PostgreSQL     │        │    Redis      │   │  ML Core  │
         │   16 (async)     │        │    Cache      │   │ PyTorch   │
         └──────────────────┘        └──────────────┘   └───────────┘
```

## ML Pipeline

### Stage 1: Preprocessing
1. Load image (PNG/JPG/DICOM → RGB numpy array)
2. Resize to 224×224 (Lanczos interpolation)
3. Contrast stretching (2nd–98th percentile)
4. CLAHE (clip limit 3.0, 8×8 tile grid)
5. Gamma correction (γ=1.15)
6. Median denoising (3×3 kernel)
7. Unsharp masking / sharpening
8. ImageNet normalization (mean/std)
9. Channel-first tensor (1×3×224×224)

### Stage 2: Segmentation (U-Net)
- Lightweight U-Net: 4 encoder blocks (64→128→256→512→1024)
- Skip connections
- Sigmoid output → binary threshold (0.5)
- Morphological close+open (15×15 elliptic kernel)
- Otsu fallback if mask is degenerate
- Metrics: Dice, IoU

### Stage 3: Classification
Each model uses:
- Pretrained ImageNet backbone (frozen/fine-tuned)
- Custom head: Dropout(0.5) → FC(512) → BN → ReLU → Dropout(0.25) → FC(2)
- Cross-entropy with label smoothing (0.1) and class weights
- AdamW optimizer + CosineAnnealingLR scheduler
- Mixed-precision training (AMP)

Ensemble: weighted-average softmax probabilities
- DenseNet121:    0.40
- EfficientNetB3: 0.35
- ResNet50:       0.25

### Stage 4: Explainability
**Grad-CAM:**
```
weights = global_avg_pool(∂score/∂A^k)
CAM = ReLU(Σ_k weights_k · A^k)
```

**Grad-CAM++:**
```
α = (∂²score/∂A²) / (2·∂²score/∂A² + A·∂³score/∂A³)
weights = Σ_i,j (α · ReLU(∂score/∂A))
```

**Integrated Gradients:**
```
IG = (x - x') · (1/T) Σ_{t=0}^{T} ∂F(x'+t(x-x'))/∂x
```

### Stage 5: Severity Assessment
```
raw_score = 0.40·P(pneumonia)
          + 0.25·activation_coverage
          + 0.20·mean_cam_intensity
          + 0.15·lung_involvement

score = clip(raw_score × 100, 0, 100)
```

Thresholds: Normal [0,10) · Mild [10,35) · Moderate [35,60) · Severe [60,80) · Critical [80,100]

### Stage 6: Uncertainty
Monte Carlo Dropout:
```
{p_t}_{t=1}^{T} = T stochastic forward passes with dropout active
mean = (1/T) Σ p_t
var  = (1/T) Σ (p_t - mean)²
H    = -Σ_c p̄_c · log₂(p̄_c)   (predictive entropy)
```

## Database Schema
- `users` — JWT-authenticated users with role-based permissions
- `patients` — Patient demographics (linked to scans)
- `xray_scans` — Uploaded image metadata and storage paths
- `predictions` — Model outputs: label, confidence, severity, uncertainty
- `segmentations` — U-Net mask results and metrics
- `heatmaps` — XAI outputs for each prediction
- `reports` — Generated PDF report metadata
- `model_benchmarks` — Historical benchmark results
- `audit_logs` — Action audit trail for compliance
