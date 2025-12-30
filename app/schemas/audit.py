from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class DetectionOut(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float]

class AuditOut(BaseModel):
    id: int
    store_id: int
    image_path: str
    timestamp: datetime
    compliance_score: float
    detections: List[DetectionOut]
    missing_items: List[str]
    misplaced_items: List[str]

    class Config:
        from_attributes = True

class StoreCreate(BaseModel):
    name: str
    location: str
    planogram: Dict[str, int]