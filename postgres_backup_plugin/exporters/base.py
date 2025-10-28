"""
Base exporter interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BackupExporter(ABC):
    """
    Base class for backup exporters.

    Exporters handle the storage/transmission of backup files
    to various destinations (local, S3, GCS, etc.)
    """

    @abstractmethod
    def export(self, backup_file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Export backup file to destination

        Args:
            backup_file_path: Path to local backup file
            metadata: Optional metadata about the backup

        Returns:
            str: URL or path to exported backup

        Raises:
            ExportError: If export fails
        """
        raise NotImplementedError("Subclasses must implement export() method")

    def cleanup(self, backup_file_path: str):
        """
        Cleanup local backup file after export (optional)

        Args:
            backup_file_path: Path to local file to cleanup
        """
        pass

    def validate_config(self) -> bool:
        """
        Validate exporter configuration before use (optional)

        Returns:
            bool: True if config is valid
        """
        return True

    def __str__(self):
        return f"{self.__class__.__name__}()"
