from fastapi import FastAPI

from app.api.routes.availability import router as availability_router
from app.api.routes.booking import router as booking_router


app = FastAPI(
    title="Hotel Booking Agent API",
    description=(
        "Backend API for hotel room availability "
        "and booking operations."
    ),
    version="1.0.0",
)


app.include_router(
    availability_router,
    prefix="/api",
)

app.include_router(
    booking_router,
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