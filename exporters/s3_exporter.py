"""
AWS S3 exporter
"""
import os
import logging
from typing import Dict, Any, Optional

from .base import BackupExporter
from ..exceptions import ExportError


class S3Exporter(BackupExporter):
    """
    Export backup to AWS S3

    Example:
        exporter = S3Exporter(
            bucket='my-backups',
            prefix='postgres/',
            delete_local=True
        )
        s3_url = exporter.export('/tmp/backup.sql')
    """

    def __init__(self, bucket: str, prefix: str = '', region: str = None,
                 delete_local: bool = False, storage_class: str = 'STANDARD',
                 aws_access_key: str = None, aws_secret_key: str = None,
                 logger: logging.Logger = None):
        """
        Args:
            bucket: S3 bucket name
            prefix: Key prefix (folder path in S3)
            region: AWS region (uses default if None)
            delete_local: Delete local file after successful upload
            storage_class: S3 storage class (STANDARD, GLACIER, etc.)
            aws_access_key: AWS access key (uses boto3 default if None)
            aws_secret_key: AWS secret key (uses boto3 default if None)
            logger: Optional logger
        """
        self.bucket = bucket
        self.prefix = prefix.rstrip('/') + '/' if prefix else ''
        self.region = region
        self.delete_local = delete_local
        self.storage_class = storage_class
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.logger = logger or logging.getLogger(__name__)

    def export(self, backup_file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Upload backup to S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            # Create S3 client
            if self.aws_access_key and self.aws_secret_key:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.region
                )
            else:
                s3_client = boto3.client('s3', region_name=self.region)

            # Prepare S3 key
            filename = os.path.basename(backup_file_path)
            s3_key = f"{self.prefix}{filename}"

            # Prepare upload args
            extra_args = {
                'StorageClass': self.storage_class
            }

            # Add metadata if provided
            if metadata:
                # S3 metadata must be strings
                s3_metadata = {k: str(v) for k, v in metadata.items()}
                extra_args['Metadata'] = s3_metadata

            # Upload file
            self.logger.info(f"Uploading to S3: s3://{self.bucket}/{s3_key}")

            s3_client.upload_file(
                backup_file_path,
                self.bucket,
                s3_key,
                ExtraArgs=extra_args
            )

            # Construct S3 URL
            if self.region:
                s3_url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{s3_key}"
            else:
                s3_url = f"https://{self.bucket}.s3.amazonaws.com/{s3_key}"

            self.logger.info(f"Upload successful: {s3_url}")

            # Delete local file if requested
            if self.delete_local:
                self.cleanup(backup_file_path)

            return s3_url

        except ImportError:
            raise ExportError("boto3 is not installed. Install with: pip install boto3")
        except NoCredentialsError:
            raise ExportError("AWS credentials not found. Configure AWS credentials or pass them explicitly.")
        except ClientError as e:
            raise ExportError(f"S3 client error: {e}")
        except Exception as e:
            raise ExportError(f"Failed to export to S3: {e}")

    def cleanup(self, backup_file_path: str):
        """Delete local backup file"""
        try:
            if os.path.exists(backup_file_path):
                os.remove(backup_file_path)
                self.logger.info(f"Deleted local file: {backup_file_path}")
        except Exception as e:
            self.logger.warning(f"Failed to delete local file {backup_file_path}: {e}")

    def validate_config(self) -> bool:
        """Validate S3 configuration"""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            s3_client = boto3.client('s3', region_name=self.region)

            # Check if bucket exists and is accessible
            s3_client.head_bucket(Bucket=self.bucket)
            return True

        except ImportError:
            self.logger.error("boto3 not installed")
            return False
        except NoCredentialsError:
            self.logger.error("AWS credentials not configured")
            return False
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                self.logger.error(f"Bucket does not exist: {self.bucket}")
            elif error_code == '403':
                self.logger.error(f"Access denied to bucket: {self.bucket}")
            else:
                self.logger.error(f"S3 error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False

    def __str__(self):
        return f"S3Exporter(bucket={self.bucket}, prefix={self.prefix}, delete_local={self.delete_local})"
