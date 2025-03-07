"""API routes for transaction endpoints."""
from typing import Dict, List, Any, Optional, Union
from fastapi import APIRouter, Query, Path, HTTPException, Depends
from pydantic import BaseModel

from app.services.transaction_service import TransactionService
from app.models.schemas import TransactionQueryParams
from app.config.settings import settings
from app.utils.errors import QueryBuildError, DatabaseError

# Create router
router = APIRouter(
    prefix=f"{settings.API_PREFIX}",
    tags=["transactions"],
    responses={
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"}
    }
)


class TransactionResponse(BaseModel):
    """Response model for transaction data."""
    data: List[Dict[str, Any]]
    count: int
    metadata: Optional[Dict[str, Any]] = None


@router.get("/transactions", response_model=TransactionResponse)
def get_transactions(
        # Core filters
        type: Optional[str] = Query(None,
                                    description="Transaction type ID or comma-separated list. Use operators gte:, lte:, gt:, lt:, ne:"),
        year: Optional[str] = Query(None,
                                    description="Announced year. Use operators gte:, lte:, gt:, lt:, ne: or between:start,end"),
        month: Optional[str] = Query(None, description="Announced month (1-12). Use operators for ranges."),
        day: Optional[str] = Query(None, description="Announced day. Use operators for ranges."),

        # Company and geography filters
        country: Optional[str] = Query(None, description="Country ID or comma-separated list"),
        industry: Optional[str] = Query(None, description="Industry ID or comma-separated list"),
        company: Optional[str] = Query(None, description="Company name filter. Use like: for partial matching"),
        companyId: Optional[str] = Query(None, description="Company ID"),

        # Transaction details
        size: Optional[str] = Query(None, description="Transaction size. Use operators for ranges."),
        status: Optional[str] = Query(None, description="Status ID or comma-separated list"),
        currency: Optional[str] = Query(None, description="Currency ID"),

        # Relationship filters
        acquirerId: Optional[str] = Query(None, description="Acquirer company ID"),
        targetId: Optional[str] = Query(None, description="Target company ID"),
        sellerId: Optional[str] = Query(None, description="Seller company ID"),
        investorId: Optional[str] = Query(None, description="Investor company ID"),
        advisorId: Optional[str] = Query(None, description="Advisor company ID"),
        relationType: Optional[str] = Query(None, description="Relationship type ID"),
        leadInvestor: Optional[str] = Query(None, description="Lead investor flag (0 or 1)"),

        # Complex filtering
        or_: Optional[str] = Query(None, alias="or",
                                   description="OR condition formatted as field1=value1;field2=value2"),

        # Query structure
        select: Optional[str] = Query(None, description="Fields to select, comma-separated"),
        groupBy: Optional[str] = Query(None, description="Fields to group by, comma-separated"),
        orderBy: Optional[str] = Query(None,
                                       description="Fields to order by with direction, comma-separated (field:asc/desc)"),
        limit: Optional[int] = Query(None, description="Maximum number of records to return"),
        offset: Optional[int] = Query(None, description="Number of records to skip"),

        # Special queries
        pattern: Optional[str] = Query(None, description="Predefined query pattern (e.g., ma_transactions, buybacks)"),
        count_only: Optional[bool] = Query(False, description="Return only the count of matching records"),
        include_metadata: Optional[bool] = Query(False, description="Include metadata about the query"),
        format: Optional[str] = Query(None, description="Response format (csv, json)")
):
    """
    Flexible transaction endpoint that supports various query parameters for filtering, aggregation, and formatting.

    **Filter Fields**:
    - **type**: Transaction type ID (1=Private Placement, 2=M&A, 3=IPO, 4=Secondary Offering, 5=Buyout, 14=Buyback)
    - **year**, **month**, **day**: Date filters for announced date
    - **country**: Country ID filter
    - **industry**: Industry ID filter
    - **company**, **companyId**: Company name or ID filters
    - **size**: Transaction size filter
    - **status**: Transaction status filter
    - **currency**: Currency ID filter

    **Relationship Filters**:
    - **acquirerId**, **targetId**, **sellerId**, **investorId**, **advisorId**: Company role filters
    - **relationType**: Relationship type filter
    - **leadInvestor**: Lead investor flag filter

    **Special Operators**:
    - Use **gte:value** for greater than or equal
    - Use **lte:value** for less than or equal
    - Use **gt:value** for greater than
    - Use **lt:value** for less than
    - Use **ne:value** for not equal
    - Use **like:value** for pattern matching
    - Use **between:start,end** for range filters
    - Use comma-separated values for IN clause

    **Query Structure**:
    - **select**: Comma-separated list of fields to include
    - **groupBy**: Comma-separated list of fields to group by
    - **orderBy**: Comma-separated list of fields to order by (field:asc or field:desc)
    - **limit**: Maximum number of records
    - **offset**: Number of records to skip
    - **or**: Semicolon-separated list of OR conditions (field1=value1;field2=value2)

    **Special Queries**:
    - **pattern**: Use predefined query patterns
    - **count_only**: Return only the count of matching records
    - **include_metadata**: Include query metadata in the response
    - **format**: Response format (default is JSON)

    **Examples**:
    ```
    /api/v1/transactions?type=1&year=gte:2020&groupBy=companyName&orderBy=count:desc&limit=10
    /api/v1/transactions?type=14&year=2021&country=131&orderBy=size:desc&limit=5
    /api/v1/transactions?industry=32,34&country=37&year=2023&orderBy=year:desc,month:desc,day:desc
    /api/v1/transactions?type=2&acquirerId=21835&year=gt:2017
    /api/v1/transactions?pattern=ma_transactions&targetId=24937&or=acquirerId=24937
    /api/v1/transactions?type=14&year=2022&country=37&select=COUNT(DISTINCT(si.simpleindustrydescription))&count_only=true
    ```
    """
    # Collect all provided parameters
    params = {}

    # Add core filters
    if type is not None: params['type'] = type
    if year is not None: params['year'] = year
    if month is not None: params['month'] = month
    if day is not None: params['day'] = day

    # Add company and geography filters
    if country is not None: params['country'] = country
    if industry is not None: params['industry'] = industry
    if company is not None: params['company'] = company
    if companyId is not None: params['companyId'] = companyId

    # Add transaction details
    if size is not None: params['size'] = size
    if status is not None: params['status'] = status
    if currency is not None: params['currency'] = currency

    # Add relationship filters
    if acquirerId is not None: params['acquirerId'] = acquirerId
    if targetId is not None: params['targetId'] = targetId
    if sellerId is not None: params['sellerId'] = sellerId
    if investorId is not None: params['investorId'] = investorId
    if advisorId is not None: params['advisorId'] = advisorId
    if relationType is not None: params['relationType'] = relationType
    if leadInvestor is not None: params['leadInvestor'] = leadInvestor

    # Add complex filtering
    if or_ is not None: params['or'] = or_

    # Add query structure
    if select is not None: params['select'] = select
    if groupBy is not None: params['groupBy'] = groupBy
    if orderBy is not None: params['orderBy'] = orderBy
    if limit is not None: params['limit'] = str(limit)
    if offset is not None: params['offset'] = str(offset)

    # Add special query parameters
    if pattern is not None: params['pattern'] = pattern
    if count_only: params['count_only'] = 'true'
    if include_metadata: params['include_metadata'] = 'true'
    if format is not None: params['format'] = format

    try:
        # Process request through service
        result = TransactionService.get_transactions(params)

        # For CSV format return directly
        if format == 'csv':
            # Implementation for CSV response would go here
            pass

        # Build standard response structure
        if isinstance(result, dict) and 'data' in result and 'count' in result:
            # Service already returned proper structure
            return result
        elif count_only:
            # Only return count for count_only requests
            count = len(result) if isinstance(result, list) else 0
            if result and isinstance(result[0], dict) and 'count' in result[0]:
                count = result[0]['count']
            return {"data": [], "count": count, "metadata": None}
        else:
            # Default structure
            metadata = None
            if include_metadata:
                metadata = {
                    "query_params": params,
                    "result_count": len(result) if isinstance(result, list) else 0
                }
            return {"data": result, "count": len(result) if isinstance(result, list) else 0, "metadata": metadata}

    except QueryBuildError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{transaction_id}", response_model=Dict[str, Any])
