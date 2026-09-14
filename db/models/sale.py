import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class OrderTypeEnum(str, enum.Enum):
    presencial = "presencial"        # Venta realizada directamente en caja de la tienda
    reserva_pickup = "reserva_pickup" # Pago/Entrega de una reserva en la tienda elegida
    online_delivery = "online_delivery" # Compra e-commerce con envío a domicilio


class PaymentMethodEnum(str, enum.Enum):
    tarjeta = "tarjeta"            # Tarjeta de Crédito / Débito (POS o Pasarela Web)
    efectivo = "efectivo"          # Pago en efectivo en caja
    qr = "qr"                      # Pago por código QR (Simple/PagoQR)
    transferencia = "transferencia" # Transferencia bancaria directa


class PaymentStatusEnum(str, enum.Enum):
    paid = "paid"
    pending = "pending"
    failed = "failed"
    refunded = "refunded"


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True) # None si es envío 100% digital u online
    
    order_type = Column(Enum(OrderTypeEnum), default=OrderTypeEnum.presencial, nullable=False)
    payment_method = Column(Enum(PaymentMethodEnum), default=PaymentMethodEnum.tarjeta, nullable=False)
    payment_status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.paid, nullable=False)
    
    # Detalles específicos de pago con tarjeta u otros medios
    card_type = Column(String, nullable=True)      # e.g., 'VISA', 'Mastercard'
    card_last_four = Column(String, nullable=True) # e.g., '4242'
    transaction_ref = Column(String, nullable=True)# Número de referencia o autorización del POS/Pasarela
    
    total_amount = Column(Float, nullable=False)
    is_paid = Column(Boolean, default=True)
    payment_provider = Column(String, nullable=True) # e.g., 'stripe', 'pos_redbanb', 'qr_simple'
    payment_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
    branch = relationship("Branch")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    
    order = relationship("Order", back_populates="items")
    variant = relationship("ProductVariant")

