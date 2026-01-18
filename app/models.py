"""
Database models for Contact API
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from .database import Base


class Inquiry(Base):
    """Inquiry model for storing contact form submissions"""
    __tablename__ = "inquiries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    line_user_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Inquiry(id={self.id}, name={self.name}, category={self.category})>"
