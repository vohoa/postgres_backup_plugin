#!/usr/bin/env python3
"""
Example: Backup from custom source schema with automatic prefix removal

This example demonstrates how to:
1. Backup from a non-default schema (e.g., 'as_59' instead of 'public')
2. Automatically remove the source schema prefix from all SQL statements
3. Prepare the backup for restore into a different target schema

Use case:
- Migrating data from one schema to another
- Creating schema-independent backups
- Multi-tenant applications with per-tenant schemas
"""

from postgres_backup_plugin import PostgresBackupEngine, DatabaseConfig, BackupConfig
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Example 1: Backup from custom schema with cleaning
def backup_custom_schema():
    """Backup from 'as_59' schema and remove prefix"""

    db_config = DatabaseConfig(
        host='localhost',
        port=5432,
        database='mydb',
        user='postgres',
        password='your_password'
    )

    backup_config = BackupConfig(
        clean_output=True,  # Enable automatic cleaning
        target_schema='production',  # Where to restore
    )

    engine = PostgresBackupEngine(db_config, backup_config)

    result = engine.backup(
        output_path='backups/as_59_to_production.sql',
        source_schema='as_59',  # Backup FROM this schema
        schema_name='production',  # Restore TO this schema
        metadata={
            'source': 'as_59',
            'target': 'production',
            'purpose': 'Schema migration'
        }
    )

    if result.success:
        print(f"✓ Successfully backed up {result.tables_count} tables")
        print(f"  Source schema: as_59")
        print(f"  Target schema: production")
        print(f"  All 'as_59.' prefixes removed from SQL")
        print(f"  Ready to restore with: psql -d mydb -f {result.file_path}")
    else:
        print(f"✗ Backup failed: {result.error_message}")

    return result


# Example 2: Backup multi-tenant data
def backup_tenant_schema(tenant_id: str, output_dir: str = 'backups'):
    """
    Backup a tenant-specific schema

    Args:
        tenant_id: Tenant identifier (e.g., 'tenant_123')
        output_dir: Where to save backups
    """

    db_config = DatabaseConfig(
        host='localhost',
        port=5432,
        database='saas_app',
        user='postgres',
        password='your_password'
    )

    backup_config = BackupConfig(
        clean_output=True,
        target_schema='tenant_template',  # Generic template schema
    )

    engine = PostgresBackupEngine(db_config, backup_config)

    # Backup from tenant-specific schema
    source_schema = f'tenant_{tenant_id}'
    output_file = f'{output_dir}/{source_schema}_backup.sql'

    result = engine.backup(
        output_path=output_file,
        source_schema=source_schema,  # e.g., 'tenant_123'
        schema_name='tenant_template',  # Generic restore target
        metadata={
            'tenant_id': tenant_id,
            'backup_type': 'tenant_snapshot',
        }
    )

    if result.success:
        print(f"✓ Tenant backup complete")
        print(f"  Tenant: {tenant_id}")
        print(f"  Schema: {source_schema}")
        print(f"  File: {output_file}")
        print(f"  Size: {result.size_bytes / 1024 / 1024:.2f} MB")
        print(f"\n  The backup is schema-agnostic and can be restored")
        print(f"  to any target schema by setting search_path")

    return result


# Example 3: Compare what gets cleaned
def show_cleaning_example():
    """Demonstrate the schema prefix cleaning"""

    print("=" * 70)
    print("SCHEMA PREFIX CLEANING EXAMPLE")
    print("=" * 70)

    print("\nBEFORE CLEANING (with source_schema='as_59'):")
    print("-" * 70)
    before = """
    CREATE TABLE as_59.auth_user (
        id integer NOT NULL,
        username varchar(150) NOT NULL
    );

    ALTER TABLE as_59.auth_user ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);

    CREATE INDEX auth_user_username_idx ON as_59.auth_user (username);

    ALTER TABLE as_59.auth_user_profile
        ADD CONSTRAINT fk_user
        FOREIGN KEY (user_id) REFERENCES as_59.auth_user(id);

    COPY as_59.auth_user (id, username) FROM stdin;
    1\tuser1
    2\tuser2
    \\.
    """
    print(before)

    print("\nAFTER CLEANING (all 'as_59.' prefixes removed):")
    print("-" * 70)
    after = """
    -- Cleaned SQL backup
    -- Target schema: production

    SET search_path = production, public;

    CREATE TABLE auth_user (
        id integer NOT NULL,
        username varchar(150) NOT NULL
    );

    ALTER TABLE auth_user ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);

    CREATE INDEX auth_user_username_idx ON auth_user (username);

    ALTER TABLE auth_user_profile
        ADD CONSTRAINT fk_user
        FOREIGN KEY (user_id) REFERENCES auth_user(id);

    COPY auth_user (id, username) FROM stdin;
    1\tuser1
    2\tuser2
    \\.
    """
    print(after)

    print("\n" + "=" * 70)
    print("BENEFITS:")
    print("=" * 70)
    print("✓ Schema-independent SQL (can restore to any schema)")
    print("✓ Cleaner, more readable backup files")
    print("✓ Easier schema migrations and data movement")
    print("✓ Works with any source schema name (not just 'public')")
    print("=" * 70)


if __name__ == '__main__':
    # Show what the cleaning does
    show_cleaning_example()

    # Uncomment to run actual backups:
    # backup_custom_schema()
    # backup_tenant_schema('123')
