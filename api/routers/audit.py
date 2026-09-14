from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_db, require_permission
from db.models.audit import AuditLog
from schemas.audit import AuditLogSchema

router = APIRouter()

@router.get("/", response_model=List[AuditLogSchema])
def get_audit_logs(
    db: Session = Depends(get_db),
    _ = Depends(require_permission("audit:read")),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
) -> Any:
    """
    Obtiene la bitácora de auditoría.
    Solo lectura de modificaciones realizadas en el sistema.
    """
    query = db.query(AuditLog)
    
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
        
    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
