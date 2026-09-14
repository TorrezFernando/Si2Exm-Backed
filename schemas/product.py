from typing import List, Optional
from pydantic import BaseModel, ConfigDict

# --- Category ---
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Product Variant ---
class ProductVariantBase(BaseModel):
    size: str
    color: str
    sku: str
    price_override: Optional[float] = None
    image_url: Optional[str] = None

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariant(ProductVariantBase):
    id: int
    product_id: int
    model_config = ConfigDict(from_attributes=True)

# --- Product ---
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float
    category_id: Optional[int] = None
    season: Optional[str] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    category_id: Optional[int] = None
    season: Optional[str] = None
    image_url: Optional[str] = None

class Product(ProductBase):
    id: int
    category: Optional[Category] = None
    variants: List[ProductVariant] = []
    model_config = ConfigDict(from_attributes=True)
