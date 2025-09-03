from fastapi import FastAPI,APIRouter
from .api.meal_routes import router as meal_router
from contextlib import asynccontextmanager
from .db.session import init_db



@asynccontextmanager
async def lifespan(app:FastAPI):
    init_db()
    yield


app = FastAPI(
    title = "meal-service",
    version = "1.0.0",
    description = "Meals microservice with FastAPI",
    lifespan=lifespan
)

app.include_router(meal_router, prefix = "/api/meals",tags=["meals"])

@app.get("/health")
async def health_check():
    return {"status":"ok","service":"auth"}