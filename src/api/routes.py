from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.services.audit_service import AuditService
from src.db.models import Store

router = APIRouter()

@router.post("/audit/{store_id}")
async def run_shelf_audit(
    store_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    service = AuditService(db)
    try:
        result = service.create_audit(store_id, file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/store")
def create_store(name: str, location: str, db: Session = Depends(get_db)):
    # Quick helper to seed data
    store = Store(name=name, location=location, planogram={"bottle": 5, "can": 3}) # default mock planogram
    db.add(store)
    db.commit()
    db.refresh(store)
    return store