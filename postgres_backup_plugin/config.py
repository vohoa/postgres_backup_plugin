"""
Configuration module for Postgres Backup Plugin
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int = 5432
    user: str = 'postgres'
    password: str = ''
    database: str = 'postgres'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for psycopg2"""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'dbname': self.database
        }

    @classmethod
    def from_django_settings(cls, settings_module=None):
        """
        Create config from Django settings

        Args:
            settings_module: Django settings module (uses django.conf.settings if None)
        """
        if settings_module is None:
            try:
                from django.conf import settings as settings_module
            except ImportError:
                raise ImportError("Django is not installed or configured")

        db_config = settings_module.DATABASES.get('default', {})

        return cls(
            host=db_config.get('HOST', 'localhost'),
            port=int(db_config.get('PORT', 5432)),
            user=db_config.get('USER', 'postgres'),
            password=db_config.get('PASSWORD', ''),
            database=db_config.get('NAME', 'postgres')
        )


@dataclass
class BackupConfig:
    """Backup operation configuration"""
    excluded_tables: List[str] = field(default_factory=list)
    buffer_size: int = 8192
    copy_delimiter: str = '\\t'
    copy_null_string: str = '\\N'
    timeout: int = 3600  # seconds
    encoding: str = 'utf-8'

    # Performance options
    disable_triggers: bool = True
    disable_fsync: bool = True

    # Output options
    include_header: bool = True
    include_metadata: bool = True
    verbose_logging: bool = True

    # SQL Cleaning options
    clean_output: bool = True  # Clean SQL output (remove schema prefix, psql commands, etc.)
    target_schema: Optional[str] = None  # Target schema for cleaned output (if None, uses original schema)


@dataclass
class BackupResult:
    """Result of backup operation"""
    success: bool
    file_path: Optional[str] = None
    size_bytes: Optional[int] = None
    tables_count: int = 0
    total_rows: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        if self.success:
            return (f"Backup successful: {self.file_path} "
                   f"({self.size_bytes} bytes, {self.tables_count} tables, "
                   f"{self.total_rows} rows, {self.duration_seconds:.2f}s)")
        else:
            return f"Backup failed: {self.error_message}"
