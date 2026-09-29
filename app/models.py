import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Enum,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())


class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, index = True)
    email = Column(String, unique = True, index = True, nullable = False)
    hashed_password = Column(String, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)

    bookings = relationship("Booking", back_populates = "user")

class DiagnosticCentre(Base):
    __tablename__ = "diagnostic_centres"

    id = Column(Integer, primary_key = True, index = True)
    name = Column(String, nullable = False, index = True)
    location = Column(String, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)

    tests = relationship("DiagnosticTest", back_populates = "centre", cascade = "all, delete-orphan")

class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"

    id = Column(Integer, primary_key = True, index = True)
    centre_id = Column(Integer, ForeignKey("diagnostic_centres.id"), nullable = False)
    name = Column(String, nullable = False, index = True)
    price = Column(Float, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)

    centre = relationship("DiagnosticCentre", back_populates = "tests")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    test_id = Column(Integer, ForeignKey("diagnostic_tests.id"), nullable = False)
    centre_id = Column(Integer, ForeignKey("diagnostic_centres.id"), nullable = False)
    appointment_time = Column(DateTime, nullable = False)
    amount = Column(Float, nullable = False)
    status = Column(Enum(BookingStatus), nullable = False, default = BookingStatus.PENDING)
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate = datetime.utcnow)

    user = relationship("User", back_populates = "bookings")
    test = relationship("DiagnosticTest")
    centre = relationship("DiagnosticCentre")
    payments = relationship("Payment", back_populates = "booking")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key = True, index = True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable = False)
    amount = Column(Float, nullable = False)
    status = Column(Enum(PaymentStatus), nullable = False)
    provider_reference = Column(String, unique = True, index = True, default = gen_uuid)
    created_at = Column(DateTime, default = datetime.utcnow)

    booking = relationship("Booking", back_populates = "payments")

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("event_id", name = "uq_webhook_event_id"),)

    id = Column(Integer, primary_key = True, index = True)
    event_id = Column(String, nullable = False, index = True)
    payload = Column(JSON, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)