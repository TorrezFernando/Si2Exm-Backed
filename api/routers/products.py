from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.deps import get_db, require_permission, get_current_active_user
from db.models.product import Product, Category, ProductVariant
from db.models.user import User
from schemas.product import (
    Product as ProductSchema,
    ProductCreate,
    ProductUpdate,
    Category as CategorySchema
)

router = APIRouter()

# --- CATEGORIES ---

@router.get("/categories", response_model=List[CategorySchema])
def list_categories(
    db: Session = Depends(get_db)
) -> Any:
    """Lista todas las categorías disponibles."""
    return db.query(Category).all()

# --- PRODUCTS ---

@router.get("/", response_model=List[ProductSchema])
def list_products(
    db: Session = Depends(get_db),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    season: Optional[str] = Query(None, description="Filtrar por temporada"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
) -> Any:
    """Lista productos (Catálogo). Accesible públicamente o requiere auth según diseño."""
    query = db.query(Product)
    
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if season:
        query = query.filter(Product.season == season)
        
    return query.offset(skip).limit(limit).all()

@router.get("/{product_id}", response_model=ProductSchema)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """Obtiene un producto por su ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
def create_product(
    *,
    db: Session = Depends(get_db),
    product_in: ProductCreate,
    current_user: User = Depends(require_permission("catalog:write"))
) -> Any:
    """Crea un nuevo producto (Admin/Encargado)."""
    if product_in.category_id:
        category = db.query(Category).filter(Category.id == product_in.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
            
    product = Product(
        name=product_in.name,
        description=product_in.description,
        base_price=product_in.base_price,
        category_id=product_in.category_id,
        season=product_in.season,
        image_url=product_in.image_url
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.patch("/{product_id}", response_model=ProductSchema)
def update_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    product_in: ProductUpdate,
    current_user: User = Depends(require_permission("catalog:write"))
) -> Any:
    """Actualiza un producto (Admin/Encargado)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    if product_in.category_id is not None:
        category = db.query(Category).filter(Category.id == product_in.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
            
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
        
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}", response_model=ProductSchema)
def delete_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    current_user: User = Depends(require_permission("catalog:write"))
) -> Any:
    """Elimina un producto (Admin/Encargado)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    db.delete(product)
    db.commit()
    return product
