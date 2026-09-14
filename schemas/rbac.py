from typing import List, Optional
from pydantic import BaseModel

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionSchema(PermissionBase):
    id: int

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permission_ids: List[int] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None

class RoleSchema(RoleBase):
    id: int
    is_predefined: bool
    permissions: List[PermissionSchema]

    class Config:
        from_attributes = True

class UserPermissionSchema(BaseModel):
    permission: PermissionSchema
    is_granted: bool

    class Config:
        from_attributes = True
