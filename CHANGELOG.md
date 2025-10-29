# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] - 2025-01-29

### Added
- Same as 1.0.1 (re-release due to build issue)

## [1.0.1] - 2025-01-29

### Added
- **Multi-Schema Support**: Added `source_schema` parameter to `backup()` method
  - Enable backing up from any PostgreSQL schema, not just 'public'
  - Useful for multi-tenant databases with separate schemas per tenant
  - Enables cross-schema migrations and schema-based data isolation
  - Default value is 'public' for backward compatibility

- **Automatic SQL Cleaning**: SQL output is now automatically cleaned by default
  - Removes schema prefixes (e.g., `public.users` → `users`)
  - Removes psql meta-commands (`\restrict`, `\unrestrict`, `\connect`, etc.)
  - Removes unnecessary SET commands
  - **Preserves COPY data blocks** - no data loss!
  - Configurable via `BackupConfig.clean_output` (default: `True`)

- **Target Schema Configuration**: Added `target_schema` option to `BackupConfig`
  - Specify target schema name for restore operations
  - Useful for restoring backups to different schema names

- **Enhanced Documentation**:
  - Complete API reference with all parameters
  - Real-world examples (multi-tenant backup, cross-schema migration, dev data)
  - Troubleshooting section with common issues
  - Development setup guide
  - 4 comprehensive real-world examples

### Changed
- Improved `_dump_table_structure()` to support schema parameter
- Updated `_get_tables()` to query from specified schema
- Modified `_build_query_for_table()` to build queries from any schema
- Enhanced pg_dump integration to clean meta-commands from output
- Expanded README from 299 to 689 lines with comprehensive documentation

### Fixed
- Fixed psql meta-commands (`\restrict`, `\unrestrict`) appearing in backup output from pg_dump
- Fixed COPY data preservation during SQL cleaning (critical bug - no data loss)
- Fixed bytes to string conversion in `CopyToStreamWrapper.write()`

### Technical Details
Modified methods to support `source_schema` parameter:
- `BackupEngine.backup(source_schema='public')`
- `BackupEngine._write_backup()`
- `BackupEngine._get_tables(schema='public')`
- `BackupEngine._backup_table()`
- `BackupEngine._dump_table_structure(schema='public')`
- `BackupEngine._build_query_for_table(schema='public')`

## [1.0.0] - 2025-10-28

### Added
- Initial release of postgres-backup-plugin
- Core backup engine with direct streaming support
- Framework-agnostic design (works with Django, Flask, FastAPI, pure Python)
- COPY format for fast backup and restore operations
- Low memory usage architecture (handles TB-sized tables)
- Comprehensive filter system with pre-built filters:
  - `DateRangeFilter` - Filter by date range
  - `ForeignKeyFilter` - Filter by foreign key relationships
  - `StatusFilter` - Filter by status column
  - `CompositeFilter` - Combine multiple filters
  - `CustomQueryFilter` - Use raw SQL queries
- Multiple export destinations:
  - `LocalFileExporter` - Export to local file system
  - `S3Exporter` - Export to AWS S3
- Django integration with `from_django_settings()` helper
- Complete documentation and examples
- Filter validation before backup
- Backup size estimation
- Production-ready error handling and logging

### Features
- Direct streaming from database to file (no temp files)
- ~25-30% faster than traditional methods
- RAM usage: ~50MB regardless of table size
- Supports PostgreSQL 9.5+
- Python 3.7+ support

### Documentation
- Comprehensive README with usage examples
- PyPI publishing guide
- Installation guide
- Example scripts for basic, Django, and custom filter usage
- Plugin architecture summary

## [0.1.0] - Development

- Initial development version
- Basic backup functionality
- Proof of concept

---

## Version History Format

### [Version Number] - YYYY-MM-DD

#### Added
- New features

#### Changed
- Changes in existing functionality

#### Deprecated
- Soon-to-be removed features

#### Removed
- Now removed features

#### Fixed
- Bug fixes

#### Security
- Vulnerability fixes
