import gc
import os
import tempfile

import cv2
import numpy as np
import torch
from PIL import Image

from backend.utils.preprocess import preprocess_image
from backend.utils.grad_cam import generate_grad_cam_base64


# Model / MTCNN face crop size (see backend/utils/preprocess.py)
_MODEL_INPUT_SIZE = (224, 224)


def predict_single_frame(model, image: Image.Image, device):
    """
    Runs prediction on a single PIL image.
    Returns label ("Real" or "Fake"), confidence, and grad_cam base64 string.
    """
    # Downscale ASAP so full-resolution uploads do not linger in memory
    if image.size != _MODEL_INPUT_SIZE:
        image = image.resize(_MODEL_INPUT_SIZE, Image.BILINEAR)

    input_tensor = preprocess_image(image).to(device)

    orig_np = np.array(image.convert('RGB'))

    # Forward pass only — Grad-CAM below needs gradients enabled
    with torch.inference_mode():
        output = model(input_tensor)
        prob = torch.sigmoid(output).item()

    confidence = prob if prob >= 0.5 else 1 - prob
    label = "Fake" if prob >= 0.5 else "Real"

    # Intentionally outside inference_mode: Grad-CAM runs a backward pass
    grad_cam_b64 = generate_grad_cam_base64(model, input_tensor, orig_np)

    del input_tensor, output, orig_np
    gc.collect()

    return label, confidence, grad_cam_b64, prob


def predict_video(model, video_bytes: bytes, device):
    """
    Extracts 1 frame/sec from video and aggregates predictions.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
        tmp_file.write(video_bytes)
        tmp_path = tmp_file.name

    cap = cv2.VideoCapture(tmp_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps == 0:
        fps = 30  # fallback

    frame_results = []
    frame_probs = []

    frame_count = 0
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % fps == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)

                try:
                    label, confidence, grad_cam, prob = predict_single_frame(model, pil_img, device)

                    frame_results.append({
                        "frame_num": frame_count,
                        "label": label,
                        "confidence": float(confidence),
                        "grad_cam": grad_cam
                    })
                    frame_probs.append(prob)
                except Exception:
                    # MTCNN might not detect a face in some frames
                    pass
                finally:
                    del frame, frame_rgb, pil_img

            frame_count += 1
    finally:
        cap.release()
        os.remove(tmp_path)

    if not frame_results:
        raise ValueError("No faces detected in any video frames.")

    avg_prob = sum(frame_probs) / len(frame_probs)
    final_label = "Fake" if avg_prob >= 0.5 else "Real"
    final_confidence = avg_prob if avg_prob >= 0.5 else 1 - avg_prob

    worst_frame = max(
        frame_results,
        key=lambda x: x["confidence"] if x["label"] == "Fake" else -x["confidence"],
    )

    result = {
        "label": final_label,
        "confidence": float(final_confidence),
        "grad_cam_image": worst_frame["grad_cam"],
        "frame_results": [{k: v for k, v in f.items() if k != "grad_cam"} for f in frame_results]
    }

    del frame_results, frame_probs, worst_frame
    gc.collect()

    return result
