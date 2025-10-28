"""
Basic usage examples for postgres_backup_plugin
"""

from postgres_backup_plugin import PostgresBackupEngine, DatabaseConfig


def example_basic_backup():
    """Simple backup without filters"""
    print("=== Basic Backup Example ===\n")

    # Configure database
    db_config = DatabaseConfig(
        host='localhost',
        port=5432,
        user='postgres',
        password='your_password',
        database='mydb'
    )

    # Create engine
    engine = PostgresBackupEngine(db_config)

    # Create backup
    result = engine.backup('/tmp/backup.sql')

    if result.success:
        print(f"✅ Backup successful!")
        print(f"   File: {result.file_path}")
        print(f"   Size: {result.size_bytes:,} bytes")
        print(f"   Tables: {result.tables_count}")
        print(f"   Rows: {result.total_rows:,}")
        print(f"   Duration: {result.duration_seconds:.2f}s")
    else:
        print(f"❌ Backup failed: {result.error_message}")


def example_filtered_backup():
    """Backup with filters"""
    print("\n=== Filtered Backup Example ===\n")

    from postgres_backup_plugin import DateRangeFilter, ForeignKeyFilter

    db_config = DatabaseConfig(
        host='localhost',
        port=5432,
        user='postgres',
        password='your_password',
        database='mydb'
    )

    engine = PostgresBackupEngine(db_config)

    # Define filters
    filters = {
        'orders': ForeignKeyFilter('customer_id', [1, 2, 3]),
        'invoices': DateRangeFilter('created_at', '2024-01-01', '2024-12-31'),
        'products': 'SELECT * FROM products WHERE status = \'active\''
    }

    # Create filtered backup
    result = engine.backup(
        output_path='/tmp/filtered_backup.sql',
        filters=filters,
        schema_name='my_backup',
        metadata={'purpose': 'customer_export', 'ticket': 'TASK-123'}
    )

    if result.success:
        print(f"✅ Filtered backup successful!")
        print(f"   Filtered tables: {len(filters)}")
        for table, stats in result.stats['tables'].items():
            print(f"   - {table}: {stats['rows']} rows, {stats['bytes']} bytes")
    else:
        print(f"❌ Backup failed: {result.error_message}")


def example_validate_filters():
    """Validate filters before backup"""
    print("\n=== Filter Validation Example ===\n")

    db_config = DatabaseConfig(
        host='localhost',
        port=5432,
        user='postgres',
        password='your_password',
        database='mydb'
    )

    engine = PostgresBackupEngine(db_config)

    # Invalid filter (bad column name)
    filters = {
        'users': 'SELECT * FROM users WHERE invalid_column = 123'
    }

    try:
        engine.validate_filters(filters)
        print("✅ Filters are valid")
    except Exception as e:
        print(f"❌ Filter validation failed: {e}")


def example_estimate_size():
    """Estimate backup size before running"""
    print("\n=== Size Estimation Example ===\n")

    db_config = DatabaseConfig(
        host='localhost',
        port=5432,
        user='postgres',
        password='your_password',
        database='mydb'
    )

    engine = PostgresBackupEngine(db_config)

    # Estimate size with filters
    filters = {
        'orders': 'SELECT * FROM orders WHERE created_at > \'2024-01-01\''
    }

    estimates = engine.estimate_size(filters)

    print("Estimated row counts:")
    for table, row_count in estimates.items():
        print(f"  - {table}: {row_count:,} rows")


if __name__ == '__main__':
    # Run examples
    example_basic_backup()
    example_filtered_backup()
    example_validate_filters()
    example_estimate_size()