def get_transaction_by_id(
        transaction_id: str = Path(..., description="The ID of the transaction to retrieve"),
        include_relationships: bool = Query(False, description="Include relationship data"),
        include_advisors: bool = Query(False, description="Include advisor data")
):
    """
    Get a specific transaction by its ID with optional relationship and advisor data.

    Parameters:
    - **transaction_id**: Unique identifier for the transaction
    - **include_relationships**: Whether to include company relationship data
    - **include_advisors**: Whether to include advisor data

    Returns detailed information about the specified transaction.
    """
    try:
        params = {
            "transaction_id": transaction_id,
            "include_relationships": include_relationships,
            "include_advisors": include_advisors
        }
        return TransactionService.get_transaction_by_id(transaction_id, params)
    except QueryBuildError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/summary/{year}", response_model=Dict[str, Any])
def get_transaction_summary(
        year: int = Path(..., description="The year to summarize"),
        country: Optional[str] = Query(None, description="Optional country filter"),
        industry: Optional[str] = Query(None, description="Optional industry filter"),
        type: Optional[str] = Query(None, description="Optional transaction type filter")
):
    """
    Get a summary of transactions for a specific year with optional filters.

    Parameters:
    - **year**: The year to summarize
    - **country**: Optional country ID to filter by
    - **industry**: Optional industry ID to filter by
    - **type**: Optional transaction type ID to filter by

    Returns aggregate statistics including count, total value, average value, etc.
    """
    try:
        params = {
            "year": year
        }
        if country:
            params["country"] = country
        if industry:
            params["industry"] = industry
        if type:
            params["type"] = type

        return TransactionService.get_transaction_summary(year, params)
    except QueryBuildError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/aggregate", response_model=List[Dict[str, Any]])
