from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user
from db.models.user import User
from db.models.sale import Order, OrderItem, OrderTypeEnum, PaymentStatusEnum
from db.models.branch import Inventory
from schemas.sale import Order as OrderSchema, OrderCreate

router = APIRouter()

@router.get("", response_model=List[OrderSchema])
def list_orders(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Lista las órdenes de compra.
    Los clientes solo ven sus propias órdenes.
    Los admins/encargados/cajeros pueden ver más (depende del rol, pero para simplicidad mostramos todas si son admin).
    """
    if current_user.role.name == "cliente":
        orders = db.query(Order).filter(Order.user_id == current_user.id).offset(skip).limit(limit).all()
    else:
        orders = db.query(Order).offset(skip).limit(limit).all()
    return orders

@router.post("", response_model=OrderSchema, status_code=status.HTTP_201_CREATED)
def create_order(
    *,
    db: Session = Depends(get_db),
    order_in: OrderCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Crea una nueva orden de compra (Checkout desde el Carrito / POS Caja).
    Calcula el total a partir de los items enviados y descuenta del inventario.
    """
    # Calcular total amount
    total_amount = sum(item.quantity * item.unit_price for item in order_in.items)
    
    # Determinar tipo de orden (online_delivery si no hay branch_id)
    order_type = OrderTypeEnum.online_delivery if order_in.branch_id is None else OrderTypeEnum.presencial

    order = Order(
        user_id=current_user.id,
        branch_id=order_in.branch_id,
        order_type=order_type,
        payment_method=order_in.payment_method,
        payment_status=PaymentStatusEnum.paid, # Asumimos pagado para la simulación
        card_type=order_in.card_type,
        card_last_four=order_in.card_last_four,
        transaction_ref=order_in.transaction_ref or "TXN-SIMULADA-1234",
        total_amount=total_amount,
        is_paid=True,
        payment_provider="Simulated_Gateway"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Crear items y descontar inventario
    for item_in in order_in.items:
        order_item = OrderItem(
            order_id=order.id,
            variant_id=item_in.variant_id,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price
        )
        db.add(order_item)

        # Actualizar stock en la sucursal o cualquier inventario de la variante
        inv_query = db.query(Inventory).filter(Inventory.variant_id == item_in.variant_id)
        if order_in.branch_id:
            inv = inv_query.filter(Inventory.branch_id == order_in.branch_id).first()
            if not inv:
                inv = inv_query.first()
        else:
            inv = inv_query.first()

        if inv:
            inv.stock = max(0, inv.stock - item_in.quantity)

    db.commit()
    db.refresh(order)
    
    return order
