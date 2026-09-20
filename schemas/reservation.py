from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from db.models.reservation import ReservationStatus


# ─── Item de Reserva ──────────────────────────────────────────────────────────

class ReservationItemBase(BaseModel):
    variant_id: int
    quantity: int
    unit_price: Optional[float] = None

class ReservationItemCreate(ReservationItemBase):
    pass

class ReservationItem(ReservationItemBase):
    id: int
    reservation_id: int

    class Config:
        from_attributes = True


# ─── Reserva ──────────────────────────────────────────────────────────────────

class ReservationCreate(BaseModel):
    branch_id: int
    pickup_date: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[ReservationItemCreate]

class ReservationUpdate(BaseModel):
    status: Optional[ReservationStatus] = None
    pickup_date: Optional[datetime] = None
    notes: Optional[str] = None

class Reservation(BaseModel):
    id: int
    user_id: int
    branch_id: int
    status: ReservationStatus
    pickup_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[ReservationItem] = []

    class Config:
        from_attributes = True
