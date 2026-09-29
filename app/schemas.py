from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict, Field

from app.models import BookingStatus, PaymentStatus

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length = 8)

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    id: int
    email: EmailStr
    created_at: datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TestCreate(BaseModel):
    name: str
    price: float = Field(gt = 0)

class TestOut(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    id: int
    name: str
    price: float

class CentreCreate(BaseModel):
    name: str
    location: str

class CentreOut(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    id: int
    name: str
    location: str
    tests: List[TestOut] = []

class BookingCreate(BaseModel):
    test_id: int
    appointment_time: datetime

class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    id: int
    user_id: int
    test_id: int
    centre_id: int
    appointment_time: datetime
    amount: float
    status: BookingStatus
    created_at: datetime

class PaymentCreate(BaseModel):
    booking_id: int

class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    id: int
    booking_id: int
    amount: float
    status: PaymentStatus
    provider_reference: str

class WebhookPayload(BaseModel):
    event_id: str
    booking_id: int
    provider_reference: Optional[str] = None
    status: PaymentStatus