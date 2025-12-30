from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    # Simple JSON planogram for MVP: { "product_name": expected_count }
    planogram = Column(JSON, default={}) 
    audits = relationship("Audit", back_populates="store")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    sku_code = Column(String, unique=True)

class Audit(Base):
    __tablename__ = "audits"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    image_path = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    compliance_score = Column(Float, default=0.0)
    
    store = relationship("Store", back_populates="audits")
    detections = relationship("Detection", back_populates="audit")

class Detection(Base):
    __tablename__ = "detections"
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(Integer, ForeignKey("audits.id"))
    class_name = Column(String) # Denormalized for speed
    confidence = Column(Float)
    bbox = Column(JSON) # [x_min, y_min, x_max, y_max] (Normalized)
    
    audit = relationship("Audit", back_populates="detections")