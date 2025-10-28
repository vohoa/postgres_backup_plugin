# Installation Guide

## Quick Install

### Option 1: Direct Installation (Development)

```bash
# Navigate to plugin directory
cd postgres_backup_plugin

# Install in development mode
pip install -e .

# With S3 support
pip install -e ".[s3]"

# With Django support
pip install -e ".[django]"

# With all extras
pip install -e ".[s3,django,dev]"
```

### Option 2: From Source

```bash
# Clone or copy the postgres_backup_plugin directory

# Install dependencies
pip install -r requirements.txt

# Add to Python path (temporary)
export PYTHONPATH="${PYTHONPATH}:/path/to/postgres_backup_plugin"

# Or add to sys.path in your code
import sys
sys.path.insert(0, '/path/to/postgres_backup_plugin')
```

### Option 3: Package Installation (Future)

```bash
# Once published to PyPI
pip install postgres-backup-plugin

# With extras
pip install postgres-backup-plugin[s3,django]
```

## Verify Installation

```python
# Test import
from postgres_backup_plugin import PostgresBackupEngine
print("✅ Plugin installed successfully!")

# Check version
import postgres_backup_plugin
print(f"Version: {postgres_backup_plugin.__version__}")
```

## Dependencies

### Required
- Python 3.7+
- PostgreSQL 9.5+
- psycopg2-binary >= 2.8.0

### Optional
- boto3 >= 1.20.0 (for S3 export)
- django >= 3.0 (for Django integration)

## Integration with Existing Project

### For Your Django Project

```bash
# From your Django project root
cd /path/to/your/django/project

# Copy plugin to your project
cp -r /path/to/postgres_backup_plugin ./

# Or create a symlink
ln -s /path/to/postgres_backup_plugin ./postgres_backup_plugin

# Install dependencies
pip install psycopg2-binary boto3
```

### Import in Your Code

```python
# In your backup_service.py or views.py
from postgres_backup_plugin import (
    PostgresBackupEngine,
    DateRangeFilter,
    ForeignKeyFilter,
    S3Exporter
)

# Use it
engine = PostgresBackupEngine.from_django_settings()
result = engine.backup('/tmp/backup.sql')
```

## Troubleshooting

### Import Error: "No module named 'postgres_backup_plugin'"

**Solution 1**: Add to Python path
```python
import sys
sys.path.insert(0, '/path/to/directory/containing/postgres_backup_plugin')
```

**Solution 2**: Install in development mode
```bash
cd postgres_backup_plugin
pip install -e .
```

### Import Error: "No module named 'psycopg2'"

```bash
pip install psycopg2-binary
```

### Import Error: "No module named 'boto3'" (when using S3)

```bash
pip install boto3
```

### Database Connection Error

Check your database configuration:
```python
from postgres_backup_plugin import DatabaseConfig

db_config = DatabaseConfig(
    host='localhost',  # Check this
    port=5432,         # Check this
    user='postgres',   # Check this
    password='your_password',  # Check this
    database='mydb'    # Check this
)

# Test connection
import psycopg2
conn = psycopg2.connect(**db_config.to_dict())
print("✅ Connection successful!")
conn.close()
```

## Next Steps

1. Read the [README.md](README.md) for usage examples
2. Check [examples/](examples/) directory for code samples
3. Try basic backup: `python examples/example_basic.py`
4. Integrate with your Django project using `backup_service_plugin.py`

## Uninstall

```bash
# If installed via pip
pip uninstall postgres-backup-plugin

# If using development mode
pip uninstall postgres-backup-plugin

# Manual cleanup
rm -rf postgres_backup_plugin
```
