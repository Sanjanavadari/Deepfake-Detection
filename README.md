# DeepGuard - Deepfake Detection System

A complete end-to-end Deepfake Detection web application built with a FastAPI backend (PyTorch) and a React + TailwindCSS frontend. It uses a Hybrid CNN + Transformer (EfficientNetV2) architecture to identify visual manipulation artifacts.

## Folder Structure

- `src/` - Contains the PyTorch model definition (`model.py`).
- `backend/` - FastAPI backend application.
- `frontend/` - React frontend application.
- `real/` and `fake/` - Dataset directories for training (local only).
- `test_model.py` - Script to verify the model architecture.

## Features

- **Inference**: Upload an image or video to the `/` route to get a real-time prediction.
- **Explainability (Grad-CAM)**: View the regions the model focused on to make its prediction for images.
- **Dashboard**: Navigate to `/dashboard` to view model evaluation metrics, trigger a live training run via SSE streaming, and view the history of all past predictions.

## Model Weights

The backend loads `backend/weights/best_model.pth` if present. **If this file is missing**, the app falls back to a timm pretrained EfficientNetV2 backbone with a randomly initialized classifier head. **Predictions will not be meaningful until a trained `best_model.pth` is added** to `backend/weights/`.

To use a trained model locally or in production, place your checkpoint at:

```
backend/weights/best_model.pth
```

## Local Development

### 1. Backend Setup

Open a terminal and navigate to the project root:

```bash
# Optional: Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install backend dependencies (CPU-only PyTorch)
pip install -r backend/requirements.txt
```

Copy the example env file and adjust if needed:

```bash
cp backend/.env.example backend/.env
```

### 2. Frontend Setup

Open another terminal and navigate to the `frontend/` directory:

```bash
cd frontend
npm install
cp .env.example .env
```

### Running the Application

**Start the Backend (FastAPI):**

```bash
# From project root
python backend/main.py
```

The API runs on `http://localhost:8000`. It auto-creates the SQLite database for prediction history.

**Start the Frontend (React + Vite):**

```bash
# From frontend/
npm run dev
```

The UI runs on `http://localhost:5173`.

### Training (Local Only)

Place real images in `real/` and fake images in `fake/`, then start training from the Dashboard. Training requires significant compute and labeled data; it is intended for local development, not the deployed Render environment.

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Local Default |
|----------|-------------|---------------|
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:5173` |
| `DATABASE_URL` | SQLite database file path | `backend/predictions.db` |
| `MODEL_PATH` | Path to `best_model.pth` | `backend/weights/best_model.pth` |
| `LOG_LEVEL` | Python log level | `INFO` |
| `PORT` | Uvicorn port (Render injects this) | `8000` |

### Frontend (`frontend/.env`)

| Variable | Description | Local Default |
|----------|-------------|---------------|
| `VITE_API_BASE_URL` | Backend API URL (no trailing slash) | `http://localhost:8000` |

## Deploy Backend to Render

1. Push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com), create a **New Web Service** and connect your repo.
3. Alternatively, use the included `render.yaml` Blueprint.
4. Configure the service:
   - **Runtime**: Docker
   - **Dockerfile path**: `backend/Dockerfile`
   - **Docker context**: `.` (repository root)
   - **Health check path**: `/health`
5. Set environment variables:
   - `ALLOWED_ORIGINS` → your Vercel frontend URL, e.g. `https://your-app.vercel.app`
   - `DATABASE_URL` → `/tmp/predictions.db` (ephemeral; see note below)
   - `LOG_LEVEL` → `INFO`
6. Deploy. Render sets `PORT` automatically.

### SQLite on Render (Important)

Render's filesystem is **ephemeral** on the free tier. Prediction history stored in SQLite will be **lost on every redeploy or restart**. For persistence, attach a [Render persistent disk](https://render.com/docs/disks) and point `DATABASE_URL` to a path on that disk, or migrate to PostgreSQL (not included in this project).

### Memory / Free Tier (512 MB)

The backend is optimized for low memory (CPU-only PyTorch, lazy MTCNN loading, headless OpenCV, garbage collection after video inference). However, **torch + MTCNN + EfficientNetV2 together are memory-intensive**. The free tier may work for light image inference but can OOM on video processing or under concurrent load. If the service crashes or is killed with OOM errors, upgrade to Render's **Starter plan (1 GB RAM)**.

## Deploy Frontend to Vercel

1. Import the repository in [Vercel](https://vercel.com).
2. Set the **Root Directory** to `frontend`.
3. Build settings (defaults are fine):
   - **Build command**: `npm run build`
   - **Output directory**: `dist`
4. Add environment variable:
   - `VITE_API_BASE_URL` → your Render backend URL, e.g. `https://your-api.onrender.com`
5. Deploy. The included `vercel.json` handles SPA routing for `/dashboard`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check (status + model loaded) |
| `POST` | `/predict` | Image/video deepfake detection |
| `GET` | `/evaluate` | Model evaluation metrics |
| `GET` | `/history` | Prediction history |
| `POST` | `/train` | SSE training stream (local datasets required) |

## Notes

- The `src/model.py` MUST contain the `HybridDeepfakeDetector` class for the backend to run properly.
- Training via `/train` in production returns a clear SSE error if `real/` and `fake/` folders are not present.
- On first startup, timm downloads EfficientNetV2 pretrained weights (~30–50 MB). Ensure outbound network access is available.
