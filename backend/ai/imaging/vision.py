import torch
import torchvision.transforms as transforms
import torchxrayvision as xrv
from PIL import Image
import pydicom
import io
import logging
import numpy as np

logger = logging.getLogger(__name__)

class ImagingVisionEngine:
    def __init__(self):
        try:
            self.model = xrv.models.DenseNet(weights="densenet121-res224-all")
            self.model.eval()
        except Exception as e:
            logger.warning(f"Failed to load torchxrayvision model: {e}")
            self.model = None

    def parse_dicom(self, dicom_bytes: bytes):
        try:
            dicom = pydicom.dcmread(io.BytesIO(dicom_bytes))
            pixel_array = dicom.pixel_array
            return pixel_array
        except Exception as e:
            logger.error(f"Failed to parse DICOM: {e}")
            return None
        
    def process_image(self, image_path_or_array):
        if not self.model:
            return {"predictions": {}, "heatmap_url": None}
            
        try:
            if isinstance(image_path_or_array, str):
                img = Image.open(image_path_or_array).convert('L')
                img_array = np.array(img)
            else:
                img_array = image_path_or_array
                
            img_array = xrv.datasets.normalize(img_array, 255)
            img_array = img_array[None, ...]
            
            transform = transforms.Compose([xrv.datasets.XRayCenterCrop(), xrv.datasets.XRayResizer(224)])
            img_tensor = transform(img_array)
            img_tensor = torch.from_numpy(img_tensor).unsqueeze(0)
            
            with torch.no_grad():
                preds = self.model(img_tensor).cpu().numpy()[0]
                
            results = dict(zip(xrv.datasets.default_pathologies, preds))
            # Heatmap generation would be hooked here (Grad-CAM)
            heatmap_url = "/static/heatmaps/placeholder.png" 
            return {"predictions": results, "heatmap_url": heatmap_url}
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {"predictions": {}, "heatmap_url": None}

imaging_vision_engine = ImagingVisionEngine()
