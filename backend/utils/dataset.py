import os
from PIL import Image
from torch.utils.data import Dataset
import torchvision.transforms as transforms
from backend.utils.preprocess import get_mtcnn

class DeepfakeDataset(Dataset):
    def __init__(self, real_dir, fake_dir, transform=None):
        self.real_dir = real_dir
        self.fake_dir = fake_dir
        self.transform = transform
        self.samples = []
        
        # Load real images (label 0)
        if os.path.exists(real_dir):
            for file in os.listdir(real_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.samples.append((os.path.join(real_dir, file), 0.0))
                    
        # Load fake images (label 1)
        if os.path.exists(fake_dir):
            for file in os.listdir(fake_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.samples.append((os.path.join(fake_dir, file), 1.0))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert('RGB')
        
        # We apply MTCNN to crop face, if no face we just use the raw image resized.
        # For training, it's safer to use images that already have faces.
        face = get_mtcnn()(image)
        if face is None:
            # Fallback if no face detected
            face = transforms.ToTensor()(image.resize((224, 224)))
        else:
            face = face / 255.0

        if self.transform:
            face = self.transform(face)
            
        import torch
        return face, torch.tensor([label], dtype=torch.float32)
