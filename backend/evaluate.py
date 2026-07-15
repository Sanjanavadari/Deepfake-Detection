import os
import sys

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from torch.utils.data import DataLoader, random_split
from torchvision import transforms

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model import HybridDeepfakeDetector
from backend.utils.dataset import DeepfakeDataset

DEPLOYED_EVAL_ERROR = (
    "Evaluation requires local validation data — not available in this deployed environment"
)

# Must match predict.py polarity handling for the current checkpoint
APPLY_POLARITY_FLIP = True


def evaluate_model():
    """
    Evaluates best_model.pth on a held-out split of local real/ + fake/ images.
    Returns real metrics, or an error dict if data/weights are unavailable.
    Never fabricates metrics.
    """
    best_model_path = os.path.join(os.path.dirname(__file__), 'weights', 'best_model.pth')

    if not os.path.exists(best_model_path):
        return {"error": "Model not trained yet. best_model.pth missing."}

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    real_dir = os.path.join(project_root, 'real')
    fake_dir = os.path.join(project_root, 'fake')

    if not os.path.isdir(real_dir) or not os.path.isdir(fake_dir):
        return {"error": DEPLOYED_EVAL_ERROR}

    eval_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    dataset = DeepfakeDataset(real_dir, fake_dir, transform=eval_transform)
    dataset_size = len(dataset)
    if dataset_size == 0:
        return {"error": DEPLOYED_EVAL_ERROR}

    # Held-out 20% validation split (fixed seed for reproducibility)
    val_size = max(1, int(0.2 * dataset_size))
    train_size = dataset_size - val_size
    generator = torch.Generator().manual_seed(42)
    _, val_dataset = random_split(dataset, [train_size, val_size], generator=generator)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = HybridDeepfakeDetector(cnn_model_name='efficientnet_b0', num_classes=1)
    model.load_state_dict(torch.load(best_model_path, map_location=device))
    model.to(device)
    model.eval()

    loader = DataLoader(val_dataset, batch_size=8, shuffle=False)
    y_true = []
    y_pred_probs = []

    with torch.inference_mode():
        for inputs, labels in loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            raw_prob = torch.sigmoid(outputs).squeeze(-1)
            # Same checkpoint polarity flip as backend/predict.py (see NOTE there)
            probs = (1.0 - raw_prob) if APPLY_POLARITY_FLIP else raw_prob
            y_pred_probs.extend(probs.cpu().numpy().tolist())
            y_true.extend(labels.squeeze(-1).cpu().numpy().tolist())

    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred_probs = np.asarray(y_pred_probs, dtype=np.float64)
    y_pred = (y_pred_probs >= 0.5).astype(int)

    # Need both classes present for a defined AUC-ROC
    if len(np.unique(y_true)) < 2:
        return {
            "error": (
                "Validation split contains only one class; cannot compute AUC-ROC. "
                "Add more real and fake images and retry."
            )
        }

    accuracy = float(accuracy_score(y_true, y_pred))
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    auc_roc = float(roc_auc_score(y_true, y_pred_probs))
    cm = confusion_matrix(y_true, y_pred).tolist()

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "auc_roc": auc_roc,
        "confusion_matrix": cm,
        "num_samples": int(len(y_true)),
    }
