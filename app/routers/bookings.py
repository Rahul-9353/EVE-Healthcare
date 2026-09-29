from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.deps import get_db, get_current_user

router = APIRouter(prefix = "/booking", tags = ["bookings"])

@router.post("/", response_model = schemas.BookingOut, status_code = status.HTTP_201_CREATED)
def create_booking(
    payload: schemas.BookingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    test = db.query(models.DiagnosticTest).filter(models.DiagnosticTest.id == payload.test_id).first()
    if not test:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Diagnostic test not found")

    booking = models.Booking(
        user_id = current_user.id,
        test_id = test.id,
        centre_id = test.centre_id,
        appointment_time = payload.appointment_time,
        amount = test.price,
        status = models.BookingStatus.PENDING,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

@router.get("/", response_model = List[schemas.BookingOut])
def list_my_bookings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Booking).filter(models.Booking.user_id == current_user.id).all()

def _get_owned_booking(booking_id: int, db: Session, current_user: models.User) -> models.Booking:
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "Not authorized to access this booking")
    return booking

@router.get("/{booking_id}", response_model = schemas.BookingOut)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_owned_booking(booking_id, db, current_user)

@router.post("/{booking_id}/cancel", response_model = schemas.BookingOut)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    booking = _get_owned_booking(booking_id, db, current_user)
    if booking.status == models.BookingStatus.CONFIRMED:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "A confirmed (paid) booking cannot be cancelled",
        )
    if booking.status == models.BookingStatus.CANCELLED:
        return booking

    booking.status = models.BookingStatus.CANCELLED
    db.commit()
    db.refresh(booking)
    return booking