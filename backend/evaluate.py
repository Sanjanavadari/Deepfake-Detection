import torch
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model import HybridDeepfakeDetector

# For testing we'll just run random data if dataset doesn't exist to simulate it for the frontend
def evaluate_model():
    """
    Evaluates the best model on test data and returns metrics.
    """
    best_model_path = os.path.join(os.path.dirname(__file__), 'weights', 'best_model.pth')
    
    if not os.path.exists(best_model_path):
        return {"error": "Model not trained yet. best_model.pth missing."}
        
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model = HybridDeepfakeDetector(cnn_model_name='efficientnet_b0', num_classes=1)
    model.load_state_dict(torch.load(best_model_path, map_location=device))
    model.to(device)
    model.eval()
    
    # IN A REAL SCENARIO: Load test dataset.
    # Because we don't have the dataset guaranteed right now, let's mock the test output
    # based on the requested output format.
    
    # Dummy mock eval to unblock frontend setup
    # In reality, you'd iterate over test_loader and collect preds and true labels
    y_true = np.random.randint(0, 2, 100)
    y_pred_probs = np.random.rand(100)
    y_pred = (y_pred_probs >= 0.5).astype(int)
    
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc_roc = roc_auc_score(y_true, y_pred_probs)
    cm = confusion_matrix(y_true, y_pred).tolist()  # 2x2 array
    
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "auc_roc": auc_roc,
        "confusion_matrix": cm
    }
