"""
PostgreSQL Backup Plugin

Framework-agnostic PostgreSQL backup library with filtering support.

Features:
- Direct streaming (no temp files, low RAM usage)
- COPY format (fast backup and restore)
- Flexible filtering per table
- Multiple export destinations (local, S3, etc.)
- Framework-agnostic (works with Django, Flask, FastAPI, pure Python)

Quick Start:
    from postgres_backup_plugin import PostgresBackupEngine, DatabaseConfig

    db_config = DatabaseConfig(
        host='localhost',
        database='mydb',
        user='postgres',
        password='secret'
    )

    engine = PostgresBackupEngine(db_config)
    result = engine.backup('/tmp/backup.sql')

For Django:
    from postgres_backup_plugin import PostgresBackupEngine

    engine = PostgresBackupEngine.from_django_settings()
    result = engine.backup('/tmp/backup.sql')
"""

__version__ = '1.0.4'
__author__ = 'Võ Thiên Hòa'

# Core components
from .core import PostgresBackupEngine, CopyToStreamWrapper, QueryBuilder

# Configuration
from .config import DatabaseConfig, BackupConfig, BackupResult

# Filters
from .filters import (
    FilterQuery,
    DateRangeFilter,
    ForeignKeyFilter,
    StatusFilter,
    CompositeFilter,
    CustomQueryFilter
)

# Exporters
from .exporters import BackupExporter, LocalFileExporter, S3Exporter

# Exceptions
from .exceptions import (
    BackupPluginError,
    DatabaseConnectionError,
    FilterValidationError,
    ExportError,
    BackupCreationError,
    ConfigurationError
)

__all__ = [
    # Core
    'PostgresBackupEngine',
    'CopyToStreamWrapper',
    'QueryBuilder',

    # Config
    'DatabaseConfig',
    'BackupConfig',
    'BackupResult',

    # Filters
    'FilterQuery',
    'DateRangeFilter',
    'ForeignKeyFilter',
    'StatusFilter',
    'CompositeFilter',
    'CustomQueryFilter',

    # Exporters
    'BackupExporter',
    'LocalFileExporter',
    'S3Exporter',

    # Exceptions
    'BackupPluginError',
    'DatabaseConnectionError',
    'FilterValidationError',
    'ExportError',
    'BackupCreationError',
    'ConfigurationError',
]
