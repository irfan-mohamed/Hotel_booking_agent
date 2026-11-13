# Register health router
from app.api.routes.health import router as health_router
app.include_router(health_router)