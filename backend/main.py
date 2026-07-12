import gc
import io
import logging
import os
import sys

import torch
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.model import HybridDeepfakeDetector

from backend.config import MODEL_PATH, PORT, LOG_LEVEL, get_allowed_origins
from backend.database import init_db, save_prediction, get_all_predictions
from backend.predict import OOM_DETAIL, is_oom_error, predict_single_frame, predict_video
from backend.evaluate import evaluate_model
from backend.train import train_model

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = None
weights_loaded = False


@app.on_event("startup")
async def startup_event():
    # Limit intra-op threads before loading models (Render free tier CPU/RAM)
    torch.set_num_threads(1)

    await init_db()

    global model, weights_loaded
    model = HybridDeepfakeDetector(cnn_model_name='efficientnet_b0', num_classes=1)

    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        weights_loaded = True
        logger.info("Loaded trained weights from %s", MODEL_PATH)
    else:
        # No best_model.pth: uses timm pretrained EfficientNet-B0 backbone + randomly
        # initialized FC head. Predictions will NOT be meaningful until a trained
        # best_model.pth is placed in backend/weights/.
        weights_loaded = False
        logger.warning(
            "No trained weights at %s. Using pretrained EfficientNet-B0 backbone with "
            "untrained FC head. Predictions will not be meaningful until best_model.pth is added.",
            MODEL_PATH,
        )

    model.to(device)
    model.eval()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "weights_loaded": weights_loaded,
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    image = None

    is_video = file.filename.lower().endswith(('.mp4', '.avi', '.mov'))

    try:
        if is_video:
            result = predict_video(model, contents, device)
        else:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            contents = None  # release raw upload bytes ASAP
            # Drop full-res pixels before MTCNN / model (model input is 224x224)
            if image.size != (224, 224):
                image = image.resize((224, 224), Image.BILINEAR)
            label, confidence, grad_cam_b64, prob = predict_single_frame(model, image, device)
            result = {
                "label": label,
                "confidence": float(confidence),
                "grad_cam_image": grad_cam_b64
            }

        await save_prediction(
            filename=file.filename,
            label=result["label"],
            confidence=result["confidence"],
            grad_cam_path=None,
        )
        return result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except (MemoryError, RuntimeError) as e:
        if is_oom_error(e):
            logger.error("OOM during prediction for file %s: %s", file.filename, e)
            raise HTTPException(status_code=503, detail=OOM_DETAIL)
        logger.exception("Prediction failed for file %s", file.filename)
        raise HTTPException(status_code=500, detail="An error occurred during prediction.")
    except Exception:
        logger.exception("Prediction failed for file %s", file.filename)
        raise HTTPException(status_code=500, detail="An error occurred during prediction.")
    finally:
        del contents, image
        gc.collect()


class TrainParams(BaseModel):
    epochs: int
    batch_size: int
    learning_rate: float


@app.post("/train")
async def train(params: TrainParams):
    return StreamingResponse(
        train_model(params.epochs, params.batch_size, params.learning_rate),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/evaluate")
async def evaluate():
    metrics = evaluate_model()
    if "error" in metrics:
        raise HTTPException(status_code=400, detail=metrics["error"])
    return metrics


@app.get("/history")
async def history():
    return await get_all_predictions()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, workers=1)
