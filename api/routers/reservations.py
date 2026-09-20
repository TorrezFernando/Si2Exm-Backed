from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_active_user, require_permission
from db.models.user import User
from db.models.reservation import Reservation, ReservationItem, ReservationStatus
from db.models.product import ProductVariant
from schemas.reservation import (
    Reservation as ReservationSchema,
    ReservationCreate,
    ReservationUpdate,
)


class ReservationStatusUpdate(BaseModel):
    status: ReservationStatus

router = APIRouter()


@router.get("", response_model=List[ReservationSchema])
def list_reservations(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Lista las reservas.
    - Clientes: solo ven las suyas.
    - Admin/Encargado: ven todas.
    """
    user_perms = {p.name for p in (current_user.role.permissions if current_user.role else [])}
    if "reservations:read" in user_perms or "users:read" in user_perms:
        reservations = db.query(Reservation).offset(skip).limit(limit).all()
    else:
        reservations = (
            db.query(Reservation)
            .filter(Reservation.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    return reservations


@router.get("/{reservation_id}", response_model=ReservationSchema)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Obtiene el detalle de una reserva."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    # Solo el dueño o staff puede verla
    user_perms = {p.name for p in (current_user.role.permissions if current_user.role else [])}
    if reservation.user_id != current_user.id and "reservations:read" not in user_perms and "users:read" not in user_perms:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta reserva")
    return reservation


@router.post("", response_model=ReservationSchema, status_code=status.HTTP_201_CREATED)
def create_reservation(
    *,
    db: Session = Depends(get_db),
    reservation_in: ReservationCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Crea una nueva reserva para el usuario autenticado."""
    if not reservation_in.items:
        raise HTTPException(status_code=400, detail="La reserva debe tener al menos un producto")

    reservation = Reservation(
        user_id=current_user.id,
        branch_id=reservation_in.branch_id,
        pickup_date=reservation_in.pickup_date,
        notes=reservation_in.notes,
        status=ReservationStatus.pending,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    for item_in in reservation_in.items:
        # Verificar que la variante existe
        variant = db.query(ProductVariant).filter(ProductVariant.id == item_in.variant_id).first()
        if not variant:
            db.delete(reservation)
            db.commit()
            raise HTTPException(status_code=404, detail=f"Variante {item_in.variant_id} no encontrada")

        item = ReservationItem(
            reservation_id=reservation.id,
            variant_id=item_in.variant_id,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price or variant.price_override,
        )
        db.add(item)

    db.commit()
    db.refresh(reservation)
    return reservation


@router.patch("/{reservation_id}/status", response_model=ReservationSchema)
def update_reservation_status(
    reservation_id: int,
    reservation_in: ReservationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reservations:write", "sales:write", "users:read")),
) -> Any:
    """Actualiza el estado de una reserva (ej. confirmado/completado/cancelado)."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    reservation.status = reservation_in.status
    db.commit()
    db.refresh(reservation)
    return reservation


@router.patch("/{reservation_id}/cancel", response_model=ReservationSchema)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Cancela una reserva (solo el dueño o admin)."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    if reservation.user_id != current_user.id:
        user_perms = {p.name for p in (current_user.role.permissions if current_user.role else [])}
        if "users:read" not in user_perms:
            raise HTTPException(status_code=403, detail="No puedes cancelar esta reserva")
    if reservation.status == ReservationStatus.completed:
        raise HTTPException(status_code=400, detail="No se puede cancelar una reserva completada")

    reservation.status = ReservationStatus.cancelled
    db.commit()
    db.refresh(reservation)
    return reservation


@router.patch("/{reservation_id}", response_model=ReservationSchema)
def update_reservation(
    reservation_id: int,
    reservation_in: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reservations:write", "sales:write", "users:read")),
) -> Any:
    """Actualiza notas, horario o estado de una reserva."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    update_data = reservation_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reservation, field, value)

    db.commit()
    db.refresh(reservation)
    return reservation
