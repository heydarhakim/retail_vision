from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Store, Audit, Detection

class StoreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_store(self, name: str, location: str, planogram: dict):
        store = Store(name=name, location=location, planogram=planogram)
        self.db.add(store)
        await self.db.commit()
        await self.db.refresh(store)
        return store

    async def get_store(self, store_id: int):
        result = await self.db.execute(select(Store).where(Store.id == store_id))
        return result.scalars().first()

    async def create_audit(self, store_id: int, image_path: str, score: float):
        audit = Audit(store_id=store_id, image_path=image_path, compliance_score=score)
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(audit)
        return audit

    async def add_detections(self, audit_id: int, detections: list):
        # Batch insert for performance
        objs = [
            Detection(
                audit_id=audit_id,
                class_name=d['class_name'],
                confidence=d['confidence'],
                bbox=d['bbox']
            ) for d in detections
        ]
        self.db.add_all(objs)
        await self.db.commit()