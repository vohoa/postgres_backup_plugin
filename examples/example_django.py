"""
Django integration examples for postgres_backup_plugin
"""

from postgres_backup_plugin import PostgresBackupEngine, S3Exporter
from postgres_backup_plugin.filters import DateRangeFilter, ForeignKeyFilter


def example_django_basic():
    """Basic Django backup"""
    print("=== Django Basic Backup ===\n")

    # Create engine from Django settings
    engine = PostgresBackupEngine.from_django_settings(
        excluded_tables=['django_session', 'django_admin_log']
    )

    # Create backup
    result = engine.backup('/tmp/django_backup.sql')

    if result.success:
        print(f"✅ Django backup successful!")
        print(f"   Tables: {result.tables_count}")
        print(f"   Rows: {result.total_rows:,}")
    else:
        print(f"❌ Backup failed: {result.error_message}")


def example_django_with_s3():
    """Django backup with S3 export"""
    print("\n=== Django Backup + S3 Export ===\n")

    # Create backup
    engine = PostgresBackupEngine.from_django_settings()
    result = engine.backup('/tmp/backup_for_s3.sql')

    if result.success:
        print(f"✅ Backup created: {result.file_path}")

        # Export to S3
        exporter = S3Exporter(
            bucket='my-backups',
            prefix='django/backups/',
            delete_local=True  # Delete local file after upload
        )

        s3_url = exporter.export(result.file_path, metadata=result.metadata)
        print(f"✅ Uploaded to S3: {s3_url}")
    else:
        print(f"❌ Backup failed: {result.error_message}")


def example_django_filtered_by_user():
    """Backup data related to specific users"""
    print("\n=== Django Filtered by User IDs ===\n")

    # Users to backup
    user_ids = [10, 20, 30]

    engine = PostgresBackupEngine.from_django_settings()

    # Create filters for related data
    filters = {
        'auth_user': ForeignKeyFilter('id', user_ids),
        'orders': ForeignKeyFilter('user_id', user_ids),
        'profiles': ForeignKeyFilter('user_id', user_ids),
        'comments': ForeignKeyFilter('user_id', user_ids)
    }

    result = engine.backup(
        output_path='/tmp/user_data_backup.sql',
        filters=filters,
        schema_name='user_export',
        metadata={'user_ids': user_ids}
    )

    if result.success:
        print(f"✅ User data backup successful!")
        print(f"   Backed up data for {len(user_ids)} users")
        print(f"   Total rows: {result.total_rows:,}")
    else:
        print(f"❌ Backup failed: {result.error_message}")


def example_django_delivery_backup():
    """
    Example: Backup data for a specific delivery
    (Like your current use case!)
    """
    print("\n=== Django Delivery Backup ===\n")

    delivery_id = 123  # Example delivery ID

    engine = PostgresBackupEngine.from_django_settings(
        excluded_tables=['django_session', 'django_admin_log']
    )

    # Build filters to get only delivery-related data
    filters = {
        'delivery_table': f'SELECT * FROM delivery_table WHERE delivery_id = {delivery_id}',
        'delivery_items': f'SELECT * FROM delivery_items WHERE delivery_id = {delivery_id}',
        'delivery_logs': f'SELECT * FROM delivery_logs WHERE delivery_id = {delivery_id}'
    }

    result = engine.backup(
        output_path=f'/tmp/delivery_{delivery_id}_backup.sql',
        filters=filters,
        schema_name=f'as_{delivery_id}',
        metadata={
            'delivery_id': delivery_id,
            'backup_type': 'delivery_export',
            'created_by': 'backup_service'
        }
    )

    if result.success:
        print(f"✅ Delivery backup successful!")
        print(f"   Delivery ID: {delivery_id}")
        print(f"   File: {result.file_path}")
        print(f"   Size: {result.size_bytes:,} bytes")

        # Upload to S3
        exporter = S3Exporter(
            bucket='my-delivery-backups',
            prefix=f'deliveries/{delivery_id}/',
            delete_local=True
        )

        s3_url = exporter.export(result.file_path, metadata=result.metadata)
        print(f"✅ Uploaded to S3: {s3_url}")
    else:
        print(f"❌ Backup failed: {result.error_message}")


if __name__ == '__main__':
    # Note: These examples require Django to be configured
    # Run with: python manage.py shell < example_django.py

    example_django_basic()
    example_django_with_s3()
    example_django_filtered_by_user()
    example_django_delivery_backup()
