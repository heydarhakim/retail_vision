import os
import uuid
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.inference import InferenceEngine
from app.repositories.store_repo import StoreRepository
from app.schemas.audit import AuditOut

class AuditService:
    def __init__(self, db: AsyncSession):
        self.repo = StoreRepository(db)
        self.inference = InferenceEngine()

    async def process_shelf_audit(self, store_id: int, file) -> AuditOut:
        # 1. Validation
        store = await self.repo.get_store(store_id)
        if not store:
            raise ValueError("Store not found")

        # 2. IO: Save Image Asynchronously
        file_ext = file.filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{file_ext}"
        filepath = os.path.join("data/images", filename)
        
        content = await file.read()
        async with aiofiles.open(filepath, 'wb') as out_file:
            await out_file.write(content)

        # 3. Inference (CPU/GPU)
        img_np = self.inference.preprocess(content)
        # Passing as list to utilize batch architecture
        batch_results = self.inference.predict_batch([img_np])
        detections = batch_results[0]

        # 4. Compliance Logic
        detected_counts = {}
        for d in detections:
            name = d['class_name']
            detected_counts[name] = detected_counts.get(name, 0) + 1

        missing_items = []
        misplaced_items = [] # Simplification: items detected not in planogram
        total_expected = 0
        total_found_correctly = 0

        # Compare vs Planogram
        if store.planogram:
            for product, expected_qty in store.planogram.items():
                total_expected += expected_qty
                actual_qty = detected_counts.get(product, 0)
                
                if actual_qty < expected_qty:
                    missing_items.append(f"{product} (Exp: {expected_qty}, Fnd: {actual_qty})")
                    total_found_correctly += actual_qty
                else:
                    total_found_correctly += expected_qty # Cap at expected for score
                
                # Remove checked items to find misplaced ones
                if product in detected_counts:
                    del detected_counts[product]
            
            # Remaining items are misplaced/unlisted
            misplaced_items = list(detected_counts.keys())

        # Calculate Score
        score = 0.0
        if total_expected > 0:
            score = round((total_found_correctly / total_expected) * 100, 2)
        elif len(detections) > 0: 
            score = 100.0 # No planogram but items found

        # 5. Persistence
        audit = await self.repo.create_audit(store_id, f"/static/images/{filename}", score)
        await self.repo.add_detections(audit.id, detections)

        return AuditOut(
            id=audit.id,
            store_id=store.id,
            image_path=audit.image_path,
            timestamp=audit.timestamp,
            compliance_score=score,
            detections=detections,
            missing_items=missing_items,
            misplaced_items=misplaced_items
        )