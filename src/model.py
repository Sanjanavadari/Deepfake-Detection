import torch
import torch.nn as nn
import timm

class HybridDeepfakeDetector(nn.Module):
    def __init__(self, cnn_model_name='efficientnet_b0', num_classes=1):
        super(HybridDeepfakeDetector, self).__init__()
        # Lightweight EfficientNet-B0 backbone (timm); suited to Render free-tier RAM
        self.backbone = timm.create_model(cnn_model_name, pretrained=True, num_classes=0)
        # num_features is backbone-specific (1280 for efficientnet_b0) — sized dynamically
        self.fc = nn.Linear(self.backbone.num_features, num_classes)
        
    def forward(self, x):
        features = self.backbone(x)
        out = self.fc(features)
        return out
