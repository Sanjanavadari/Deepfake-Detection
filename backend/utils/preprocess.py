# NOTE: MTCNN face detection is currently disabled — see marked block below for details.
import torch
from torchvision import transforms
from facenet_pytorch import MTCNN
from PIL import Image
from fastapi import HTTPException

_mtcnn_instance = None

# ImageNet normalization standard
normalize = transforms.Normalize(
    mean=[0.485, 0.456, 0.406],
    std=[0.229, 0.224, 0.225],
)


def get_mtcnn() -> MTCNN:
    """Lazily initialize MTCNN on first use to reduce startup memory."""
    global _mtcnn_instance
    if _mtcnn_instance is None:
        # margin=20 adds context around the face; post_process=False keeps values [0, 255]
        _mtcnn_instance = MTCNN(
            image_size=224,
            margin=20,
            keep_all=False,
            post_process=False,
        )
    return _mtcnn_instance


def preprocess_image(image: Image.Image) -> torch.Tensor:
    """
    Resizes to 224x224 and normalizes it (MTCNN face crop currently disabled).
    Input: PIL Image (RGB)
    Output: torch.Tensor of shape [1, 3, 224, 224]
    """
    # === MTCNN FACE DETECTION — DISABLED FOR RENDER FREE TIER (512MB) ===
    # Re-enable by uncommenting this block and removing the bypass below.
    # Disabled on: 2026-07-13. Reason: MTCNN adds ~100-200MB resident
    # memory, pushing the app over Render's free-tier limit during prediction.
    # To restore: comment out the bypass block and uncomment this section.
    #
    # face_tensor = get_mtcnn()(image)
    #
    # if face_tensor is None:
    #     raise HTTPException(status_code=422, detail="No face detected in image")
    #
    # face_tensor = face_tensor / 255.0
    # face_tensor = normalize(face_tensor)
    # return face_tensor.unsqueeze(0)
    # === END MTCNN BLOCK ===

    # --- BYPASS: pass image through without face cropping ---
    # Resize to model input size and normalize; no MTCNN allocation.
    face_tensor = transforms.ToTensor()(image.resize((224, 224), Image.BILINEAR))
    face_tensor = normalize(face_tensor)
    return face_tensor.unsqueeze(0)
