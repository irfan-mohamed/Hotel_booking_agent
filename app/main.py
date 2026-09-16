from fastapi import FastAPI

from app.api.routes.chat import router as chat_router


app = FastAPI(
    title="Hotel Booking Agent API",
    description=(
        "Backend API for hotel room availability "
        "and booking operations."
    ),
    version="1.0.0",
)


app.include_router(
    chat_router,
    prefix="/api",
)


@app.get(
    "/",
    tags=["Health"],
)
def root() -> dict[str, str]:
    """
    Basic API health endpoint.
    """

    return {
        "status": "ok",
        "service": "hotel-booking-agent",
    }


@app.get(
    "/health",
    tags=["Health"],
)
def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    """

    return {
        "status": "healthy",
    }