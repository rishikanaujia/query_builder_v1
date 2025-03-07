"""Pydantic models for request/response schemas."""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class EndpointInfo(BaseModel):
    """Information about an API endpoint."""
    id: str
    name: str
    description: str


class EndpointSchema(BaseModel):
    """Schema information for an API endpoint."""
    id: str
    name: str
    description: str
    required_params: List[str]
    allowed_params: List[str]


class QueryParams(BaseModel):
    """Internal representation of query parameters."""
    select: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    joins: Optional[List[str]] = None
    group_by: Optional[List[str]] = None
    order_by: Optional[Dict[str, str]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class TransactionQueryParams(BaseModel):
    """Query parameters for transaction endpoint."""
    type: Optional[str] = None
    year: Optional[str] = None
    month: Optional[str] = None
    day: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    company: Optional[str] = None
    companyName: Optional[str] = None
    size: Optional[str] = None
    select: Optional[str] = None
    groupBy: Optional[str] = None
    orderBy: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str


class TransactionSummary(BaseModel):
    """Summary of transaction data."""
    year: int
    totalTransactions: int
    totalValue: Optional[float] = None
    averageValue: Optional[float] = None
    minValue: Optional[float] = None
    maxValue: Optional[float] = None
    uniqueCompanies: Optional[int] = None


class TransactionDetail(BaseModel):
    """Detailed transaction information."""
    transactionId: str
    companyName: Optional[str] = None
    announcedYear: Optional[int] = None
    announcedMonth: Optional[int] = None
    announcedDay: Optional[int] = None
    transactionSize: Optional[float] = None
    transactionIdTypeName: Optional[str] = None
    statusId: Optional[int] = None
    currencyId: Optional[str] = None

    class Config:
        """Pydantic config."""
        orm_mode = True


class TransactionListResponse(BaseModel):
    """Response model for transaction list endpoint."""
    data: List[Dict[str, Any]]
    count: int
    metadata: Optional[Dict[str, Any]] = None