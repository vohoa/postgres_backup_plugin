#!/usr/bin/env python3
"""
Example: Clean SQL Backup with Automatic Cleaning

This example shows how to use the backup() method with automatic SQL cleaning.
The output SQL file will be clean and ready to restore without errors.
"""

from postgres_backup_plugin import PostgresBackupEngine, DatabaseConfig, BackupConfig


def example_simple_clean_backup():
    """
    Simplest example - automatic cleaning enabled by default
    """
    print("Example 1: Simple Clean Backup")
    print("-" * 60)

    # Database configuration
    db_config = DatabaseConfig(
        host='localhost',
        port=5432,
        user='postgres',
        password='your_password',
        database='mydb'
    )

    # Backup configuration (clean_output=True by default)
    backup_config = BackupConfig()

    # Create engine
    engine = PostgresBackupEngine(db_config, backup_config)

    # Single function call!
    result = engine.backup('/tmp/backup_clean.sql')

    if result.success:
        print(f"✅ Backup successful!")
        print(f"   File: {result.file_path}")
        print(f"   Size: {result.size_bytes} bytes")
        print(f"   Tables: {result.tables_count}")
        print(f"   Rows: {result.total_rows}")
        print(f"   Duration: {result.duration_seconds:.2f}s")
        print(f"   Cleaned: {result.metadata.get('cleaned', False)}")
    else:
        print(f"❌ Backup failed: {result.error_message}")

    print()


def example_with_target_schema():
    """
    Example with custom target schema
    """
    print("Example 2: Clean Backup with Target Schema")
    print("-" * 60)

    db_config = DatabaseConfig(
        host='localhost',
        port=5432,
        user='postgres',
        password='your_password',
        database='mydb'
    )

    # Specify target schema for cleaned output
    backup_config = BackupConfig(
        clean_output=True,
        target_schema='as_123'  # Custom schema name
    )

    engine = PostgresBackupEngine(db_config, backup_config)
    result = engine.backup('/tmp/backup_as_123.sql')

    if result.success:
        print(f"✅ Backup created with target schema 'as_123'")
        print(f"   The SQL file includes: SET search_path = as_123, public;")
        print(f"   All public. prefixes removed")
    else:
        print(f"❌ Backup failed: {result.error_message}")

    print()


def example_with_filters():
    """
    Example with filters and cleaning
    """
    print("Example 3: Filtered Clean Backup")
    print("-" * 60)

    db_config = DatabaseConfig(
        host='localhost',
        port=5432,
        user='postgres',
        password='your_password',
        database='mydb'
    )

    backup_config = BackupConfig(
        clean_output=True,
        target_schema='as_123',
        excluded_tables=['django_migrations', 'auth_permission']
    )

    engine = PostgresBackupEngine(db_config, backup_config)

    # Apply filters to specific tables
    filters = {
        'users': "SELECT * FROM users WHERE active = true",
        'orders': "SELECT * FROM orders WHERE created_at >= NOW() - INTERVAL '30 days'"
    }

    result = engine.backup(
        '/tmp/backup_filtered_clean.sql',
        filters=filters,
        metadata={'backup_type': 'filtered_monthly'}
    )

    if result.success:
        print(f"✅ Filtered backup created and cleaned")
        print(f"   Tables backed up: {result.tables_count}")
        print(f"   Total rows: {result.total_rows}")
    else:
        print(f"❌ Backup failed: {result.error_message}")

    print()


def example_raw_backup():
    """
    Example with cleaning disabled (raw output)
    """
    print("Example 4: Raw Backup (No Cleaning)")
    print("-" * 60)

    db_config = DatabaseConfig(
        host='localhost',
        port=5432,
        user='postgres',
        password='your_password',
        database='mydb'
    )

    # Disable cleaning for raw output
    backup_config = BackupConfig(
        clean_output=False  # Get raw pg_dump output
    )

    engine = PostgresBackupEngine(db_config, backup_config)
    result = engine.backup('/tmp/backup_raw.sql')

    if result.success:
        print(f"✅ Raw backup created (not cleaned)")
        print(f"   This file will contain all original pg_dump output")
        print(f"   Including SET commands, schema prefixes, etc.")
    else:
        print(f"❌ Backup failed: {result.error_message}")

    print()


def example_comparison():
    """
    Create both cleaned and raw backups for comparison
    """
    print("Example 5: Create Both Cleaned and Raw Backups")
    print("-" * 60)

    db_config = DatabaseConfig(
        host='localhost',
        port=5432,
        user='postgres',
        password='your_password',
        database='mydb'
    )

    # Create cleaned backup
    clean_config = BackupConfig(clean_output=True, target_schema='as_123')
    clean_engine = PostgresBackupEngine(db_config, clean_config)
    clean_result = clean_engine.backup('/tmp/backup_cleaned.sql')

    # Create raw backup
    raw_config = BackupConfig(clean_output=False)
    raw_engine = PostgresBackupEngine(db_config, raw_config)
    raw_result = raw_engine.backup('/tmp/backup_raw.sql')

    if clean_result.success and raw_result.success:
        print(f"✅ Both backups created successfully")
        print(f"\nCleaned backup:")
        print(f"   File: {clean_result.file_path}")
        print(f"   Size: {clean_result.size_bytes} bytes")
        print(f"\nRaw backup:")
        print(f"   File: {raw_result.file_path}")
        print(f"   Size: {raw_result.size_bytes} bytes")
        print(f"\nYou can now compare the two files to see the difference!")

    print()


if __name__ == '__main__':
    print("=" * 60)
    print("PostgreSQL Clean Backup Examples")
    print("=" * 60)
    print()

    print("These examples show how to use the integrated clean backup feature.")
    print("To run these examples, update the database credentials and uncomment")
    print("the example you want to run.")
    print()

    # Uncomment the example you want to run:
    # example_simple_clean_backup()
    # example_with_target_schema()
    # example_with_filters()
    # example_raw_backup()
    # example_comparison()

    print("=" * 60)
    print("KEY POINTS:")
    print("=" * 60)
    print("""
1. ✅ AUTOMATIC CLEANING (Default)
   backup_config = BackupConfig(clean_output=True)  # Default

2. ✅ NO MANUAL POST-PROCESSING
   result = engine.backup('/path/to/backup.sql')  # Done!

3. ✅ REMOVES PROBLEMATIC CONTENT
   - \\unrestrict commands
   - \\c, \\dt, \\. commands
   - SET search_path, SET default_tablespace, etc.
   - public. schema prefixes

4. ✅ OPTIONAL TARGET SCHEMA
   backup_config.target_schema = 'as_123'

5. ✅ DISABLE IF NEEDED
   backup_config.clean_output = False  # Get raw output

6. ✅ WORKS WITH ALL FEATURES
   - Filters
   - Excluded tables
   - Custom metadata
   - Schema names
""")
    print()
