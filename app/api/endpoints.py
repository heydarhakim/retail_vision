from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.audit_service import AuditService
from app.repositories.store_repo import StoreRepository
from app.schemas.audit import AuditOut, StoreCreate

router = APIRouter()

@router.post("/stores")
async def create_store(store: StoreCreate, db: AsyncSession = Depends(get_db)):
    repo = StoreRepository(db)
    return await repo.create_store(store.name, store.location, store.planogram)

@router.get("/stores")
async def get_stores(db: AsyncSession = Depends(get_db)):
    # Minimal implementation for frontend dropdown
    from sqlalchemy import select
    from app.db.models import Store
    result = await db.execute(select(Store))
    return result.scalars().all()

@router.post("/audit/{store_id}", response_model=AuditOut)
async def perform_audit(
    store_id: int, 
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db)
):
    service = AuditService(db)
    try:
        return await service.process_shelf_audit(store_id, file)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))