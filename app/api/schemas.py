"""Pydantic schemas for API request/response validation."""

from datetime import datetime, date
from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from decimal import Decimal


# Auth schemas
class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload."""
    email: Optional[str] = None


# Document schemas
class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    mime_type: str
    file_size: int
    status: str
    created_at: datetime


class DocumentResponse(BaseModel):
    """Schema for document details response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    mime_type: str
    file_size: int
    status: str
    error_message: Optional[str] = None
    raw_text: Optional[str] = None
    extracted_data: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


# Transaction schemas
class TransactionCreate(BaseModel):
    """Schema for creating a transaction."""
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    date: date
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    merchant: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    tax: Optional[Decimal] = Field(None, ge=0)
    is_expense: bool = True


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    merchant: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    tax: Optional[Decimal] = Field(None, ge=0)
    is_expense: Optional[bool] = None


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: Optional[int]
    category_id: Optional[int]
    document_id: Optional[int]
    date: date
    amount: Decimal
    currency: str
    merchant: Optional[str]
    description: Optional[str]
    tax: Optional[Decimal]
    is_expense: bool
    created_at: datetime
    updated_at: datetime


# Category schemas
class CategoryCreate(BaseModel):
    """Schema for creating a category."""
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[int] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=7)


class CategoryResponse(BaseModel):
    """Schema for category response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: Optional[int]
    icon: Optional[str]
    color: Optional[str]
    created_at: datetime


# Account schemas
class AccountCreate(BaseModel):
    """Schema for creating an account."""
    name: str = Field(..., min_length=1, max_length=255)
    account_type: str
    currency: str = Field(default="USD", max_length=3)
    balance: Decimal = Field(default=Decimal("0"))


class AccountResponse(BaseModel):
    """Schema for account response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    account_type: str
    currency: str
    balance: Decimal
    is_active: bool
    created_at: datetime


# Budget schemas
class BudgetCreate(BaseModel):
    """Schema for creating a budget."""
    category_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    period: str = Field(..., max_length=20)
    start_date: date
    end_date: Optional[date] = None


class BudgetResponse(BaseModel):
    """Schema for budget response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: Optional[int]
    name: str
    amount: Decimal
    currency: str
    period: str
    start_date: date
    end_date: Optional[date]
    is_active: bool
    created_at: datetime


# Analytics schemas
class AnalyticsSummary(BaseModel):
    """Schema for analytics summary."""
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal
    transactions_count: int
    period_start: date
    period_end: date


class CategorySummary(BaseModel):
    """Schema for category summary."""
    category_id: Optional[int]
    category_name: Optional[str]
    total: Decimal
    count: int
    percentage: float
