import cv2
import numpy as np
import torch
import torch.nn.functional as F
import base64

class GradCam:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self.target_layer.register_forward_hook(self.save_activation)
        self.target_layer.register_full_backward_hook(self.save_gradient)

    def save_activation(self, module, input, output):
        self.activations = output

    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def generate(self, input_tensor):
        self.model.eval()
        
        # Forward pass
        output = self.model(input_tensor)
        
        # We want to explain the prediction with respect to the output node
        # Since it's binary, output is shape [B, 1].
        self.model.zero_grad()
        output.backward(torch.ones_like(output))
        
        # Pool the gradients across the spatial dimensions
        pooled_gradients = torch.mean(self.gradients, dim=[0, 2, 3])
        
        # Weight the channels by corresponding gradients
        activations = self.activations.detach()[0]
        for i in range(activations.size(0)):
            activations[i, :, :] *= pooled_gradients[i]
            
        # Average the channels of the activations
        heatmap = torch.mean(activations, dim=0).squeeze()
        
        # ReLU on top of the heatmap
        heatmap = F.relu(heatmap)
        
        # Normalize the heatmap
        heatmap /= torch.max(heatmap)
        
        return heatmap.cpu().numpy()

def generate_grad_cam_base64(model, input_tensor, original_image_np):
    """
    Generates a Grad-CAM heatmap and overlays it on the original image.
    Returns base64 encoded PNG string.
    """
    # EfficientNet-B0 (timm): hook conv_head — the final 1x1 Conv2d (320 -> 1280)
    # immediately before bn2 / global pooling. This is the last spatial feature map
    # and the correct Grad-CAM target (equivalent role to EfficientNetV2's conv_head).
    if hasattr(model.backbone, 'conv_head'):
        target_layer = model.backbone.conv_head
    elif hasattr(model.backbone, 'blocks'):
        target_layer = model.backbone.blocks[-1]
    else:
        # Fallback, just pick the last child
        target_layer = list(model.backbone.children())[-1]
        
    cam = GradCam(model, target_layer)
    heatmap = cam.generate(input_tensor)
    
    # Resize heatmap to match original image size (224x224)
    heatmap = cv2.resize(heatmap, (224, 224))
    heatmap = np.uint8(255 * heatmap)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    
    # Ensure original_image_np is RGB and 224x224
    if original_image_np.shape[:2] != (224, 224):
        original_image_np = cv2.resize(original_image_np, (224, 224))
        
    # Superimpose the heatmap on original image
    superimposed_img = heatmap * 0.4 + original_image_np * 0.6
    superimposed_img = np.uint8(superimposed_img)
    
    # Encode as base64 PNG
    _, buffer = cv2.imencode('.png', superimposed_img)
    b64_string = base64.b64encode(buffer).decode('utf-8')
    
    return b64_string
