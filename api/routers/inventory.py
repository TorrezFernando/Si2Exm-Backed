from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from db.models.branch import Inventory
from schemas.product import InventorySchema

router = APIRouter()

@router.get("/variant/{variant_id}", response_model=List[InventorySchema])
def get_inventory_by_variant(variant_id: int, db: Session = Depends(get_db)):
    """
    Obtener el inventario (stock en sucursales) de una variante específica.
    """
    inventories = db.query(Inventory).filter(Inventory.variant_id == variant_id).all()
    # Si no hay inventario (0 o vacío) se devuelve lista vacía, no 404, para que la UI lo maneje.
    return inventories

@router.get("/branch/{branch_id}", response_model=List[InventorySchema])
def get_inventory_by_branch(branch_id: int, db: Session = Depends(get_db)):
    """
    Obtener todo el inventario de una sucursal.
    """
    inventories = db.query(Inventory).filter(Inventory.branch_id == branch_id).all()
    return inventories
