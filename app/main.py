"""Main application module for the Transaction API."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routes import transactions
from app.utils.errors import handle_exceptions
from app.config.settings import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Dynamic Transaction API",
    description="API for querying transaction data with flexible query parameters",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transactions.router)

# Add exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return handle_exceptions(exc)

# API documentation customization
@app.get("/")
async def api_root():
    """Root endpoint showing API information and examples."""
    return {
        "message": "Transaction API",
        "documentation": "/docs",
        "examples": [
            "/api/v1/transactions?type=1&year=gte:2020&groupBy=companyName&orderBy=count:desc&limit=10",
            "/api/v1/transactions?type=14&year=2021&country=131&orderBy=size:desc&limit=5",
            "/api/v1/transactions?industry=32,34&country=37&year=2023&orderBy=year:desc,month:desc,day:desc",
            "/api/v1/transactions/summary/2023?country=37&type=2",
            "/api/v1/transactions/aggregate?groupBy=industry&measure=sum&field=transactionSize&type=14&year=2022"
        ]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)