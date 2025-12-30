from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api import endpoints
from app.db.database import init_db, get_db, SessionLocal
from app.db.models import Store
from sqlalchemy import select

# Seeding Logic for Demo
async def seed_data():
    async with SessionLocal() as db:
        result = await db.execute(select(Store))
        if not result.scalars().first():
            # Seed a demo store
            store = Store(
                name="SuperMart Downtown",
                location="NYC Block 4",
                # Note: These keys match COCO dataset classes for immediate demo functionality
                planogram={"bottle": 5, "cup": 3, "bowl": 2} 
            )
            db.add(store)
            await db.commit()
            print("--- Database Seeded with Demo Store ---")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await seed_data()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mounts
app.mount("/static", StaticFiles(directory="data"), name="static")
app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")

app.include_router(endpoints.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "RetailVision API is running. Go to /app/ for UI."}