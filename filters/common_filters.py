"""
Common pre-built filters for typical use cases
"""
from typing import List, Any, Union
from datetime import date, datetime
from .base import FilterQuery


class DateRangeFilter(FilterQuery):
    """
    Filter by date range

    Example:
        filter = DateRangeFilter('created_at', '2024-01-01', '2024-12-31')
        query = filter.build('orders')
        # SELECT * FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'
    """

    def __init__(self, date_column: str, start_date: Union[str, date, datetime],
                 end_date: Union[str, date, datetime], inclusive: bool = True):
        """
        Args:
            date_column: Column name containing date/timestamp
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            inclusive: Use BETWEEN (inclusive) vs < and > (exclusive)
        """
        self.date_column = date_column
        self.start_date = self._format_date(start_date)
        self.end_date = self._format_date(end_date)
        self.inclusive = inclusive

    def build(self, table_name: str, **params) -> str:
        schema = params.get('schema', 'public')

        if self.inclusive:
            condition = (f"{self.date_column} BETWEEN '{self.start_date}' "
                        f"AND '{self.end_date}'")
        else:
            condition = (f"{self.date_column} >= '{self.start_date}' "
                        f"AND {self.date_column} < '{self.end_date}'")

        return f"SELECT * FROM {schema}.{table_name} WHERE {condition}"

    @staticmethod
    def _format_date(d: Union[str, date, datetime]) -> str:
        """Format date for SQL"""
        if isinstance(d, str):
            return d
        elif isinstance(d, datetime):
            return d.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(d, date):
            return d.strftime('%Y-%m-%d')
        else:
            raise ValueError(f"Invalid date type: {type(d)}")

    def __str__(self):
        return f"DateRangeFilter({self.date_column}: {self.start_date} to {self.end_date})"


class ForeignKeyFilter(FilterQuery):
    """
    Filter by foreign key relationship

    Example:
        filter = ForeignKeyFilter('customer_id', [123, 456, 789])
        query = filter.build('orders')
        # SELECT * FROM orders WHERE customer_id IN (123, 456, 789)
    """

    def __init__(self, fk_column: str, fk_values: List[Any]):
        """
        Args:
            fk_column: Foreign key column name
            fk_values: List of foreign key values to include
        """
        self.fk_column = fk_column
        self.fk_values = fk_values

    def build(self, table_name: str, **params) -> str:
        schema = params.get('schema', 'public')

        if not self.fk_values:
            # No values = select nothing
            return f"SELECT * FROM {schema}.{table_name} WHERE 1=0"

        # Handle different data types
        if isinstance(self.fk_values[0], str):
            values_str = ', '.join(f"'{v}'" for v in self.fk_values)
        else:
            values_str = ', '.join(str(v) for v in self.fk_values)

        return f"SELECT * FROM {schema}.{table_name} WHERE {self.fk_column} IN ({values_str})"

    def __str__(self):
        return f"ForeignKeyFilter({self.fk_column} IN {len(self.fk_values)} values)"


class StatusFilter(FilterQuery):
    """
    Filter by status column

    Example:
        filter = StatusFilter('status', ['active', 'pending'])
        query = filter.build('users')
        # SELECT * FROM users WHERE status IN ('active', 'pending')
    """

    def __init__(self, status_column: str = 'status',
                 allowed_statuses: List[str] = None,
                 excluded_statuses: List[str] = None):
        """
        Args:
            status_column: Column name containing status
            allowed_statuses: List of statuses to include (whitelist)
            excluded_statuses: List of statuses to exclude (blacklist)
        """
        self.status_column = status_column
        self.allowed_statuses = allowed_statuses
        self.excluded_statuses = excluded_statuses

        if allowed_statuses and excluded_statuses:
            raise ValueError("Cannot specify both allowed_statuses and excluded_statuses")

    def build(self, table_name: str, **params) -> str:
        schema = params.get('schema', 'public')

        if self.allowed_statuses:
            statuses_str = ', '.join(f"'{s}'" for s in self.allowed_statuses)
            condition = f"{self.status_column} IN ({statuses_str})"
        elif self.excluded_statuses:
            statuses_str = ', '.join(f"'{s}'" for s in self.excluded_statuses)
            condition = f"{self.status_column} NOT IN ({statuses_str})"
        else:
            # No filter
            condition = "1=1"

        return f"SELECT * FROM {schema}.{table_name} WHERE {condition}"

    def __str__(self):
        if self.allowed_statuses:
            return f"StatusFilter(allowed: {self.allowed_statuses})"
        elif self.excluded_statuses:
            return f"StatusFilter(excluded: {self.excluded_statuses})"
        else:
            return "StatusFilter(no filter)"


class CompositeFilter(FilterQuery):
    """
    Combine multiple filters with AND/OR

    Example:
        date_filter = DateRangeFilter('created_at', '2024-01-01', '2024-12-31')
        status_filter = StatusFilter('status', ['active'])
        composite = CompositeFilter(date_filter, status_filter, operator='AND')
    """

    def __init__(self, *filters: FilterQuery, operator: str = 'AND'):
        """
        Args:
            *filters: Variable number of FilterQuery objects
            operator: 'AND' or 'OR' to combine filters
        """
        self.filters = filters
        self.operator = operator.upper()

        if self.operator not in ('AND', 'OR'):
            raise ValueError(f"Invalid operator: {operator}. Must be 'AND' or 'OR'")

    def build(self, table_name: str, **params) -> str:
        schema = params.get('schema', 'public')

        if not self.filters:
            return f"SELECT * FROM {schema}.{table_name}"

        # Build each filter and extract WHERE conditions
        conditions = []
        for f in self.filters:
            query = f.build(table_name, **params)
            # Extract WHERE clause
            where_idx = query.upper().find('WHERE')
            if where_idx != -1:
                condition = query[where_idx + 5:].strip()
                conditions.append(f"({condition})")

        if not conditions:
            return f"SELECT * FROM {schema}.{table_name}"

        combined_condition = f" {self.operator} ".join(conditions)
        return f"SELECT * FROM {schema}.{table_name} WHERE {combined_condition}"

    def __str__(self):
        filters_str = f" {self.operator} ".join(str(f) for f in self.filters)
        return f"CompositeFilter({filters_str})"


class CustomQueryFilter(FilterQuery):
    """
    Wrapper for custom raw SQL queries

    Example:
        filter = CustomQueryFilter("SELECT * FROM users WHERE age > 18 AND country = 'US'")
    """

    def __init__(self, query: str):
        """
        Args:
            query: Complete SELECT query
        """
        self.query = query

    def build(self, table_name: str, **params) -> str:
        return self.query

    def __str__(self):
        return f"CustomQueryFilter({self.query[:50]}...)"
