from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, require_permission
from db.models.branch import Branch
from schemas.branch import Branch as BranchSchema, BranchCreate, BranchUpdate

router = APIRouter()

@router.get("", response_model=List[BranchSchema])
def list_branches(
    db: Session = Depends(get_db),
    active_only: bool = True
) -> Any:
    """Lista sucursales. Si active_only es True, solo retorna las activas."""
    query = db.query(Branch)
    if active_only:
        query = query.filter(Branch.is_active == True)
    return query.all()

@router.get("/{branch_id}", response_model=BranchSchema)
def get_branch(
    branch_id: int,
    db: Session = Depends(get_db)
) -> Any:
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return branch

@router.post("", response_model=BranchSchema, status_code=status.HTTP_201_CREATED)
def create_branch(
    *,
    db: Session = Depends(get_db),
    branch_in: BranchCreate,
    current_user = Depends(require_permission("branches:write"))
) -> Any:
    """Crea una nueva sucursal (Solo Admin)."""
    branch = Branch(
        name=branch_in.name,
        address=branch_in.address,
        phone=branch_in.phone,
        is_active=branch_in.is_active
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch

@router.patch("/{branch_id}", response_model=BranchSchema)
def update_branch(
    *,
    db: Session = Depends(get_db),
    branch_id: int,
    branch_in: BranchUpdate,
    current_user = Depends(require_permission("branches:write"))
) -> Any:
    """Actualiza una sucursal (Solo Admin)."""
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
        
    update_data = branch_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(branch, field, value)
        
    db.commit()
    db.refresh(branch)
    return branch

@router.delete("/{branch_id}", response_model=BranchSchema)
def delete_branch(
    *,
    db: Session = Depends(get_db),
    branch_id: int,
    current_user = Depends(require_permission("branches:write"))
) -> Any:
    """Desactiva una sucursal (soft delete) (Solo Admin)."""
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
        
    branch.is_active = False
    db.commit()
    db.refresh(branch)
    return branch
