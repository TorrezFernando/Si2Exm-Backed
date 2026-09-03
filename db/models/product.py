from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from db.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    base_price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    season = Column(String) # e.g., Summer 2026
    
    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    size = Column(String, nullable=False) # e.g., S, M, L, XL
    color = Column(String, nullable=False) # e.g., Red, Blue
    sku = Column(String, unique=True, index=True, nullable=False)
    price_override = Column(Float, nullable=True) # Optional different price for specific variant
    
    product = relationship("Product", back_populates="variants")
    inventories = relationship("Inventory", back_populates="variant")
