"""
Custom exceptions for Postgres Backup Plugin
"""


class BackupPluginError(Exception):
    """Base exception for all plugin errors"""
    pass


class DatabaseConnectionError(BackupPluginError):
    """Raised when database connection fails"""
    pass


class FilterValidationError(BackupPluginError):
    """Raised when filter query is invalid"""
    pass


class ExportError(BackupPluginError):
    """Raised when export operation fails"""
    pass


class BackupCreationError(BackupPluginError):
    """Raised when backup creation fails"""
    pass


class ConfigurationError(BackupPluginError):
    """Raised when configuration is invalid"""
    pass
