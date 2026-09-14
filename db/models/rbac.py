from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from db.database import Base

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False) # e.g. "users:read", "audit:read"
    description = Column(String, nullable=True)

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    is_predefined = Column(Boolean, default=False, nullable=False) # Admin is immutable

    # Relation to permissions via role_permissions
    permissions = relationship("Permission", secondary="role_permissions", backref="roles")
    users = relationship("User", back_populates="role")

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

class UserPermission(Base):
    """Overrides for a specific user. is_granted=True adds the permission, False revokes it from the role."""
    __tablename__ = "user_permissions"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
    is_granted = Column(Boolean, nullable=False, default=True)

    permission = relationship("Permission")
    user = relationship("User", back_populates="user_permissions")
