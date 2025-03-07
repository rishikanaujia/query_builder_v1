"""Snowflake database connection management."""
from contextlib import contextmanager
import logging
from typing import List, Dict, Any
import snowflake.connector
from snowflake.connector.connection import SnowflakeConnection
from snowflake.connector.errors import ProgrammingError
from fastapi import HTTPException
from app.config.settings import settings

# Setup logging
logger = logging.getLogger(__name__)

def get_snowflake_connection() -> SnowflakeConnection:
    """Create and return a Snowflake connection."""
    try:
        conn = snowflake.connector.connect(
            user=settings.SNOWFLAKE_USER,
            password=settings.SNOWFLAKE_PASSWORD,
            account=settings.SNOWFLAKE_ACCOUNT,
            warehouse=settings.SNOWFLAKE_WAREHOUSE,
            database=settings.SNOWFLAKE_DATABASE,
            schema=settings.SNOWFLAKE_SCHEMA
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to Snowflake: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@contextmanager
def snowflake_cursor():
    """Context manager for getting a Snowflake cursor that automatically handles connection cleanup."""
    conn = None
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor(snowflake.connector.DictCursor)
        yield cursor
    except ProgrammingError as e:
        logger.error(f"Snowflake programming error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"SQL query error: {str(e)}")
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

def execute_query(sql_query: str) -> List[Dict[str, Any]]:
    """Execute a SQL query and return the results."""
    with snowflake_cursor() as cursor:
        logger.info(f"Executing SQL query: {sql_query}")
        cursor.execute(sql_query)
        results = cursor.fetchall()
        return [dict(row) for row in results]