def get_transaction_aggregate(
        groupBy: str = Query(..., description="Field to group by (industry, country, type, year, month)"),
        measure: str = Query(..., description="Measure to calculate (count, sum, avg, min, max)"),
        field: Optional[str] = Query("transactionSize", description="Field to measure"),
        type: Optional[str] = Query(None, description="Transaction type filter"),
        year: Optional[str] = Query(None, description="Year filter"),
        country: Optional[str] = Query(None, description="Country filter"),
        industry: Optional[str] = Query(None, description="Industry filter"),
        limit: Optional[int] = Query(10, description="Limit results")
):
    """
    Get aggregated transaction data grouped by a specific field.

    Parameters:
    - **groupBy**: Field to group by (industry, country, type, year, month)
    - **measure**: Measure to calculate (count, sum, avg, min, max)
    - **field**: Field to measure (default: transactionSize)
    - **type**, **year**, **country**, **industry**: Optional filters
    - **limit**: Maximum number of results to return

    Examples:
    ```
    /api/v1/transactions/aggregate?groupBy=industry&measure=sum&field=transactionSize&type=14&year=2022
    /api/v1/transactions/aggregate?groupBy=country&measure=count&type=2&year=gte:2020
    ```
    """
    try:
        # Build parameters
        params = {
            "select": f"{groupBy}, {measure.upper()}({field}) AS value",
            "groupBy": groupBy,
            "orderBy": "value:desc"
        }

        # Add filters
        if type is not None: params['type'] = type
        if year is not None: params['year'] = year
        if country is not None: params['country'] = country
        if industry is not None: params['industry'] = industry
        if limit is not None: params['limit'] = str(limit)

        # Process request through service
        result = TransactionService.get_transactions(params)
        return result
    except QueryBuildError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/distinct/{field}", response_model=List[Dict[str, Any]])
def get_distinct_values(
        field: str = Path(..., description="Field to get distinct values for"),
        type: Optional[str] = Query(None, description="Transaction type filter"),
        year: Optional[str] = Query(None, description="Year filter"),
        country: Optional[str] = Query(None, description="Country filter"),
        industry: Optional[str] = Query(None, description="Industry filter"),
        limit: Optional[int] = Query(100, description="Limit results")
):
    """
    Get distinct values for a specified field with optional filters.

    Parameters:
    - **field**: Field to get distinct values for
    - **type**, **year**, **country**, **industry**: Optional filters
    - **limit**: Maximum number of results to return

    Examples:
    ```
    /api/v1/transactions/distinct/country?type=2&year=2023
    /api/v1/transactions/distinct/industry?type=14
    ```
    """
    try:
        # Map field names to database fields
        field_mapping = {
            "industry": "si.simpleIndustryDescription",
            "country": "geo.country",
            "type": "tt.transactionIdTypeName",
            "year": "tr.announcedYear",
            "month": "tr.announcedMonth",
            "company": "c.companyName",
            "status": "ts.statusName"
        }

        db_field = field_mapping.get(field, field)

        # Build parameters
        params = {
            "select": f"DISTINCT({db_field}) AS value",
            "orderBy": "value:asc"
        }

        # Add filters
        if type is not None: params['type'] = type
        if year is not None: params['year'] = year
        if country is not None: params['country'] = country
        if industry is not None: params['industry'] = industry
        if limit is not None: params['limit'] = str(limit)

        # Process request through service
        result = TransactionService.get_transactions(params)
        return result
    except QueryBuildError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))