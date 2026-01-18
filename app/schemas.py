"""
Pydantic schemas for request/response validation
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class InquiryCreate(BaseModel):
    """Schema for creating a new inquiry"""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the inquirer")
    email: EmailStr = Field(..., description="Email address")
    category: str = Field(..., min_length=1, max_length=50, description="Inquiry category")
    message: str = Field(..., min_length=10, max_length=4000, description="Inquiry message")
    idToken: Optional[str] = Field(None, description="LINE ID token for verification")


class InquiryResponse(BaseModel):
    """Schema for inquiry response"""
    ok: bool
    message: str


class InquiryDetail(BaseModel):
    """Schema for inquiry detail"""
    id: int
    name: str
    email: str
    category: str
    message: str
    line_user_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
