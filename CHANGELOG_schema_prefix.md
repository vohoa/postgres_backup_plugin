# Changelog: Custom Source Schema Prefix Removal

## Feature Added: Dynamic Schema Prefix Removal

### Summary
Enhanced the SQL cleaning feature to support removal of ANY source schema prefix, not just the hardcoded 'public' schema.

### Changes Made

#### 1. Core Function Updates

**File: `postgres_backup_plugin/core/backup_engine.py`**

- **`_clean_sql_content()`**
  - Added parameter: `source_schema: str = 'public'`
  - Now dynamically removes schema prefix based on `source_schema` parameter
  - Uses `re.escape()` to safely handle schema names with special characters
  - Applies to all SQL statement types:
    - CREATE TABLE, ALTER TABLE, DROP TABLE
    - CREATE INDEX, ALTER INDEX
    - CREATE SEQUENCE, ALTER SEQUENCE
    - COPY statements
    - FOREIGN KEY REFERENCES
    - GRANT/REVOKE statements
    - SELECT setval() calls
    - And more...

- **`_clean_backup_file()`**
  - Added parameter: `source_schema: str = 'public'`
  - Passes `source_schema` to `_clean_sql_content()`

- **`backup()`**
  - Updated call to `_clean_backup_file()` to pass `source_schema` parameter
  - Now correctly removes prefix from custom schemas during backup

- **`from_django_settings()`**
  - Added parameter: `backup_config: Optional[BackupConfig] = None`
  - Allows passing custom BackupConfig when creating from Django settings

#### 2. Documentation

**Updated Files:**
- `README.md` - Enhanced Multi-Schema Backup section
- Added examples:
  - `examples/example_custom_source_schema.py` - Comprehensive examples
  - `test_custom_schema.py` - Test script for custom schemas
  - `demo_clean_as59.py` - Real-world demo with SQL file

#### 3. Testing

**Added Test Suite:**
- `test_schema_prefix_removal.py` - 8 unit tests covering:
  - Removal of 'public' prefix
  - Removal of custom schema prefix (e.g., 'as_59')
  - Removal of tenant schema prefix (e.g., 'tenant_123')
  - Preservation of COPY data blocks
  - Complex SQL statements with multiple references
  - SELECT setval() sequence cleanup
  - Disabling prefix removal when needed

**Test Results:** ✅ All 8 tests passing

### Usage Examples

#### Before (hardcoded to 'public'):
```python
# Only worked with 'public' schema
result = engine.backup(
    output_path='backup.sql',
    source_schema='as_59'  # Would backup from as_59, but cleaning would try to remove 'public.'
)
```

#### After (dynamic schema):
```python
# Now correctly removes 'as_59.' prefix
result = engine.backup(
    output_path='backup.sql',
    source_schema='as_59',  # Backup FROM this schema
    schema_name='new_schema'  # Restore TO this schema
)

# Works with ANY schema name
result = engine.backup(
    output_path='backup.sql',
    source_schema='tenant_123',  # Removes 'tenant_123.' prefix
    schema_name='tenant_template'
)
```

### Benefits

1. **Schema-Independent Backups**: Create portable SQL backups that can be restored to any schema
2. **Multi-Tenant Support**: Easy backup/restore for multi-tenant applications with per-tenant schemas
3. **Schema Migration**: Simplify migrations from one schema to another
4. **Cleaner SQL**: Remove unnecessary schema prefixes for better readability
5. **Flexible**: Works with ANY schema name (not limited to 'public')

### Backward Compatibility

✅ **Fully backward compatible**
- Default `source_schema='public'` maintains existing behavior
- All existing code continues to work without changes
- Optional parameters don't affect existing functionality

### Use Cases

1. **Multi-tenant SaaS applications**
   - Each tenant has their own schema (tenant_1, tenant_2, etc.)
   - Backup individual tenant data
   - Restore to a template schema

2. **Schema-based environments**
   - development, staging, production schemas
   - Backup from one environment, restore to another

3. **Data migration**
   - Move data from old schema to new schema
   - Rename schemas without SQL modifications

4. **Legacy database cleanup**
   - Remove old schema prefixes
   - Prepare data for new schema structure

### Testing Checklist

- [x] Unit tests for prefix removal
- [x] Test with 'public' schema (default)
- [x] Test with custom schema names
- [x] Test with schema names containing special characters
- [x] Test COPY data preservation
- [x] Test complex SQL statements
- [x] Test backward compatibility
- [x] Real-world demo with actual SQL file

### Files Modified

```
postgres_backup_plugin/
├── core/
│   └── backup_engine.py          # Core logic updated
├── examples/
│   └── example_custom_source_schema.py  # New example
├── test_schema_prefix_removal.py    # New tests
├── test_custom_schema.py            # New demo script
├── demo_clean_as59.py               # Real-world demo
├── README.md                        # Documentation updated
└── CHANGELOG_schema_prefix.md       # This file
```

### Performance Impact

⚡ **Minimal performance impact**
- Regex compilation happens once per cleaning operation
- String replacement is efficient with compiled patterns
- No additional database queries
- Memory usage unchanged

### Future Enhancements

Potential future improvements:
- [ ] Support for multiple source schemas in one backup
- [ ] Schema mapping (rename schemas during cleaning)
- [ ] Whitelist/blacklist for schema prefix removal
- [ ] GUI tool for SQL file cleaning

---

**Date**: 2025-10-30
**Version**: 1.0.4 (proposed)
**Author**: Dragon Team
