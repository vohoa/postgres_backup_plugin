# Quick Start: Clean SQL Backup

## 🚀 One Function, Clean Output

```python
from postgres_backup_plugin import PostgresBackupEngine, DatabaseConfig, BackupConfig

# Setup
db_config = DatabaseConfig(
    host='localhost',
    user='postgres',
    password='password',
    database='mydb'
)

backup_config = BackupConfig(
    clean_output=True,        # Auto-clean (default)
    target_schema='as_123'    # Optional
)

# Backup
engine = PostgresBackupEngine(db_config, backup_config)
result = engine.backup('/tmp/backup.sql')

# Done! ✅ File is clean and ready to restore
```

## ✅ What's Cleaned Automatically

- ❌ `\unrestrict lbIrFh...` → Removed
- ❌ `\c`, `\dt`, `\.` commands → Removed
- ❌ `SET search_path`, `SET default_tablespace` → Removed
- ❌ `public.users` → `users`
- ✅ Tables, data, indexes, constraints → Preserved

## 📖 Examples

### Simple Backup
```python
backup_config = BackupConfig()  # clean_output=True by default
result = engine.backup('/tmp/backup.sql')
```

### With Custom Schema
```python
backup_config = BackupConfig(target_schema='as_123')
result = engine.backup('/tmp/backup.sql')
# Output includes: SET search_path = as_123, public;
```

### Raw Output (No Cleaning)
```python
backup_config = BackupConfig(clean_output=False)
result = engine.backup('/tmp/backup_raw.sql')
```

## 🎯 Key Points

1. **Default Behavior**: Cleaning is ON by default
2. **Single Call**: No manual post-processing needed
3. **No Errors**: Removes all problematic psql commands
4. **Portable**: Works across different schemas
5. **Fast**: Minimal overhead (~50ms)

## 📚 Full Documentation

See [CLEAN_BACKUP_GUIDE.md](CLEAN_BACKUP_GUIDE.md) for complete details.

## 🧪 Test It

```bash
python test_clean_sql.py
python test_integrated_backup.py
```
