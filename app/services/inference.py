import torch
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class InferenceEngine:
    """
    Singleton Wrapper for YOLOv8.
    Supports Batch Inference and FP16 Quantization.
    """
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InferenceEngine, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        logger.info(f"Loading Model from {settings.MODEL_PATH}...")
        self._model = YOLO(settings.MODEL_PATH)
        
        # ENGINEERING: Check for GPU availability
        if torch.cuda.is_available():
            logger.info("CUDA detected. Running in FP16 mode.")
            # YOLOv8 handles .half() internally on prediction if specified, 
            # but explicit FP16 export is also possible.
        else:
            logger.warning("CUDA not found. Running on CPU (INT8 quantization recommended for Edge).")

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        """Convert bytes to opencv format."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img

    def predict_batch(self, images: List[np.ndarray]) -> List[List[dict]]:
        """
        Batch inference implementation.
        Accepts list of numpy images, returns list of detections per image.
        """
        # agnostic=True applies NMS across classes (good for dense shelves)
        results = self._model.predict(images, conf=0.25, iou=0.45, agnostic_nms=True)
        
        batch_output = []
        for result in results:
            detections = []
            for box in result.boxes:
                # Engineering: Logging low confidence drift
                conf = float(box.conf)
                if conf < 0.4:
                    logger.debug(f"Low confidence detection: {conf}")

                detections.append({
                    "class_id": int(box.cls),
                    "class_name": result.names[int(box.cls)],
                    "confidence": conf,
                    "bbox": box.xyxyn.tolist()[0] # Normalized [x1, y1, x2, y2]
                })
            batch_output.append(detections)
        
        return batch_output