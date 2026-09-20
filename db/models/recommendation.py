from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from db.database import Base

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    preferences_json = Column(Text, default="{}") # Almacena {"categories": {"Vestidos": 2}, "colors": {"Amarillo": 5}}

    user = relationship("User")
