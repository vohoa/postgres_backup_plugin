"""
Core backup engine - framework-agnostic PostgreSQL backup with filtering
"""
import os
import time
import datetime
import logging
import subprocess
from typing import Dict, Optional, List, Any

from ..config import DatabaseConfig, BackupConfig, BackupResult
from ..exceptions import (
    DatabaseConnectionError, BackupCreationError,
    FilterValidationError, ConfigurationError
)
from .stream_wrapper import CopyToStreamWrapper
from .query_builder import QueryBuilder


class PostgresBackupEngine:
    """
    Framework-agnostic PostgreSQL backup engine with filtering support.

    Features:
    - Direct streaming (no temp files, low RAM usage)
    - COPY format (fast backup and restore)
    - Flexible filtering per table
    - Extensible and reusable
    """

    def __init__(self, db_config: DatabaseConfig, backup_config: Optional[BackupConfig] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize backup engine

        Args:
            db_config: Database connection configuration
            backup_config: Backup operation configuration
            logger: Optional logger (uses stdlib logging if None)
        """
        self.db_config = db_config
        self.backup_config = backup_config or BackupConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.query_builder = QueryBuilder()

    @classmethod
    def from_django_settings(cls, excluded_tables: Optional[List[str]] = None,
                            logger: Optional[logging.Logger] = None,
                            settings_module=None):
        """
        Create engine from Django settings

        Args:
            excluded_tables: Tables to exclude from backup
            logger: Optional logger
            settings_module: Django settings module (uses django.conf.settings if None)

        Returns:
            PostgresBackupEngine instance
        """
        db_config = DatabaseConfig.from_django_settings(settings_module)
        backup_config = BackupConfig(excluded_tables=excluded_tables or [])
        return cls(db_config, backup_config, logger)

    def backup(self, output_path: str, filters: Optional[Dict[str, Any]] = None,
               schema_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> BackupResult:
        """
        Create backup with optional filtering

        Args:
            output_path: Where to save backup file
            filters: Dictionary mapping table names to filter queries
                Can be: {table_name: "SELECT ...", ...}
                Or: {table_name: FilterQuery object, ...}
            schema_name: Custom schema name for restore (optional)
            metadata: Additional metadata to include in header

        Returns:
            BackupResult object with statistics
        """
        start_time = time.time()
        result = BackupResult(success=False)

        try:
            self.logger.info(f"Starting backup to {output_path}")

            # Validate filters
            if filters:
                self._validate_filters(filters)

            # Connect to database
            conn = self._connect()

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

            # Create backup
            with open(output_path, 'w', encoding=self.backup_config.encoding) as outfile:
                stats = self._write_backup(conn, outfile, filters, schema_name, metadata)

            conn.close()

            # Populate result
            result.success = True
            result.file_path = output_path
            result.size_bytes = os.path.getsize(output_path)
            result.tables_count = stats['tables_count']
            result.total_rows = stats['total_rows']
            result.duration_seconds = time.time() - start_time
            result.metadata = metadata or {}
            result.stats = stats

            self.logger.info(f"Backup completed successfully: {result}")

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.duration_seconds = time.time() - start_time
            self.logger.error(f"Backup failed: {e}", exc_info=True)

        return result

    def validate_filters(self, filters: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate filter queries before backup

        Args:
            filters: Dictionary of table filters

        Returns:
            Dict with validation results per table

        Raises:
            FilterValidationError: If any filter is invalid
        """
        return self._validate_filters(filters)

    def estimate_size(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        Estimate backup size before running

        Args:
            filters: Optional filters to apply

        Returns:
            Dict with estimated rows per table
        """
        conn = self._connect()
        estimates = {}

        with conn.cursor() as cursor:
            tables = self._get_tables(cursor)

            for table_name in tables:
                if table_name in self.backup_config.excluded_tables:
                    continue

                # Build query
                query = self._build_query_for_table(table_name, filters)

                # Count rows
                count_query = self.query_builder.get_row_count(query)
                cursor.execute(count_query)
                row_count = cursor.fetchone()[0] or 0

                estimates[table_name] = row_count

        conn.close()
        return estimates

    def _connect(self):
        """Establish database connection"""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.db_config.to_dict())
            self.logger.debug(f"Connected to database: {self.db_config.database}")
            return conn
        except ImportError:
            raise DatabaseConnectionError("psycopg2 is not installed. Install with: pip install psycopg2-binary")
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")

    def _validate_filters(self, filters: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate all filter queries"""
        if not filters:
            return {}

        conn = self._connect()
        validation_results = {}

        with conn.cursor() as cursor:
            for table_name, filter_query in filters.items():
                errors = []

                # Build query string
                query = self._resolve_filter_query(table_name, filter_query)

                try:
                    # Test query structure
                    test_query = self.query_builder.get_column_structure(query)
                    cursor.execute(test_query)

                    if cursor.description is None:
                        errors.append("Query returned no columns")

                except Exception as e:
                    errors.append(str(e))

                validation_results[table_name] = errors

        conn.close()

        # Check if any errors
        failed_tables = {t: e for t, e in validation_results.items() if e}
        if failed_tables:
            raise FilterValidationError(f"Filter validation failed: {failed_tables}")

        return validation_results

    def _write_backup(self, conn, outfile, filters, schema_name, metadata) -> Dict[str, Any]:
        """Write backup to file"""
        stats = {
            'tables_count': 0,
            'total_rows': 0,
            'tables': {}
        }

        # Write header
        self._write_header(outfile, schema_name, metadata, filters)

        # Write schema setup
        if schema_name:
            self._write_schema_setup(outfile, schema_name)

        # Write performance optimizations
        self._write_performance_settings(outfile)

        with conn.cursor() as cursor:
            # Get all tables
            tables = self._get_tables(cursor)

            outfile.write("-- ========================================\n")
            outfile.write("-- TABLE STRUCTURES AND DATA\n")
            outfile.write("-- ========================================\n\n")

            # Process each table
            for table_name in tables:
                # Skip excluded tables
                if table_name in self.backup_config.excluded_tables:
                    self.logger.info(f"Skipping excluded table: {table_name}")
                    continue

                try:
                    table_stats = self._backup_table(cursor, outfile, table_name, filters)
                    stats['tables'][table_name] = table_stats
                    stats['total_rows'] += table_stats['rows']
                    stats['tables_count'] += 1

                except Exception as e:
                    self.logger.warning(f"Failed to backup table {table_name}: {e}")
                    outfile.write(f"\n-- ERROR backing up table: {table_name}\n")
                    outfile.write(f"-- {str(e)}\n\n")
                    continue

        # Write footer
        self._write_footer(outfile)

        return stats

    def _backup_table(self, cursor, outfile, table_name, filters) -> Dict[str, Any]:
        """Backup single table"""
        # Dump table structure
        self._dump_table_structure(table_name, outfile)

        # Build query
        query = self._build_query_for_table(table_name, filters)

        # Get column names
        test_query = self.query_builder.get_column_structure(query)
        cursor.execute(test_query)

        if cursor.description is None:
            raise BackupCreationError(f"Query returned no columns for table {table_name}")

        column_names = [desc[0] for desc in cursor.description]
        columns_str = ', '.join(column_names)

        # Count rows
        count_query = self.query_builder.get_row_count(query)
        cursor.execute(count_query)
        row_count = cursor.fetchone()[0] or 0

        bytes_written = 0

        if row_count > 0:
            # Write COPY command header
            outfile.write(f"\n-- Data for table: {table_name}\n")
            outfile.write(f"-- Rows: {row_count}\n")

            copy_from_stmt = self.query_builder.build_copy_from(
                table_name, column_names,
                delimiter=self.backup_config.copy_delimiter,
                null_string=self.backup_config.copy_null_string
            )
            outfile.write(f"{copy_from_stmt};\n")

            # Stream data directly
            copy_to_query = self.query_builder.build_copy_to(
                query,
                delimiter=self.backup_config.copy_delimiter,
                null_string=self.backup_config.copy_null_string
            )

            wrapper = CopyToStreamWrapper(outfile)
            cursor.copy_expert(copy_to_query, wrapper)
            bytes_written = wrapper.bytes_written

            # Write terminator
            outfile.write("\\.\n\n")

            self.logger.info(f"Exported {row_count} rows ({bytes_written} bytes) for table: {table_name}")
        else:
            outfile.write(f"\n-- Data for table: {table_name}\n")
            outfile.write(f"-- No rows to export (filtered or empty)\n\n")
            self.logger.info(f"No rows to export for table: {table_name}")

        return {
            'rows': row_count,
            'bytes': bytes_written,
            'columns': len(column_names)
        }

    def _get_tables(self, cursor) -> List[str]:
        """Get all tables in public schema"""
        query = self.query_builder.get_all_tables()
        cursor.execute(query)
        return [row[0] for row in cursor.fetchall()]

    def _build_query_for_table(self, table_name: str, filters: Optional[Dict[str, Any]]) -> str:
        """Build SELECT query for table with optional filter"""
        if filters and table_name in filters:
            filter_query = filters[table_name]
            return self._resolve_filter_query(table_name, filter_query)
        else:
            return self.query_builder.build_select_all(table_name)

    def _resolve_filter_query(self, table_name: str, filter_query: Any) -> str:
        """Resolve filter query (string or FilterQuery object)"""
        if isinstance(filter_query, str):
            return filter_query
        elif hasattr(filter_query, 'build'):
            # FilterQuery object
            return filter_query.build(table_name)
        else:
            raise FilterValidationError(
                f"Invalid filter for table {table_name}: must be string or FilterQuery object"
            )

    def _dump_table_structure(self, table_name: str, outfile):
        """Dump table structure using pg_dump"""
        try:
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config.password

            pg_dump_cmd = [
                'pg_dump',
                '--host', self.db_config.host,
                '--port', str(self.db_config.port),
                '--username', self.db_config.user,
                '--dbname', self.db_config.database,
                '--schema-only',
                '--no-owner',
                '--no-privileges',
                '--table', f'public.{table_name}'
            ]

            result = subprocess.run(
                pg_dump_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                outfile.write(f"\n-- Table structure for: {table_name}\n")
                outfile.write(result.stdout)
                outfile.write("\n")
            else:
                self.logger.warning(f"Failed to dump structure for {table_name}: {result.stderr}")

        except Exception as e:
            self.logger.warning(f"Could not dump structure for {table_name}: {e}")

    def _write_header(self, outfile, schema_name, metadata, filters):
        """Write backup file header"""
        if not self.backup_config.include_header:
            return

        outfile.write(f"-- PostgreSQL Database Backup\n")
        outfile.write(f"-- Generated: {datetime.datetime.now().isoformat()}\n")
        outfile.write(f"-- Database: {self.db_config.database}\n")
        outfile.write(f"-- Using COPY format for fast restore\n")

        if schema_name:
            outfile.write(f"-- Target schema: {schema_name}\n")

        if filters:
            outfile.write(f"-- Filtered tables: {len(filters)}\n")

        if metadata:
            outfile.write(f"-- Metadata:\n")
            for key, value in metadata.items():
                outfile.write(f"--   {key}: {value}\n")

        outfile.write("\n")

    def _write_schema_setup(self, outfile, schema_name):
        """Write schema setup SQL"""
        outfile.write("-- ========================================\n")
        outfile.write("-- SCHEMA SETUP\n")
        outfile.write("-- ========================================\n\n")

        statements = self.query_builder.build_schema_setup(schema_name, drop_existing=True)
        for stmt in statements:
            outfile.write(f"{stmt}\n")

        outfile.write("\n")

    def _write_performance_settings(self, outfile):
        """Write performance optimization settings"""
        outfile.write("-- ========================================\n")
        outfile.write("-- PERFORMANCE OPTIMIZATIONS\n")
        outfile.write("-- ========================================\n\n")

        statements = self.query_builder.build_performance_settings(
            disable_triggers=self.backup_config.disable_triggers,
            disable_fsync=self.backup_config.disable_fsync
        )
        for stmt in statements:
            outfile.write(f"{stmt}\n")

        outfile.write("\n")

    def _write_footer(self, outfile):
        """Write backup file footer"""
        outfile.write("-- ========================================\n")
        outfile.write("-- FINALIZATION\n")
        outfile.write("-- ========================================\n\n")
        outfile.write("-- Re-enable optimizations\n")
        outfile.write("SET session_replication_role = DEFAULT;\n")
        outfile.write("SET synchronous_commit = on;\n")
        outfile.write("ANALYZE;\n\n")
        outfile.write(f"-- Backup completed: {datetime.datetime.now().isoformat()}\n")
