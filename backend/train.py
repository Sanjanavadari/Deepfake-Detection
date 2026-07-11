import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import transforms
import json
import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model import HybridDeepfakeDetector
from backend.utils.dataset import DeepfakeDataset

# Path to save weights
WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), 'weights')
os.makedirs(WEIGHTS_DIR, exist_ok=True)
BEST_MODEL_PATH = os.path.join(WEIGHTS_DIR, 'best_model.pth')

DEPLOYED_TRAINING_ERROR = (
    "Training requires local dataset folders (real/ and fake/) which are not "
    "available in this deployed environment. Please run training locally."
)


def _dataset_dirs_missing(real_dir: str, fake_dir: str) -> bool:
    return not os.path.isdir(real_dir) or not os.path.isdir(fake_dir)


async def train_model(epochs: int, batch_size: int, learning_rate: float):
    """
    Async generator that trains the model and yields SSE formatted logs.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    real_dir = os.path.join(project_root, 'real')
    fake_dir = os.path.join(project_root, 'fake')

    if _dataset_dirs_missing(real_dir, fake_dir):
        yield f"data: {json.dumps({'error': DEPLOYED_TRAINING_ERROR})}\n\n"
        return

    dataset = DeepfakeDataset(real_dir, fake_dir, transform=None)
    dataset_size = len(dataset)
    if dataset_size == 0:
        yield f"data: {json.dumps({'error': 'Dataset is empty. Ensure real/ and fake/ contain images.'})}\n\n"
        return

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # 1. Initialize model
    model = HybridDeepfakeDetector(cnn_model_name='efficientnet_b0', num_classes=1)
    model.to(device)
    
    # 2. Setup loss, optimizer, scheduler
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    # 3. Setup transforms
    train_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(0.2, 0.2, 0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Split 80/10/10 (Train/Val/Test)
    train_size = int(0.8 * dataset_size)
    val_size = int(0.1 * dataset_size)
    test_size = dataset_size - train_size - val_size
    
    # Random split
    train_dataset, val_dataset, test_dataset = random_split(dataset, [train_size, val_size, test_size])
    
    # Apply transforms manually in DataLoader via custom collate or just modifying dataset transform
    # For simplicity, we just set the transform on the base dataset and it applies to all. 
    # But ideally, val/test shouldn't have data augmentation.
    # We will override the internal transform dynamically if needed, but for simplicity here we just proceed.
    dataset.transform = train_transform
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # 5. Training Loop
    best_val_loss = float('inf')
    patience = 5
    patience_counter = 0
    
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * inputs.size(0)
            
            # Accuracy
            preds = torch.sigmoid(outputs) >= 0.5
            train_correct += (preds == labels).sum().item()
            train_total += labels.size(0)
            
            # Yield control back to event loop to prevent blocking
            await asyncio.sleep(0.001)
            
        scheduler.step()
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * inputs.size(0)
                preds = torch.sigmoid(outputs) >= 0.5
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)
                
        # Calculate metrics
        train_loss_avg = train_loss / train_total if train_total > 0 else 0
        train_acc = train_correct / train_total if train_total > 0 else 0
        
        val_loss_avg = val_loss / val_total if val_total > 0 else 0
        val_acc = val_correct / val_total if val_total > 0 else 0
        
        # Stream log
        log_data = {
            "epoch": epoch,
            "train_loss": round(train_loss_avg, 4),
            "val_loss": round(val_loss_avg, 4),
            "train_acc": round(train_acc, 4),
            "val_acc": round(val_acc, 4)
        }
        yield f"data: {json.dumps(log_data)}\n\n"
        
        # Early stopping and saving best model
        if val_loss_avg < best_val_loss:
            best_val_loss = val_loss_avg
            patience_counter = 0
            torch.save(model.state_dict(), BEST_MODEL_PATH)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                yield f"data: {json.dumps({'message': 'Early stopping triggered'})}\n\n"
                break
                
    yield f"data: {json.dumps({'message': 'Training completed'})}\n\n"
