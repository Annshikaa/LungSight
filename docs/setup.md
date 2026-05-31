# LungSight AI — Setup Guide

## Development Setup

### 1. Clone repository
```bash
git clone https://github.com/yourusername/lungsight-ai.git
cd lungsight-ai
```

### 2. Environment configuration
```bash
cp .env.example .env
# Edit .env and set:
# - DATABASE_URL (your PostgreSQL connection)
# - SECRET_KEY and JWT_SECRET_KEY (strong random strings)
# - DEVICE (cuda or cpu)
```

### 3. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start in development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit:
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Frontend

```bash
cd frontend
npm install --legacy-peer-deps

# Development server
npm run dev

# Production build
npm run build && npm start
```

Visit: http://localhost:3000

---

## Training Setup

### Download dataset
```bash
pip install kaggle
kaggle datasets download -d paultimothymooney/chest-xray-pneumonia
unzip chest-xray-pneumonia.zip -d data/
```

### Train a model
```bash
python training/train.py \
  --model EfficientNetB3 \
  --data_dir ./data/chest_xray \
  --epochs 30 \
  --batch_size 32 \
  --lr 0.0001 \
  --output_dir ./backend/models/weights
```

### Evaluate
```bash
python training/evaluate.py \
  --model EfficientNetB3 \
  --data_dir ./data/chest_xray \
  --weights_dir ./backend/models/weights \
  --output_dir ./research/results
```

### TensorBoard
```bash
tensorboard --logdir tb_logs --port 6006
```

---

## Docker Production Deployment

```bash
# Set environment variables
export SECRET_KEY="your-very-long-random-secret-key"
export JWT_SECRET_KEY="another-very-long-random-key"

# Build and run
cd docker
docker compose up --build -d

# View logs
docker compose logs -f

# Scale backend
docker compose up --scale backend=2

# Stop
docker compose down
```

### SSL Setup (optional)
Place SSL certificates in `docker/ssl/`:
- `docker/ssl/cert.pem`
- `docker/ssl/key.pem`

Update `nginx.conf` to enable HTTPS server block.

---

## Running Tests

```bash
# Backend tests
cd backend
pytest ../tests/ -v --cov=app --cov-report=html

# Frontend type check
cd frontend
npm run type-check

# Frontend lint
npm run lint
```
