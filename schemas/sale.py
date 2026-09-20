from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from db.models.sale import OrderTypeEnum, PaymentMethodEnum, PaymentStatusEnum

class OrderItemBase(BaseModel):
    variant_id: int
    quantity: int
    unit_price: float

class OrderItemCreate(OrderItemBase):
    pass

class ProductSummary(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class VariantSummary(BaseModel):
    id: int
    size: str
    color: str
    product: Optional[ProductSummary] = None
    image_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    variant: Optional[VariantSummary] = None

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    branch_id: Optional[int] = None
    order_type: OrderTypeEnum = OrderTypeEnum.presencial
    payment_method: PaymentMethodEnum = PaymentMethodEnum.tarjeta
    payment_status: PaymentStatusEnum = PaymentStatusEnum.paid
    total_amount: float
    is_paid: bool = True
    payment_provider: Optional[str] = None
    card_type: Optional[str] = None
    card_last_four: Optional[str] = None
    transaction_ref: Optional[str] = None

class OrderCreate(BaseModel):
    branch_id: Optional[int] = None
    items: List[OrderItemCreate]
    # Atributos de pago simulados (se pasarán desde el frontend)
    payment_method: PaymentMethodEnum = PaymentMethodEnum.tarjeta
    card_type: Optional[str] = None
    card_last_four: Optional[str] = None
    transaction_ref: Optional[str] = None

class Order(OrderBase):
    id: int
    user_id: int
    created_at: datetime
    items: List[OrderItem]

    class Config:
        from_attributes = True
