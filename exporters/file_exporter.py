"""
Local file system exporter
"""
import os
import shutil
from typing import Dict, Any, Optional

from .base import BackupExporter
from ..exceptions import ExportError


class LocalFileExporter(BackupExporter):
    """
    Export backup to local file system (copy/move to another location)

    Example:
        exporter = LocalFileExporter('/backups/archive/', move=True)
        destination = exporter.export('/tmp/backup.sql')
    """

    def __init__(self, destination_dir: str, move: bool = False, create_dir: bool = True):
        """
        Args:
            destination_dir: Destination directory path
            move: Move file instead of copy (default: False)
            create_dir: Create destination directory if not exists (default: True)
        """
        self.destination_dir = destination_dir
        self.move = move
        self.create_dir = create_dir

    def export(self, backup_file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Export backup to local directory"""
        try:
            # Create destination directory if needed
            if self.create_dir:
                os.makedirs(self.destination_dir, exist_ok=True)

            # Check if destination dir exists
            if not os.path.isdir(self.destination_dir):
                raise ExportError(f"Destination directory does not exist: {self.destination_dir}")

            # Get filename
            filename = os.path.basename(backup_file_path)
            destination_path = os.path.join(self.destination_dir, filename)

            # Copy or move
            if self.move:
                shutil.move(backup_file_path, destination_path)
            else:
                shutil.copy2(backup_file_path, destination_path)

            return destination_path

        except Exception as e:
            raise ExportError(f"Failed to export to local file system: {e}")

    def validate_config(self) -> bool:
        """Validate that destination directory is writable"""
        if os.path.exists(self.destination_dir):
            return os.access(self.destination_dir, os.W_OK)
        else:
            # Check parent directory
            parent = os.path.dirname(self.destination_dir)
            return os.access(parent, os.W_OK) if os.path.exists(parent) else False

    def __str__(self):
        mode = "move" if self.move else "copy"
        return f"LocalFileExporter(destination={self.destination_dir}, mode={mode})"
