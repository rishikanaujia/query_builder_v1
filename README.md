# Dynamic Transaction API

A flexible, powerful API for querying and analyzing transaction data with dynamic query parameters.

## Overview

This project provides a RESTful API for accessing and analyzing transaction data from a Snowflake database. It features a sophisticated query builder that allows for flexible, dynamic queries through URL parameters.

The API supports a wide range of operations including:
- Filtering transactions by various criteria (type, date, industry, country, etc.)
- Complex query operations (range filters, IN clauses, NOT NULL checks)
- Data aggregation (counting, summing, averaging)
- Grouping and ordering results
- Pagination

## Project Structure

```
project_root/
│
├── app/
│   ├── main.py                  # FastAPI application entry point
│   │
│   ├── constants/               # Constants for different aspects of the domain
│   │   ├── advisory_types.py
│   │   ├── company_relationships.py
│   │   ├── industries.py
│   │   ├── joins.py
│   │   ├── relationship_types.py
│   │   ├── transaction_statuses.py
│   │   └── transaction_types.py
│   │
│   ├── controllers/             # Request handling logic
│   │   └── transaction_controller.py
│   │
│   ├── database/                # Database connection management
│   │   └── connection.py
│   │
│   ├── models/                  # Pydantic schemas for request/response
│   │   └── schemas.py
│   │
│   ├── routes/                  # API route definitions
│   │   └── transactions.py
│   │
│   ├── services/                # Business logic layer
│   │   └── transaction_service.py
│   │
│   ├── utils/                   # Utility functions and helpers
│   │   ├── constants.py
│   │   ├── errors.py
│   │   └── query_builder.py
│   │
│   └── config/                  # Configuration settings
│       └── settings.py
```

## Key Features

### Flexible Query Builder

The heart of the system is a flexible query builder that can construct complex SQL queries based on URL parameters. It supports:

- Dynamic JOINs based on the fields being queried
- Automatic detection of query patterns (M&A, buybacks, private placements)
- Filtering with various operators (>=, <=, >, <, !=, LIKE, IN, BETWEEN)
- Aggregation functions (COUNT, SUM, AVG, MIN, MAX)
- SELECT, WHERE, GROUP BY, ORDER BY, LIMIT, and OFFSET clauses

### Transaction Types

The system handles various transaction types including:
- Private Placements
- M&A Transactions
- IPOs
- Secondary Offerings
- Buyouts
- Venture Capital/Private Equity
- Spin-offs/Split-offs
- Buybacks

### Relationship Management

The API can handle complex company relationships in transactions:
- Acquirer
- Target
- Seller
- Investor
- Advisor

## API Endpoints

### GET /api/v1/transactions

The main endpoint supporting flexible querying with parameters:

- Filter fields: `type`, `year`, `month`, `day`, `country`, `industry`, `company`, `size`
- Special operators: `gte:`, `lte:`, `gt:`, `lt:`, `ne:`, comma for IN
- Query structure: `select`, `groupBy`, `orderBy`, `limit`, `offset`

Examples:
```
/api/v1/transactions?type=1&year=gte:2020&groupBy=companyName&orderBy=count:desc&limit=10
/api/v1/transactions?type=14&year=2021&country=131&orderBy=size:desc&limit=5
/api/v1/transactions?industry=32,34&country=37&year=2023&orderBy=year:desc,month:desc,day:desc
```

### GET /api/v1/transactions/{transaction_id}

Get a specific transaction by its ID.

### GET /api/v1/transactions/summary/{year}

Get a summary of transactions for a specific year, with optional country filter.

## Setup

### Prerequisites

- Python 3.8+
- Snowflake account with appropriate access privileges
- Required Python packages (see requirements.txt)

### Configuration

Set the following environment variables:

```
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
API_PREFIX=/api/v1
```

### Running the Application

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

The API will be available at http://localhost:8000

## API Documentation

When the application is running, visit:
- OpenAPI documentation: http://localhost:8000/docs
- ReDoc alternative documentation: http://localhost:8000/redoc

## Error Handling

The API provides consistent error responses with appropriate HTTP status codes:
- 400: Bad Request (invalid parameters, query building errors)
- 404: Not Found (resource not found)
- 500: Internal Server Error (database errors, unhandled exceptions)

## License

[Your chosen license]