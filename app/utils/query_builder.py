"""Flexible SQL query builder for transaction API."""
from typing import Dict, List, Any, Optional, Tuple, Set
import logging
import re

from app.constants import (
    TRANSACTION_TYPES,
    RELATIONSHIP_TYPES,
    JOIN_REQUIREMENTS,
    DEFAULT_INCLUDED_STATUSES
)
from app.constants.joins import ALL_JOIN_PATHS
from app.utils.constants import (
    TABLE_MAPPINGS,
    FIELD_MAPPINGS,
    JOIN_PATHS,
    FILTER_OPERATORS,
    SQL_FUNCTIONS,
    QUERY_PATTERNS
)
from app.utils.errors import QueryBuildError

# Setup logging
logger = logging.getLogger(__name__)


class FlexibleQueryBuilder:
    """Dynamic SQL query builder that supports flexible parameters."""

    def __init__(self, schema: str, base_table: str = "ciqTransaction", base_alias: str = "tr"):
        """Initialize the query builder with schema and base table information."""
        self.schema = schema
        self.base_table = base_table
        self.base_alias = base_alias
        self.select_fields = []
        self.where_conditions = []
        self.group_by_fields = []
        self.order_by_clauses = []
        self.limit_value = None
        self.offset_value = None

        # Store all joins that need to be made
        self.joins = []

        # Track which aliases are in use
        self.used_aliases = set()

        # Track field prefixes
        self.field_prefixes = {}

        # Track query pattern
        self.detected_pattern = None

        # Track OR conditions
        self.or_conditions = []

        # Track special SQL constructs
        self.has_window_function = False
        self.has_distinct = False

    def parse_request_params(self, params: Dict[str, str]) -> None:
        """Parse request parameters into SQL query components."""
        try:
            # Process each parameter
            for key, value in params.items():
                if key == "select":
                    self._process_select(value)
                elif key == "groupBy":
                    self._process_group_by(value)
                elif key == "orderBy":
                    self._process_order_by(value)
                elif key == "limit":
                    self.limit_value = int(value)
                elif key == "offset":
                    self.offset_value = int(value)
                elif key == "or":
                    self._process_or_condition(value)
                elif key == "pattern":
                    # Set detected pattern directly
                    self.detected_pattern = value
                elif key in ALL_JOIN_PATHS or key in self._get_field_keys():
                    self._process_filter(key, value)

            # If no select fields specified, use * as default
            if not self.select_fields:
                self.select_fields = ["tr.*"]

            # Try to detect query pattern if not explicitly set
            if not self.detected_pattern:
                self._detect_query_pattern()

            # Add joins based on field usage
            self._analyze_field_usage()

            # Add or conditions to where conditions if any
            if self.or_conditions:
                self.where_conditions.append(f"({' OR '.join(self.or_conditions)})")

            # Add default status filter if not specified
            self._add_default_status_filter()

        except ValueError as e:
            # Handle numeric conversion errors
            raise QueryBuildError(f"Invalid numeric value: {str(e)}")
        except Exception as e:
            # Handle other parsing errors
            logger.error(f"Error parsing parameters: {e}", exc_info=True)
            raise QueryBuildError(f"Error parsing query parameters: {str(e)}")

    def _get_field_keys(self):
        """Get all field keys that can be used in parameters."""
        # Collect field mappings from all constant files
        field_keys = set()

        # Add transaction fields
        field_keys.update(["type", "year", "month", "day", "size", "status", "currency"])

        # Add company fields
        field_keys.update(["company", "companyName", "companyId", "industry", "country"])

        # Add relationship fields
        field_keys.update(["acquirerId", "targetId", "sellerId", "investorId", "advisorId",
                           "relationType", "leadInvestor", "individualEquity", "percentAcquired"])

        # Add all fields from FIELD_MAPPINGS
        field_keys.update(FIELD_MAPPINGS.keys())

        return field_keys

    def _process_select(self, value: str) -> None:
        """Process select parameter."""
        fields = value.split(',')
        for field in fields:
            field = field.strip()

            # Check for window functions
            if "OVER" in field.upper():
                self.has_window_function = True
                self.select_fields.append(field)
                # Extract field reference from window function
                match = re.search(r'\((.*?)\)', field)
                if match:
                    field_ref = match.group(1)
                    self._check_field_for_join(field_ref)
                continue

            # Check for DISTINCT
            if "DISTINCT" in field.upper():
                self.has_distinct = True
                # Handle COUNT(DISTINCT())
                if field.upper().startswith("COUNT(DISTINCT("):
                    match = re.search(r'COUNT\(DISTINCT\((.*?)\)\)', field, re.IGNORECASE)
                    if match:
                        inner_field = match.group(1)
                        self._check_field_for_join(inner_field)
                        self.select_fields.append(field)
                    continue
                # Handle DISTINCT()
                match = re.search(r'DISTINCT\((.*?)\)', field, re.IGNORECASE)
                if match:
                    inner_field = match.group(1)
                    self._check_field_for_join(inner_field)
                    self.select_fields.append(field)
                continue

            # Check for aggregate functions
            for func in ["COUNT", "SUM", "AVG", "MIN", "MAX"]:
                if field.upper().startswith(f"{func}("):
                    match = re.search(f'{func}\\((.*?)\\)', field, re.IGNORECASE)
                    if match:
                        inner_field = match.group(1)
                        self._check_field_for_join(inner_field)
                        self.select_fields.append(field)
                    continue

            # Map field if needed
            mapped_field = self._map_field_name(field)
            self.select_fields.append(mapped_field)
            self._check_field_for_join(mapped_field)

    def _process_group_by(self, value: str) -> None:
        """Process groupBy parameter."""
        fields = value.split(',')
        for field in fields:
            field = field.strip()
            # Map field name
            mapped_field = self._map_field_name(field)

            # Add to select if not already there
            if mapped_field not in self.select_fields:
                self.select_fields.append(mapped_field)

            self.group_by_fields.append(mapped_field)
            self._check_field_for_join(mapped_field)

    def _process_order_by(self, value: str) -> None:
        """Process orderBy parameter."""
        fields = value.split(',')
        for field in fields:
            field = field.strip()
            if ':' in field:
                field_name, direction = field.split(':')
                field_name = field_name.strip()
                direction = direction.strip().upper()

                # Map field name
                mapped_field = self._map_field_name(field_name)

                self.order_by_clauses.append(f"{mapped_field} {direction}")
                self._check_field_for_join(mapped_field)
            else:
                # Default to ASC if no direction specified
                field_name = field.strip()

                # Map field name
                mapped_field = self._map_field_name(field_name)

                self.order_by_clauses.append(f"{mapped_field} ASC")
                self._check_field_for_join(mapped_field)

    def _process_or_condition(self, value: str) -> None:
        """Process OR condition parameter."""
        # Format: field1=value1;field2=value2
        conditions = value.split(';')
        for condition in conditions:
            if '=' in condition:
                field, val = condition.split('=', 1)
                field = field.strip()
                val = val.strip()

                # Map field name
                mapped_field = self._map_field_name(field)

                # Add to OR conditions
                self.or_conditions.append(f"{mapped_field} = '{val}'")

                # Check for joins
                self._check_field_for_join(mapped_field)

    def _process_filter(self, key: str, value: str) -> None:
        """Process filter parameter."""
        # Handle special field mappings
        field_name = self._map_field_name(key)

        # Check for operators
        for op_prefix, sql_op in FILTER_OPERATORS.items():
            if isinstance(value, str) and value.startswith(f"{op_prefix}:"):
                filter_value = value[len(op_prefix) + 1:]

                # Special handling for BETWEEN
                if op_prefix == "between":
                    if "," in filter_value:
                        start, end = filter_value.split(",", 1)
                        self.where_conditions.append(f"{field_name} BETWEEN '{start.strip()}' AND '{end.strip()}'")
                    else:
                        # Invalid BETWEEN format
                        raise QueryBuildError(f"Invalid BETWEEN format: {filter_value}")
                # Special handling for NULL/NOT NULL
                elif op_prefix == "null":
                    self.where_conditions.append(f"{field_name} IS NULL")
                elif op_prefix == "notnull":
                    self.where_conditions.append(f"{field_name} IS NOT NULL")
                # Standard operator
                else:
                    self.where_conditions.append(f"{field_name} {sql_op} '{filter_value}'")

                # Add to join tables if needed
                self._check_field_for_join(field_name)
                return

        # Handle comma-separated values (IN clause)
        if isinstance(value, str) and ',' in value:
            values = [f"'{v.strip()}'" for v in value.split(',')]
            self.where_conditions.append(f"{field_name} IN ({', '.join(values)})")
        else:
            # Default to equality
            self.where_conditions.append(f"{field_name} = '{value}'")

        # Add to join tables if needed
        self._check_field_for_join(field_name)

    def _map_field_name(self, key: str) -> str:
        """Map a parameter key to a field name."""
        # First check if this is already a fully qualified field (contains a dot)
        if '.' in key:
            return key

        # Then check FIELD_MAPPINGS from constants
        if key in FIELD_MAPPINGS:
            return FIELD_MAPPINGS[key]

        # Then check the mappings used in the original code
        mappings = {
            # Transaction fields
            "type": "tr.transactionIdTypeId",
            "typeName": "tt.transactionIdTypeName",
            "year": "tr.announcedYear",
            "month": "tr.announcedMonth",
            "day": "tr.announcedDay",
            "size": "tr.transactionSize",
            "status": "tr.statusId",
            "currency": "tr.currencyId",

            # Company fields
            "company": "c.companyName",
            "companyName": "c.companyName",
            "companyId": "c.companyId",
            "industry": "si.simpleIndustryId",
            "country": "geo.countryId",

            # Relationship fields
            "acquirerId": "acquirer.companyId",
            "targetId": "target.companyId",
            "sellerId": "seller.companyId",
            "investorId": "investor.companyId",
            "advisorId": "advisor.companyId",
            "relationType": "crt.transactionToCompRelTypeId",
            "leadInvestor": "tcr.leadInvestorFlag",
            "individualEquity": "tcr.individualEquity",
            "percentAcquired": "tcr.percentAcquired",

            # Aggregate functions
            "count": "COUNT(tr.transactionId)"
        }

        return mappings.get(key, key)

    def _check_field_for_join(self, field: str) -> None:
        """Check if a field requires a join and add it to required joins."""
        # Extract the field prefix (table alias)
        match = re.match(r'([a-z]+)\.', field)
        if match:
            prefix = match.group(1)
            # Find which join this belongs to and add it
            self._add_join_for_prefix(prefix)

    def _add_join_for_prefix(self, prefix: str) -> None:
        """Add a join that provides the given prefix."""
        # Skip for base table alias
        if prefix == self.base_alias:
            return

        # Find all join paths that use this prefix - first in ALL_JOIN_PATHS
        matching_joins = []
        for join_key, join_info in ALL_JOIN_PATHS.items():
            if join_info['alias'] == prefix:
                matching_joins.append((join_key, join_info))

        # If not found in ALL_JOIN_PATHS, check JOIN_PATHS
        if not matching_joins:
            for join_key, join_info in JOIN_PATHS.items():
                if join_info['alias'] == prefix:
                    matching_joins.append((join_key, join_info))

        # If none found, nothing to do
        if not matching_joins:
            return

        # If we already have a join for this prefix, nothing to do
        if any(j['info']['alias'] == prefix for j in self.joins):
            return

        # Choose the most appropriate join for this prefix
        if matching_joins:
            join_key, join_info = matching_joins[0]
            self._add_join_with_dependencies(join_key)

    def _add_join_with_dependencies(self, join_key: str) -> None:
        """Add a join and all its dependencies."""
        # Skip if already added
        if join_key in [j['key'] for j in self.joins]:
            return

        # Get join info - first check ALL_JOIN_PATHS
        join_info = ALL_JOIN_PATHS.get(join_key)

        # If not found in ALL_JOIN_PATHS, check JOIN_PATHS
        if not join_info:
            join_info = JOIN_PATHS.get(join_key)

        if not join_info:
            return

        # Add dependencies first
        if 'requires' in join_info:
            for dep_key in join_info['requires']:
                self._add_join_with_dependencies(dep_key)

        # Add this join
        self.joins.append({
            'key': join_key,
            'info': join_info,
            'use_exact': join_key in ['company_reverse', 'target_industry', 'acquirer', 'target', 'seller', 'investor']
        })

    def _detect_query_pattern(self) -> None:
        """Detect which query pattern this might be."""
        params = self._get_query_params()

        # First check against QUERY_PATTERNS from utils.constants
        for pattern_name, pattern_info in QUERY_PATTERNS.items():
            if 'conditions' in pattern_info:
                matches = True
                for cond_key, cond_value in pattern_info['conditions'].items():
                    if cond_key not in params:
                        matches = False
                        break
                    if cond_value != '*' and params[cond_key] != cond_value:
                        matches = False
                        break
                if matches:
                    self.detected_pattern = pattern_name
                    return

        # Check for M&A transactions
        if 'type' in params and params['type'] == '2':
            self.detected_pattern = "ma_transactions"

        # Check for buybacks
        elif 'type' in params and params['type'] == '14':
            self.detected_pattern = "buybacks"

        # Check for private placements
        elif 'type' in params and params['type'] == '1':
            self.detected_pattern = "private_placements"

    def _analyze_field_usage(self) -> None:
        """Analyze field usage to determine required joins."""
        params = self._get_query_params()

        # Handle specific parameters that need special joins
        self._process_special_parameters(params)

        # Add joins based on detected pattern
        self._add_pattern_joins()

        # Add joins for any remaining fields
        self._add_field_based_joins()

    def _process_special_parameters(self, params: Dict[str, str]) -> None:
        """Process special parameters that need specific joins."""
        # Transaction type
        if 'type' in params:
            self._add_join_with_dependencies('transaction_type')

        # Status
        if 'status' in params:
            self._add_join_with_dependencies('transaction_status')

        # Company
        if 'company' in params or 'companyName' in params or 'companyId' in params:
            self._add_join_with_dependencies('company')

        # Industry
        if 'industry' in params:
            self._add_join_with_dependencies('industry')

        # Country
        if 'country' in params:
            self._add_join_with_dependencies('country')

        # Currency
        if 'currency' in params:
            self._add_join_with_dependencies('currency')

        # Relationship-specific parameters
        if 'acquirerId' in params:
            self._add_join_with_dependencies('transaction_company_rel')
            self._add_join_with_dependencies('comp_rel_type')
            self._add_join_with_dependencies('acquirer')

        if 'targetId' in params:
            self._add_join_with_dependencies('target')

        if 'sellerId' in params:
            self._add_join_with_dependencies('transaction_company_rel')
            self._add_join_with_dependencies('comp_rel_type')
            self._add_join_with_dependencies('seller')

        if 'investorId' in params:
            self._add_join_with_dependencies('transaction_company_rel')
            self._add_join_with_dependencies('comp_rel_type')
            self._add_join_with_dependencies('investor')

        if 'advisorId' in params:
            self._add_join_with_dependencies('transaction_to_advisor')
            self._add_join_with_dependencies('advisor_company')

    def _add_pattern_joins(self) -> None:
        """Add joins based on detected pattern."""
        # First check if pattern is in QUERY_PATTERNS
        if self.detected_pattern in QUERY_PATTERNS and 'recommended_joins' in QUERY_PATTERNS[self.detected_pattern]:
            for join_key in QUERY_PATTERNS[self.detected_pattern]['recommended_joins']:
                self._add_join_with_dependencies(join_key)

        # Then check specific patterns from original code
        elif self.detected_pattern == "ma_transactions":
            # Required joins for M&A transactions
            self._add_join_with_dependencies('transaction_type')
            self._add_join_with_dependencies('target')
            self._add_join_with_dependencies('transaction_company_rel')
            self._add_join_with_dependencies('comp_rel_type')
            self._add_join_with_dependencies('acquirer')

        elif self.detected_pattern == "buybacks":
            # Required joins for buybacks
            self._add_join_with_dependencies('transaction_type')
            self._add_join_with_dependencies('company')

        elif self.detected_pattern == "private_placements":
            # Required joins for private placements
            self._add_join_with_dependencies('transaction_type')
            self._add_join_with_dependencies('company')

    def _add_field_based_joins(self) -> None:
        """Add joins based on field references."""
        all_text = ' '.join(
            self.select_fields +
            self.where_conditions +
            self.group_by_fields +
            self.order_by_clauses
        )

        # Find all field prefixes used
        field_refs = re.findall(r'([a-z]+)\.([a-zA-Z_]+)', all_text)
        for prefix, _ in field_refs:
            if prefix != self.base_alias:
                self._add_join_for_prefix(prefix)

    def _add_default_status_filter(self) -> None:
        """Add default status filter if not specified."""
        # Check if status filter already exists
        has_status_filter = any('tr.statusId' in condition for condition in self.where_conditions)

        if not has_status_filter:
            # Create default status filter for active transactions
            status_values = ', '.join([str(s) for s in DEFAULT_INCLUDED_STATUSES])
            self.where_conditions.append(f"tr.statusId IN ({status_values})")

    def _get_query_params(self) -> Dict[str, str]:
        """Extract query parameters from where conditions."""
        params = {}
        for condition in self.where_conditions:
            # Parse equality conditions like "tr.transactionIdTypeId = '1'"
            match = re.match(r'([a-z]+\.[a-zA-Z_]+)\s*=\s*\'([^\']+)\'', condition)
            if match:
                field, value = match.groups()

                # Convert field to parameter name
                if field == 'tr.transactionIdTypeId':
                    params['type'] = value
                elif field == 'tr.announcedYear':
                    params['year'] = value
                elif field == 'tr.statusId':
                    params['status'] = value
                elif field == 'si.simpleIndustryId':
                    params['industry'] = value
                elif field == 'geo.countryId':
                    params['country'] = value
                # Add other field mappings as needed

            # Parse IN conditions like "si.simpleIndustryId IN ('32', '34')"
            match = re.match(r'([a-z]+\.[a-zA-Z_]+)\s+IN\s+\(([^\)]+)\)', condition)
            if match:
                field, values_str = match.groups()
                values = [v.strip().strip("'") for v in values_str.split(',')]

                # Convert field to parameter name
                if field == 'tr.transactionIdTypeId':
                    params['type'] = ','.join(values)
                elif field == 'tr.announcedYear':
                    params['year'] = ','.join(values)
                elif field == 'tr.statusId':
                    params['status'] = ','.join(values)
                elif field == 'si.simpleIndustryId':
                    params['industry'] = ','.join(values)
                elif field == 'geo.countryId':
                    params['country'] = ','.join(values)
                # Add other field mappings as needed

        return params

    def build_query(self) -> str:
        """Build the complete SQL query."""
        # Try to use specialized handlers if available
        try:
            from app.utils.query_handlers import get_handler_for_pattern

            # Check for pattern-specific handler
            handler = None

            # Check if we have a detected pattern
            if self.detected_pattern:
                handler = get_handler_for_pattern(self.detected_pattern)

            # Use the handler if we found one
            if handler:
                handler.set_schema(self.schema)
                query_parts = {
                    'select_fields': self.select_fields,
                    'where_conditions': self.where_conditions,
                    'group_by_fields': self.group_by_fields,
                    'order_by_clauses': self.order_by_clauses,
                    'limit_value': self.limit_value,
                    'offset_value': self.offset_value,
                    'base_table': self.base_table,
                    'base_alias': self.base_alias
                }
                return handler.build_query(self._get_query_params(), query_parts)
        except ImportError:
            # Fall back to standard query building if handlers aren't available
            logger.info("Specialized query handlers not available, using default query builder")

        # Standard query building if no handler was used
        # Build SELECT clause
        select_clause = f"SELECT {', '.join(self.select_fields)}"

        # Build FROM clause
        from_clause = f"FROM {self.schema}.{self.base_table} {self.base_alias}"

        # Build JOIN clause
        join_statements = []

        # Order joins - put company joins first if needed by other joins
        for join_item in self._order_joins():
            join_key = join_item['key']
            join_info = join_item['info']
            use_exact = join_item.get('use_exact', False)

            # Create join SQL
            join_statements.append(
                f"JOIN {self.schema}.{join_info['table']} {join_info['alias']} "
                f"ON {join_info['condition']}"
            )

        join_clause = " ".join(join_statements)

        # Build WHERE clause
        where_clause = ""
        if self.where_conditions:
            where_clause = f"WHERE {' AND '.join(self.where_conditions)}"

        # Build GROUP BY clause
        group_by_clause = ""
        if self.group_by_fields:
            group_by_clause = f"GROUP BY {', '.join(self.group_by_fields)}"

        # Build ORDER BY clause
        order_by_clause = ""
        if self.order_by_clauses:
            order_by_clause = f"ORDER BY {', '.join(self.order_by_clauses)}"

        # Build LIMIT and OFFSET clause
        limit_clause = ""
        if self.limit_value is not None:
            # For Snowflake compatibility, use LIMIT instead of FETCH FIRST
            limit_clause = f"LIMIT {self.limit_value}"
            if self.offset_value is not None:
                limit_clause += f" OFFSET {self.offset_value}"

        # Combine all clauses
        query_parts = [select_clause, from_clause]
        if join_clause:
            query_parts.append(join_clause)
        if where_clause:
            query_parts.append(where_clause)
        if group_by_clause:
            query_parts.append(group_by_clause)
        if order_by_clause:
            query_parts.append(order_by_clause)
        if limit_clause:
            query_parts.append(limit_clause)

        query = " ".join(query_parts)

        # Log the query for debugging
        logger.info(f"Generated query: {query}")

        return query

    def _order_joins(self) -> List[Dict[str, Any]]:
        """Order joins to ensure dependencies are met."""
        ordered_joins = []
        remaining_joins = self.joins.copy()

        # Create a map of dependencies
        deps_map = {}
        for join in self.joins:
            join_info = join['info']
            if 'requires' in join_info:
                deps_map[join['key']] = join_info['requires']
            else:
                deps_map[join['key']] = []

        # Topological sort
        while remaining_joins:
            # Find joins with no remaining dependencies
            ready_joins = [j for j in remaining_joins
                           if all(dep not in [r['key'] for r in remaining_joins]
                                  for dep in deps_map.get(j['key'], []))]

            if not ready_joins:
                # Circular dependency detected
                logger.warning("Circular dependency detected in joins. Breaking the cycle.")
                ready_joins = [remaining_joins[0]]

            # Add ready joins to ordered list
            for join in ready_joins:
                ordered_joins.append(join)
                remaining_joins.remove(join)

        return ordered_joins