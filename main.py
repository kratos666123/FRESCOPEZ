from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.infrastructure.config.settings import get_settings
from app.presentation.api.middleware.error_handler import register_exception_handlers
from app.presentation.api.routers.auth_router import router as auth_router
from app.presentation.api.routers.user_router import router as user_router
from app.presentation.api.routers.category_router import router as category_router
from app.presentation.api.routers.product_router import router as product_router
from app.presentation.api.routers.order_router import router as order_router
from app.presentation.api.routers.delivery_router import router as delivery_router
from app.presentation.api.routers.vehicle_router import router as vehicle_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

os.makedirs("static/products", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handlers ────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ──────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router,     prefix=API_PREFIX)
app.include_router(user_router,     prefix=API_PREFIX)
app.include_router(category_router, prefix=API_PREFIX)
app.include_router(product_router,  prefix=API_PREFIX)
app.include_router(order_router,    prefix=API_PREFIX)
app.include_router(delivery_router, prefix=API_PREFIX)
app.include_router(vehicle_router,  prefix=API_PREFIX)


@app.post("/__test_post")
def __test_post(payload: dict):
    return {"ok": True, "received": payload}


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Sistema"], summary="Health check")
def health_check():
    return {
        "success": True,
        "message": "API funcionando correctamente",
        "data": {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
