"""Transaction controller for handling transaction-related API requests."""
from typing import Dict, List, Any, Optional
import logging

from app.utils.query_builder import FlexibleQueryBuilder
from app.database.connection import execute_query
from app.config.settings import settings
from app.utils.errors import QueryBuildError, DatabaseError

# Setup logging
logger = logging.getLogger(__name__)


class TransactionController:
    """Controller for handling transaction API requests."""

    @staticmethod
    def handle_request(request_params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Handle a transaction API request with flexible parameters."""
        try:
            # Build query from request parameters
            query_builder = FlexibleQueryBuilder(settings.SNOWFLAKE_SCHEMA)
            query_builder.parse_request_params(request_params)
            sql_query = query_builder.build_query()

            logger.info(f"Generated SQL query: {sql_query}")

            # Execute query
            results = execute_query(sql_query)
            return results

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            if isinstance(e, QueryBuildError):
                raise
            raise DatabaseError(f"Request processing error: {str(e)}")

    @staticmethod
    def handle_transaction_by_id(transaction_id: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle a request to get a specific transaction by ID."""
        try:
            # Default params
            if params is None:
                params = {}

            include_relationships = params.get('include_relationships', False)
            include_advisors = params.get('include_advisors', False)

            # Start with base query
            query = f"""
            SELECT tr.*, c.companyName, tt.transactionIdTypeName
            FROM {settings.SNOWFLAKE_SCHEMA}.ciqTransaction tr
            LEFT JOIN {settings.SNOWFLAKE_SCHEMA}.ciqCompany c ON tr.companyId = c.companyId
            LEFT JOIN {settings.SNOWFLAKE_SCHEMA}.ciqTransactionType tt ON tr.transactionIdTypeId = tt.transactionIdTypeId
            WHERE tr.transactionId = '{transaction_id}'
            """

            # Execute base query first
            results = execute_query(query)
            if not results:
                raise QueryBuildError(f"Transaction with ID {transaction_id} not found")

            transaction = results[0]

            # Get relationships if requested
            if include_relationships:
                rel_query = f"""
                SELECT crt.transactionToCompanyRelType as relationshipType, 
                       c.companyId, c.companyName, tcr.leadInvestorFlag, 
                       tcr.individualEquity, tcr.percentAcquired
                FROM {settings.SNOWFLAKE_SCHEMA}.ciqTransactionToCompanyRel tcr
                JOIN {settings.SNOWFLAKE_SCHEMA}.ciqTransactionToCompRelType crt 
                  ON tcr.transactionToCompRelTypeId = crt.transactionToCompRelTypeId
                JOIN {settings.SNOWFLAKE_SCHEMA}.ciqCompany c 
                  ON tcr.companyRelId = c.companyId
                WHERE tcr.transactionId = '{transaction_id}'
                """
                rel_results = execute_query(rel_query)
                transaction['relationships'] = rel_results

            # Get advisors if requested
            if include_advisors:
                adv_query = f"""
                SELECT advtype.advisorTypeName, advisor.companyId, advisor.companyName
                FROM {settings.SNOWFLAKE_SCHEMA}.ciqTransactionToAdvisor tadv
                JOIN {settings.SNOWFLAKE_SCHEMA}.ciqAdvisorType advtype 
                  ON tadv.advisorTypeId = advtype.advisorTypeId
                JOIN {settings.SNOWFLAKE_SCHEMA}.ciqCompany advisor 
                  ON tadv.companyId = advisor.companyId
                WHERE tadv.transactionId = '{transaction_id}'
                """
                adv_results = execute_query(adv_query)
                transaction['advisors'] = adv_results

            return transaction

        except Exception as e:
            logger.error(f"Error getting transaction by ID: {str(e)}")
            if isinstance(e, QueryBuildError):
                raise
            raise DatabaseError(f"Error retrieving transaction: {str(e)}")

    @staticmethod
    def handle_transaction_summary(year: int, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle a request to get a summary of transactions for a specific year."""
        try:
            # Default params
            if params is None:
                params = {}

            # Build WHERE conditions
            where_conditions = [f"tr.announcedYear = {year}"]

            # Add optional filters
            if 'country' in params:
                where_conditions.append(f"c.countryId = '{params['country']}'")

            if 'industry' in params:
                where_conditions.append(f"c.simpleIndustryId = '{params['industry']}'")

            if 'type' in params:
                where_conditions.append(f"tr.transactionIdTypeId = '{params['type']}'")

            query = f"""
            SELECT 
                tr.announcedYear,
                COUNT(tr.transactionId) as totalTransactions,
                SUM(tr.transactionSize) as totalValue,
                AVG(tr.transactionSize) as averageValue,
                MIN(tr.transactionSize) as minValue,
                MAX(tr.transactionSize) as maxValue,
                COUNT(DISTINCT c.companyId) as uniqueCompanies
            FROM {settings.SNOWFLAKE_SCHEMA}.ciqTransaction tr
            JOIN {settings.SNOWFLAKE_SCHEMA}.ciqCompany c ON tr.companyId = c.companyId
            WHERE {" AND ".join(where_conditions)}
            GROUP BY tr.announcedYear
            """

            results = execute_query(query)
            if not results:
                raise QueryBuildError(f"No transaction data found for year {year}")

            return results[0]
        except Exception as e:
            logger.error(f"Error getting transaction summary: {str(e)}")
            if isinstance(e, QueryBuildError):
                raise
            raise DatabaseError(f"Error retrieving transaction summary: {str(e)}")

    @staticmethod
    def handle_distinct_values(field: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Handle a request to get distinct values for a specific field."""
        try:
            # Default params
            if params is None:
                params = {}

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

            # Build WHERE conditions
            where_conditions = []

            # Add optional filters
            if 'type' in params:
                where_conditions.append(f"tr.transactionIdTypeId = '{params['type']}'")

            if 'year' in params:
                where_conditions.append(f"tr.announcedYear = {params['year']}")

            if 'country' in params:
                where_conditions.append(f"geo.countryId = '{params['country']}'")

            if 'industry' in params:
                where_conditions.append(f"si.simpleIndustryId = '{params['industry']}'")

            # Create query builder for proper joins
            builder = FlexibleQueryBuilder(settings.SNOWFLAKE_SCHEMA)

            # Add our SELECT
            select_field = f"DISTINCT({db_field}) AS value"
            builder.select_fields = [select_field]

            # Add WHERE conditions
            builder.where_conditions = where_conditions

            # Add ORDER BY
            builder.order_by_clauses = ["value ASC"]

            # Add LIMIT if specified
            if 'limit' in params:
                builder.limit_value = int(params['limit'])

            # Analyze field usage to add required joins
            builder._check_field_for_join(db_field)
            builder._analyze_field_usage()

            # Build and execute query
            sql_query = builder.build_query()

            results = execute_query(sql_query)
            return results
        except Exception as e:
            logger.error(f"Error getting distinct values: {str(e)}")
            if isinstance(e, QueryBuildError):
                raise
            raise DatabaseError(f"Error retrieving distinct values: {str(e)}")

    @staticmethod
    def handle_aggregate_query(params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle a request for aggregated transaction data."""
        try:
            # Required parameters
            if 'groupBy' not in params or 'measure' not in params:
                raise QueryBuildError("groupBy and measure parameters are required")

            group_by = params['groupBy']
            measure = params['measure'].upper()
            field = params.get('field', 'transactionSize')

            # Map group_by to database field
            group_by_mapping = {
                "industry": "si.simpleIndustryDescription",
                "country": "geo.country",
                "type": "tt.transactionIdTypeName",
                "year": "tr.announcedYear",
                "month": "tr.announcedMonth"
            }

            group_by_field = group_by_mapping.get(group_by, group_by)

            # Map field to database field if needed
            field_mapping = {
                "size": "tr.transactionSize",
                "transactionSize": "tr.transactionSize",
                "count": "tr.transactionId"
            }

            db_field = field_mapping.get(field, field)

            # Build the aggregate measure
            if measure == "COUNT" and field == "transactions":
                aggregate = "COUNT(tr.transactionId)"
            else:
                aggregate = f"{measure}({db_field})"

            # Create query builder
            builder = FlexibleQueryBuilder(settings.SNOWFLAKE_SCHEMA)

            # Add our SELECT
            builder.select_fields = [f"{group_by_field} AS category", f"{aggregate} AS value"]

            # Add GROUP BY
            builder.group_by_fields = [group_by_field]

            # Add WHERE conditions
            where_conditions = []

            # Add filters
            for filter_key in ['type', 'year', 'country', 'industry']:
                if filter_key in params:
                    # Get the field name
                    field_name = builder._map_field_name(filter_key)
                    filter_value = params[filter_key]

                    # Handle operators
                    if ':' in filter_value:
                        op, value = filter_value.split(':', 1)
                        op_map = {"gte": ">=", "lte": "<=", "gt": ">", "lt": "<", "ne": "!="}
                        if op in op_map:
                            where_conditions.append(f"{field_name} {op_map[op]} '{value}'")
                    else:
                        where_conditions.append(f"{field_name} = '{filter_value}'")

            builder.where_conditions = where_conditions

            # Add ORDER BY
            builder.order_by_clauses = ["value DESC"]

            # Add LIMIT if specified
            if 'limit' in params:
                builder.limit_value = int(params['limit'])

            # Analyze field usage to add required joins
            builder._check_field_for_join(group_by_field)
            builder._check_field_for_join(db_field)
            builder._analyze_field_usage()

            # Build and execute query
            sql_query = builder.build_query()

            results = execute_query(sql_query)
            return results
        except Exception as e:
            logger.error(f"Error executing aggregate query: {str(e)}")
            if isinstance(e, QueryBuildError):
                raise
            raise DatabaseError(f"Error aggregating transaction data: {str(e)}")