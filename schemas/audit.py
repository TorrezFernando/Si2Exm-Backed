from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel

class AuditLogSchema(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    entity_type: str
    entity_id: Optional[str]
    details: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True
