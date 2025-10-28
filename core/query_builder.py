"""
SQL query builder utilities
"""
from typing import List, Optional


class QueryBuilder:
    """Helper class for building SQL queries"""

    @staticmethod
    def get_all_tables(schema='public') -> str:
        """Get query to list all tables in schema"""
        return f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = '{schema}'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """

    @staticmethod
    def get_table_structure(table_name: str, schema='public') -> str:
        """Get query to retrieve table structure"""
        return f"""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = '{schema}'
            AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """

    @staticmethod
    def get_table_columns(table_name: str, schema='public') -> str:
        """Get query to retrieve just column names"""
        return f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = '{schema}'
            AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """

    @staticmethod
    def get_row_count(query: str) -> str:
        """Wrap query to count rows"""
        return f"SELECT COUNT(*) FROM ({query}) AS t"

    @staticmethod
    def get_column_structure(query: str) -> str:
        """Wrap query to get column structure (no data)"""
        return f"SELECT * FROM ({query}) AS t LIMIT 0"

    @staticmethod
    def build_select_all(table_name: str, schema='public') -> str:
        """Build SELECT * query"""
        return f"SELECT * FROM {schema}.{table_name}"

    @staticmethod
    def build_copy_to(query: str, delimiter='\\t', null_string='\\N',
                     quote_char='\\b', escape_char='\\b') -> str:
        """
        Build COPY TO STDOUT query

        Args:
            query: SELECT query to export
            delimiter: Field delimiter (default: tab)
            null_string: NULL representation (default: \\N)
            quote_char: Quote character (default: \\b - backspace, rarely used)
            escape_char: Escape character (default: \\b)

        Returns:
            str: COPY TO STDOUT query
        """
        return (f"COPY ({query}) TO STDOUT WITH "
                f"(FORMAT CSV, DELIMITER E'{delimiter}', NULL '{null_string}', "
                f"QUOTE E'{quote_char}', ESCAPE E'{escape_char}')")

    @staticmethod
    def build_copy_from(table_name: str, columns: List[str],
                       delimiter='\\t', null_string='\\N',
                       quote_char='\\b', escape_char='\\b') -> str:
        """
        Build COPY FROM stdin query

        Args:
            table_name: Target table name
            columns: List of column names
            delimiter: Field delimiter (default: tab)
            null_string: NULL representation (default: \\N)
            quote_char: Quote character
            escape_char: Escape character

        Returns:
            str: COPY FROM stdin query
        """
        columns_str = ', '.join(columns)
        return (f"COPY {table_name} ({columns_str}) FROM stdin WITH "
                f"(FORMAT CSV, DELIMITER E'{delimiter}', NULL '{null_string}', "
                f"QUOTE E'{quote_char}', ESCAPE E'{escape_char}')")

    @staticmethod
    def escape_identifier(identifier: str) -> str:
        """Escape SQL identifier (table/column name)"""
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'

    @staticmethod
    def build_performance_settings(disable_triggers=True, disable_fsync=True) -> List[str]:
        """
        Build SQL statements for performance optimization during restore

        Args:
            disable_triggers: Disable triggers during restore
            disable_fsync: Disable fsync for faster writes

        Returns:
            List[str]: SQL statements
        """
        settings = []

        if disable_triggers:
            settings.append("SET session_replication_role = replica;")

        if disable_fsync:
            settings.append("SET synchronous_commit = off;")

        return settings

    @staticmethod
    def build_schema_setup(schema_name: str, drop_existing=True) -> List[str]:
        """
        Build SQL statements for schema setup

        Args:
            schema_name: Schema name to create
            drop_existing: Drop schema if exists

        Returns:
            List[str]: SQL statements
        """
        statements = []

        if drop_existing:
            statements.append(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;")

        statements.append(f"CREATE SCHEMA {schema_name};")
        statements.append(f"SET search_path = {schema_name}, public;")

        return statements
