from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, centres, bookings, payments

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title = "EVE Healthcare - Diagnostic Booking API",
    description = "Backend service for diagnostic test bookings and simulated payments.",
    version = "1.0.0",
)

app.include_router(auth.router)
app.include_router(centres.router)
app.include_router(bookings.router)
app.include_router(payments.router)

@app.get("/health", tags = ["health"])
def health_check():
    return {"status": "ok"}