"""Transaction service for handling business logic."""
from typing import Dict, List, Any, Optional
import logging
from app.controllers.transaction_controller import TransactionController
from app.utils.errors import DatabaseError, QueryBuildError

# Setup logging
logger = logging.getLogger(__name__)


class TransactionService:
    """Service for handling transaction-related operations."""

    @staticmethod
    def get_transactions(params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get transactions based on flexible query parameters."""
        try:
            # Special handling for count_only requests
            if 'count_only' in params and params['count_only'] == 'true':
                # Modify the select parameter to use COUNT
                if 'select' in params and 'DISTINCT' in params['select']:
                    # Keep the distinct clause
                    pass
                else:
                    params['select'] = 'COUNT(tr.transactionId) as count'

                # Remove unnecessary parameters for count
                if 'orderBy' in params:
                    del params['orderBy']

            # Special handling for pattern-based queries
            if 'pattern' in params:
                pattern = params['pattern']
                logger.info(f"Using predefined pattern: {pattern}")
                # Additional pattern-specific logic could be added here

            # Handle format parameter
            response_format = params.get('format', 'json')
            if 'format' in params:
                del params['format']  # Remove from query params

            # Execute the request through controller
            result = TransactionController.handle_request(params)

            # Add metadata if requested
            if 'include_metadata' in params and params['include_metadata'] == 'true':
                metadata = {
                    "query_parameters": params,
                    "result_count": len(result),
                }

                # Return with metadata wrapper
                return {
                    "data": result,
                    "count": len(result),
                    "metadata": metadata
                }

            # For CSV format, handle formatting in the service
            if response_format == 'csv':
                # Implement CSV formatting if needed
                pass

            # Standard JSON response
            return result

        except QueryBuildError as e:
            # Re-raise query building errors
            raise e
        except Exception as e:
            # Handle other errors
            logger.error(f"Error in transaction service: {str(e)}")
            raise DatabaseError(f"Error processing transaction request: {str(e)}")

    @staticmethod
    def get_transaction_by_id(transaction_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a specific transaction by ID."""
        try:
            # Delegate to controller
            return TransactionController.handle_transaction_by_id(transaction_id, params)
        except QueryBuildError as e:
            # Re-raise query building errors
            raise e
        except Exception as e:
            # Handle other errors
            logger.error(f"Error getting transaction by ID: {str(e)}")
            raise DatabaseError(f"Error retrieving transaction: {str(e)}")

    @staticmethod
    def get_transaction_summary(year: int, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a summary of transactions for a specific year and optional filters."""
        try:
            # Delegate to controller
            return TransactionController.handle_transaction_summary(year, params)
        except QueryBuildError as e:
            # Re-raise query building errors
            raise e
        except Exception as e:
            # Handle other errors
            logger.error(f"Error getting transaction summary: {str(e)}")
            raise DatabaseError(f"Error retrieving transaction summary: {str(e)}")

    @staticmethod
    def get_distinct_values(field: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get distinct values for a specific field."""
        try:
            # Delegate to controller
            return TransactionController.handle_distinct_values(field, params)
        except QueryBuildError as e:
            # Re-raise query building errors
            raise e
        except Exception as e:
            # Handle other errors
            logger.error(f"Error getting distinct values: {str(e)}")
            raise DatabaseError(f"Error retrieving distinct values: {str(e)}")

    @staticmethod
    def get_aggregate_data(params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get aggregated transaction data."""
        try:
            # Delegate to controller
            return TransactionController.handle_aggregate_query(params)
        except QueryBuildError as e:
            # Re-raise query building errors
            raise e
        except Exception as e:
            # Handle other errors
            logger.error(f"Error getting aggregate data: {str(e)}")
            raise DatabaseError(f"Error retrieving aggregate data: {str(e)}")