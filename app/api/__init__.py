from fastapi import FastAPI
def create_app() -> FastAPI:
    app = FastAPI()
    # other routers
    # Register verification router
    from .verification import router as verification_router
    app.include_router(verification_router, prefix="/api")
    return app