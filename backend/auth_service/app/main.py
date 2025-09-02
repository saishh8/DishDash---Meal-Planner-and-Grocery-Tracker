from fastapi import FastAPI
from .api.auth_routes import router as auth_router


app = FastAPI(
    title = "auth-service",
    version = "1.0.0",
    description = "Authentication microservice with FastAPI"

)

#---ROUTERS---

app.include_router(auth_router,prefix = "/api/auth", tags=["auth"])



@app.get("/health")
async def health_check():
    return {"status":"ok","service":"auth"}


