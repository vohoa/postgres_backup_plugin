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
               schema_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
               source_schema: Optional[str] = 'public') -> BackupResult:
        """
        Create backup with optional filtering and automatic SQL cleaning

        Args:
            output_path: Where to save backup file
            filters: Dictionary mapping table names to filter queries
                Can be: {table_name: "SELECT ...", ...}
                Or: {table_name: FilterQuery object, ...}
            schema_name: Custom schema name for restore (target schema, optional)
            metadata: Additional metadata to include in header
            source_schema: Source schema to backup from (default: 'public')

        Returns:
            BackupResult object with statistics

        Notes:
            - If backup_config.clean_output=True (default), the output SQL will be automatically
              cleaned to remove schema prefixes, psql meta-commands, and unnecessary SET statements
            - Use backup_config.target_schema to specify a custom target schema for cleaned output
            - source_schema specifies which schema to backup FROM (default: 'public')
        """
        start_time = time.time()
        result = BackupResult(success=False)
        temp_file = None

        try:
            self.logger.info(f"Starting backup to {output_path}")

            # Validate filters
            if filters:
                self._validate_filters(filters)

            # Connect to database
            conn = self._connect()

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

            # Determine if we need to clean the output
            need_cleaning = self.backup_config.clean_output

            if need_cleaning:
                # Create backup to a temporary file first
                import tempfile
                temp_fd, temp_file = tempfile.mkstemp(
                    suffix='.sql',
                    prefix='postgres_backup_temp_',
                    dir=os.path.dirname(output_path) or '.'
                )
                os.close(temp_fd)  # Close file descriptor, we'll open it with codecs

                self.logger.debug(f"Creating temporary backup file: {temp_file}")

                with open(temp_file, 'w', encoding=self.backup_config.encoding) as outfile:
                    stats = self._write_backup(conn, outfile, filters, schema_name, metadata, source_schema)

                conn.close()

                # Clean the SQL file
                self.logger.info("Cleaning SQL output...")
                self._clean_backup_file(temp_file, output_path, schema_name)

                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self.logger.debug(f"Removed temporary file: {temp_file}")

            else:
                # Direct write without cleaning
                with open(output_path, 'w', encoding=self.backup_config.encoding) as outfile:
                    stats = self._write_backup(conn, outfile, filters, schema_name, metadata, source_schema)

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

            if need_cleaning:
                result.metadata['cleaned'] = True

            self.logger.info(f"Backup completed successfully: {result}")

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.duration_seconds = time.time() - start_time
            self.logger.error(f"Backup failed: {e}", exc_info=True)

            # Clean up temp file on error
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    self.logger.debug(f"Cleaned up temporary file after error: {temp_file}")
                except Exception as cleanup_error:
                    self.logger.warning(f"Failed to clean up temp file: {cleanup_error}")

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

    def _write_backup(self, conn, outfile, filters, schema_name, metadata, source_schema='public') -> Dict[str, Any]:
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
            # Get all tables from source schema
            tables = self._get_tables(cursor, source_schema)

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
                    table_stats = self._backup_table(cursor, outfile, table_name, filters, source_schema)
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

    def _backup_table(self, cursor, outfile, table_name, filters, source_schema='public') -> Dict[str, Any]:
        """Backup single table"""
        # Dump table structure
        self._dump_table_structure(table_name, outfile, source_schema)

        # Build query
        query = self._build_query_for_table(table_name, filters, source_schema)

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

    def _get_tables(self, cursor, schema='public') -> List[str]:
        """Get all tables in specified schema"""
        query = self.query_builder.get_all_tables(schema=schema)
        cursor.execute(query)
        return [row[0] for row in cursor.fetchall()]

    def _build_query_for_table(self, table_name: str, filters: Optional[Dict[str, Any]], schema='public') -> str:
        """Build SELECT query for table with optional filter"""
        if filters and table_name in filters:
            filter_query = filters[table_name]
            return self._resolve_filter_query(table_name, filter_query)
        else:
            return self.query_builder.build_select_all(table_name, schema=schema)

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

    def _dump_table_structure(self, table_name: str, outfile, schema='public'):
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
                '--table', f'{schema}.{table_name}'
            ]

            result = subprocess.run(
                pg_dump_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                import re

                outfile.write(f"\n-- Table structure for: {table_name}\n")

                # Clean pg_dump output to remove psql meta-commands
                pg_dump_output = result.stdout

                # Remove \restrict and \unrestrict commands (from pg_dump)
                pg_dump_output = re.sub(r'^\s*\\restrict\s+.*$', '', pg_dump_output, flags=re.MULTILINE)
                pg_dump_output = re.sub(r'^\s*\\unrestrict\s+.*$', '', pg_dump_output, flags=re.MULTILINE)

                # Remove other psql meta-commands from pg_dump
                pg_dump_output = re.sub(r'^\s*\\[a-zA-Z]+\s+.*$', '', pg_dump_output, flags=re.MULTILINE)

                # Remove excessive empty lines
                pg_dump_output = re.sub(r'\n\n\n+', '\n\n', pg_dump_output)

                outfile.write(pg_dump_output)
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

    def _clean_backup_file(self, input_file: str, output_file: str,
                          schema_name: Optional[str] = None) -> None:
        """
        Clean a backup SQL file by removing schema prefixes and psql commands

        Args:
            input_file: Input SQL file to clean
            output_file: Output cleaned SQL file
            schema_name: Optional target schema name

        Raises:
            BackupCreationError: If cleaning fails
        """
        try:
            # Determine target schema
            target_schema = schema_name or self.backup_config.target_schema

            # Read input file
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Clean the content
            cleaned_content = self._clean_sql_content(content, remove_schema_prefix=True)

            # Write cleaned content
            with open(output_file, 'w', encoding='utf-8') as f:
                # Add header if target schema is specified
                if target_schema:
                    f.write(f"-- Cleaned SQL backup\n")
                    f.write(f"-- Target schema: {target_schema}\n")
                    f.write(f"-- Generated: {datetime.datetime.now().isoformat()}\n\n")
                    f.write(f"-- Set search path to target schema\n")
                    f.write(f"SET search_path = {target_schema}, public;\n\n")

                f.write(cleaned_content)

            file_size = os.path.getsize(output_file)
            self.logger.info(
                f"SQL file cleaned successfully: {output_file} ({file_size} bytes)"
            )

        except Exception as e:
            error_msg = f"Failed to clean backup file: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise BackupCreationError(error_msg) from e

    def _create_clean_sql_file(self, schema_file: str, data_file: str,
                               output_file: str, target_schema: str) -> None:
        """
        Create clean SQL file by combining schema and data files,
        removing schema prefix and adding target schema

        Args:
            schema_file: File containing schema backup
            data_file: File containing data backup
            output_file: Final output file
            target_schema: Target schema (e.g.: as_123)

        Raises:
            ValueError: If target_schema is invalid or files don't exist
            IOError: If file operations fail
            BackupCreationError: If backup creation fails
        """
        # Validate target schema name
        import re
        if not target_schema or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', target_schema):
            raise ValueError(f"Invalid target schema name: {target_schema}")

        # Validate input files exist (at least one should exist)
        schema_exists = os.path.exists(schema_file)
        data_exists = os.path.exists(data_file)

        if not schema_exists and not data_exists:
            raise ValueError(
                f"Both schema and data files are missing: {schema_file}, {data_file}"
            )

        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as output:
                # Header comments
                output.write(f"-- Database backup for schema: {target_schema}\n")
                output.write(f"-- Generated: {datetime.datetime.now().isoformat()}\n")
                output.write(f"-- Schema prefix removed for portability\n")
                output.write(f"-- Original schema: public -> {target_schema}\n\n")

                # Create target schema
                output.write(f"-- ========================================\n")
                output.write(f"-- SCHEMA SETUP\n")
                output.write(f"-- ========================================\n\n")
                output.write(f"-- Create target schema\n")
                output.write(f"DROP SCHEMA IF EXISTS {target_schema} CASCADE;\n")
                output.write(f"CREATE SCHEMA {target_schema};\n\n")
                output.write(f"-- Set search path to target schema\n")
                output.write(f"SET search_path = {target_schema}, public;\n\n")

                # Disable triggers and constraints for faster restore
                output.write(f"-- Disable triggers for faster restore\n")
                output.write(f"SET session_replication_role = replica;\n\n")

                # Process schema file (table structure)
                output.write("-- ========================================\n")
                output.write("-- TABLE STRUCTURES\n")
                output.write("-- ========================================\n\n")

                if schema_exists:
                    try:
                        with open(schema_file, 'r', encoding='utf-8') as f:
                            schema_content = f.read()

                        # Clean schema content
                        cleaned_schema = self._clean_sql_content(
                            schema_content,
                            remove_schema_prefix=True
                        )
                        if cleaned_schema.strip():
                            output.write(cleaned_schema)
                            output.write("\n\n")
                        else:
                            output.write("-- Schema file is empty after cleaning\n\n")

                    except UnicodeDecodeError as e:
                        self.logger.warning(
                            f"Encoding error reading schema file {schema_file}: {e}"
                        )
                        output.write(f"-- ERROR: Could not read schema file (encoding issue)\n\n")
                else:
                    output.write("-- No schema file found\n\n")

                # Process data file
                output.write("-- ========================================\n")
                output.write("-- DATA INSERTS\n")
                output.write("-- ========================================\n\n")

                if data_exists:
                    try:
                        with open(data_file, 'r', encoding='utf-8') as f:
                            data_content = f.read()

                        # Clean data content
                        cleaned_data = self._clean_sql_content(
                            data_content,
                            remove_schema_prefix=True
                        )
                        if cleaned_data.strip():
                            output.write(cleaned_data)
                            output.write("\n\n")
                        else:
                            output.write("-- Data file is empty after cleaning\n\n")

                    except UnicodeDecodeError as e:
                        self.logger.warning(
                            f"Encoding error reading data file {data_file}: {e}"
                        )
                        output.write(f"-- ERROR: Could not read data file (encoding issue)\n\n")
                else:
                    output.write("-- No data file found\n\n")

                # Re-enable triggers and constraints
                output.write("-- ========================================\n")
                output.write("-- FINALIZATION\n")
                output.write("-- ========================================\n\n")
                output.write("-- Re-enable triggers\n")
                output.write("SET session_replication_role = DEFAULT;\n\n")

                # Analyze tables for better performance
                output.write("-- Analyze tables for performance\n")
                output.write("ANALYZE;\n\n")

                # Footer
                output.write("-- ========================================\n")
                output.write("-- RESTORE COMPLETED\n")
                output.write("-- ========================================\n")
                output.write(f"-- Target schema: {target_schema}\n")
                output.write(f"-- Completion time: {datetime.datetime.now().isoformat()}\n")
                output.write(f"-- \n")
                output.write(f"-- To use this schema:\n")
                output.write(f"-- SET search_path = {target_schema}, public;\n")
                output.write(f"-- \\dt {target_schema}.*\n")

            # Verify output file was created
            if not os.path.exists(output_file):
                raise BackupCreationError(f"Output file was not created: {output_file}")

            file_size = os.path.getsize(output_file)
            self.logger.info(
                f"Clean SQL file created successfully: {output_file} "
                f"({file_size} bytes, target schema: {target_schema})"
            )

        except (IOError, OSError) as e:
            error_msg = f"File I/O error creating clean SQL file: {str(e)}"
            self.logger.error(error_msg)
            raise BackupCreationError(error_msg) from e

        except Exception as e:
            error_msg = f"Failed to create clean SQL file: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise BackupCreationError(error_msg) from e

    def _clean_sql_content(self, content: str, remove_schema_prefix: bool = True) -> str:
        """
        Clean SQL content by removing schema prefix and unnecessary commands

        Args:
            content: Original SQL content
            remove_schema_prefix: Whether to remove schema prefix

        Returns:
            Cleaned SQL content

        Raises:
            ValueError: If content is None
        """
        if content is None:
            raise ValueError("Content cannot be None")

        if not content.strip():
            return ""

        import re

        # Split into lines for processing
        lines = content.split('\n')
        cleaned_lines = []

        # Track if we're inside a COPY data block
        in_copy_block = False

        # Patterns for lines to skip (only when NOT in COPY block)
        skip_patterns = [
            r'^\s*--.*$',  # Comments (complete line comments)
            r'^\s*$',  # Empty lines
            r'^SET\s+search_path',  # Search path settings
            r'^SELECT\s+pg_catalog\.set_config',  # pg_catalog set_config calls
            r'^\s*\\[a-zA-Z]+.*$',  # All psql meta-commands (\unrestrict, \c, \d, etc.) - BUT NOT \. (COPY terminator)
            r'^SET\s+default_table_access_method',  # Table access method
            r'^SET\s+default_tablespace',  # Tablespace settings
            r'^SET\s+default_with_oids',  # OID settings (deprecated)
            r'^SET\s+row_security',  # Row security
            r'^SET\s+check_function_bodies',  # Function check
            r'^SET\s+xmloption',  # XML options
            r'^SET\s+client_min_messages',  # Client messages
            r'^SET\s+standard_conforming_strings',  # String conforming
            r'^SET\s+transaction_timeout',  # Remove unsupported transaction_timeout
            r'^SET\s+idle_in_transaction_session_timeout',  # Session timeout
            r'^SET\s+client_encoding',  # Client encoding (already handled)
            r'^\s*CREATE\s+SCHEMA\s+public\s*;',  # Remove CREATE SCHEMA public;
            r'^\s*COMMENT\s+ON\s+SCHEMA\s+public',  # Comments on public schema
        ]

        # Compile patterns once for better performance
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in skip_patterns]

        # Pattern to detect COPY command start
        copy_start_pattern = re.compile(r'^COPY\s+', re.IGNORECASE)
        # Pattern to detect COPY terminator
        copy_end_pattern = re.compile(r'^\\\.(\s*)$')

        for line in lines:
            # Check if entering COPY data block
            if copy_start_pattern.match(line):
                in_copy_block = True
                # Process COPY line (remove schema prefix)
                if remove_schema_prefix:
                    line = re.sub(
                        r'\bCOPY\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)',
                        r'COPY \1',
                        line,
                        flags=re.IGNORECASE
                    )
                cleaned_lines.append(line)
                continue

            # Check if exiting COPY data block
            if copy_end_pattern.match(line):
                in_copy_block = False
                cleaned_lines.append(line)  # Keep the terminator
                continue

            # If inside COPY block, keep ALL lines (including empty and data)
            if in_copy_block:
                cleaned_lines.append(line)
                continue

            # Outside COPY block: apply normal cleaning rules
            should_skip = any(pattern.match(line) for pattern in compiled_patterns)

            if should_skip:
                continue

            # Remove schema prefix if needed
            if remove_schema_prefix:
                # 1. CREATE TABLE statements
                line = re.sub(
                    r'\bCREATE\s+TABLE\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'CREATE TABLE \1',
                    line,
                    flags=re.IGNORECASE
                )

                # 2. INSERT INTO statements
                line = re.sub(
                    r'\bINSERT\s+INTO\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'INSERT INTO \1',
                    line,
                    flags=re.IGNORECASE
                )

                # 3. ALTER TABLE statements
                line = re.sub(
                    r'\bALTER\s+TABLE\s+(?:ONLY\s+)?public\.([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'ALTER TABLE \1',
                    line,
                    flags=re.IGNORECASE
                )

                # 4. CREATE INDEX statements
                line = re.sub(
                    r'\bCREATE\s+(UNIQUE\s+)?INDEX\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+ON\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'CREATE \1INDEX \2 ON \3',
                    line,
                    flags=re.IGNORECASE
                )

                # 5. CREATE SEQUENCE statements
                line = re.sub(
                    r'\bCREATE\s+SEQUENCE\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'CREATE SEQUENCE \1',
                    line,
                    flags=re.IGNORECASE
                )

                # 6. ALTER SEQUENCE statements
                line = re.sub(
                    r'\bALTER\s+SEQUENCE\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'ALTER SEQUENCE \1',
                    line,
                    flags=re.IGNORECASE
                )

                # 7. COPY statements
                line = re.sub(
                    r'\bCOPY\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'COPY \1',
                    line,
                    flags=re.IGNORECASE
                )

                # 8. Foreign key references
                line = re.sub(
                    r'\bREFERENCES\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'REFERENCES \1',
                    line,
                    flags=re.IGNORECASE
                )

                # 9. SELECT setval calls for sequences
                line = re.sub(
                    r"\bSELECT\s+pg_catalog\.setval\('public\.([a-zA-Z_][a-zA-Z0-9_]*)'",
                    r"SELECT pg_catalog.setval('\1'",
                    line,
                    flags=re.IGNORECASE
                )

                # 10. DROP TABLE/SEQUENCE statements
                line = re.sub(
                    r'\bDROP\s+(TABLE|SEQUENCE)\s+(?:IF\s+EXISTS\s+)?public\.([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'DROP \1 IF EXISTS \2',
                    line,
                    flags=re.IGNORECASE
                )

                # 11. GRANT/REVOKE statements
                line = re.sub(
                    r'\b(GRANT|REVOKE)\s+(.+?)\s+ON\s+(?:TABLE\s+)?public\.([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'\1 \2 ON \3',
                    line,
                    flags=re.IGNORECASE
                )

                # 12. TRIGGER statements
                line = re.sub(
                    r'\bON\s+public\.([a-zA-Z_][a-zA-Z0-9_]*)\s+FOR\s+EACH',
                    r'ON \1 FOR EACH',
                    line,
                    flags=re.IGNORECASE
                )

                # 13. General public. prefix removal (catch-all)
                # Use word boundary to avoid matching 'public' in strings
                line = re.sub(r'\bpublic\.([a-zA-Z_][a-zA-Z0-9_]*)', r'\1', line)

            # Only add line if not empty after processing
            if line.strip():
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)
