import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.deps import get_db, get_current_user

router = APIRouter(prefix="/payments", tags = ["payments"])

def _get_owned_booking(booking_id: int, db: Session, current_user: models.User) -> models.Booking:
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "Not authorised to pay for this booking")
    return booking

@router.post("/", response_model = schemas.PaymentOut, status_code = status.HTTP_201_CREATED)
def create_payment(
    payload: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    booking = _get_owned_booking(payload.booking_id, db, current_user)

    if booking.status == models.BookingStatus.CONFIRMED:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Booking is already paid for")
    if booking.status == models.BookingStatus.CANCELLED:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Cannot pay for a cancelled booking")

    outcome = (
        models.PaymentStatus.SUCCESS
        if random.random() < settings.payment_success_rate
        else models.PaymentStatus.FAILED
    )

    payment = models.Payment(booking_id = booking.id, amount = booking.amount, status = outcome)
    db.add(payment)

    booking.status = (
        models.BookingStatus.CONFIRMED if outcome == models.PaymentStatus.SUCCESS else models.BookingStatus.FAILED
    )

    db.commit()
    db.refresh(payment)
    return payment

@router.post("/webhook/", status_code = status.HTTP_200_OK)
def payment_webhook(payload: schemas.WebhookPayload, db: Session = Depends(get_db)):
    existing_event = (
        db.query(models.WebhookEvent).filter(models.WebhookEvent.event_id == payload.event_id).first()
    )
    if existing_event:
        return {"status": "ignored", "reason": "event already processed", "event_id": payload.event_id}

    booking = db.query(models.Booking).filter(models.Booking.id == payload.booking_id).first()
    if not booking:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Booking not found")

    if booking.status == models.BookingStatus.CANCELLED:
        db.add(models.WebhookEvent(event_id = payload.event_id, payload = payload.model_dump(mode = "json")))
        db.commit()
        return {"status": "ignored", "reason": "booking is cancelled", "event_id": payload.event_id}

    payment = None
    if payload.provider_reference:
        payment = (
            db.query(models.Payment)
            .filter(models.Payment.provider_reference == payload.provider_reference)
            .first()
        )

    if payment is None:
        payment = models.Payment(
            booking_id = booking.id,
            amount = booking.amount,
            status = payload.status,
            provider_reference = payload.provider_reference or None,
        )
        db.add(payment)
    else:
        payment.status = payload.status

    booking.status = (
        models.BookingStatus.CONFIRMED
        if payload.status == models.PaymentStatus.SUCCESS
        else models.BookingStatus.FAILED
    )

    db.add(models.WebhookEvent(event_id = payload.event_id, payload = payload.model_dump(mode = "json")))
    db.commit()

    return {"status": "processed", "booking_id": booking.id, "booking_status": booking.status}