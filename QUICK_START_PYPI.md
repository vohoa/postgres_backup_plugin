# Quick Start Guide - Publishing to PyPI

5 phút để publish plugin lên PyPI!

## 🚀 Bước 1: Setup PyPI Account (One-time)

```bash
# 1. Đăng ký tài khoản
# TestPyPI (for testing): https://test.pypi.org/account/register/
# Production PyPI: https://pypi.org/account/register/

# 2. Tạo API token trên PyPI
# Vào: Account Settings → API tokens → "Add API token"

# 3. Save token vào ~/.pypirc
nano ~/.pypirc
```

Nội dung `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-PRODUCTION-TOKEN-HERE

[testpypi]
username = __token__
password = pypi-YOUR-TEST-TOKEN-HERE
```

```bash
# 4. Set permissions
chmod 600 ~/.pypirc
```

## 📦 Bước 2: Install Tools

```bash
cd postgres_backup_plugin

# Install required tools
pip install --upgrade pip setuptools wheel twine build

# Verify
python -m pip --version
python -m twine --version
python -m build --version
```

## ✏️ Bước 3: Update Information

### 3.1. Update Author Info

```bash
# Edit setup.py
nano setup.py
# Change:
#   author="Your Name"
#   author_email="your.email@example.com"
#   url="https://github.com/yourusername/postgres-backup-plugin"
```

### 3.2. Update pyproject.toml

```bash
nano pyproject.toml
# Change same info as setup.py
```

### 3.3. Update README (Optional)

```bash
nano README.md
# Add your GitHub username, examples, etc.
```

## 🧪 Bước 4: Test Build Locally

```bash
# Clean old builds
rm -rf build/ dist/ *.egg-info

# Build package
python -m build

# Check output
ls -la dist/
# Should see:
#   postgres_backup_plugin-1.0.0-py3-none-any.whl
#   postgres-backup-plugin-1.0.0.tar.gz

# Validate package
twine check dist/*
# Should see: PASSED
```

## 🧪 Bước 5: Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI
./publish.sh 1.0.0 test

# Or manually:
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    postgres-backup-plugin

# Test import
python -c "from postgres_backup_plugin import PostgresBackupEngine; print('✅ Works!')"
```

## 🚀 Bước 6: Publish to Production PyPI

### Option A: Using Automation Script (Recommended)

```bash
# Interactive mode
./publish.sh 1.0.0

# Or direct to production
./publish.sh 1.0.0 prod
```

### Option B: Manual

```bash
# Upload to PyPI
twine upload dist/*

# Verify
pip install postgres-backup-plugin
python -c "from postgres_backup_plugin import PostgresBackupEngine; print('✅ Published!')"
```

## 📝 Bước 7: Post-Publishing

```bash
# Tag release
git add -A
git commit -m "Release version 1.0.0"
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin main
git push origin v1.0.0

# Create GitHub Release (if using GitHub)
# Go to: https://github.com/yourusername/postgres-backup-plugin/releases/new
# - Tag: v1.0.0
# - Title: Version 1.0.0
# - Description: Copy from CHANGELOG.md
```

## 🔄 Publishing Updates

```bash
# For version 1.0.1 (bug fix)
./publish.sh 1.0.1 test    # Test first
./publish.sh 1.0.1 prod    # Then production

# Don't forget to update CHANGELOG.md!
```

## ✅ Complete Checklist

Before publishing:

- [ ] Author info updated in setup.py
- [ ] Author info updated in pyproject.toml
- [ ] GitHub URL updated (if applicable)
- [ ] README.md complete
- [ ] CHANGELOG.md updated
- [ ] Tests pass (if any)
- [ ] Built and validated locally
- [ ] Tested on TestPyPI
- [ ] Ready to publish to production!

## 🆘 Troubleshooting

### "File already exists"
PyPI doesn't allow re-uploading same version. Bump version number.

### "Invalid distribution"
```bash
twine check dist/*
# Fix any issues shown
```

### "Authentication failed"
Check ~/.pypirc token is correct and not expired.

### Package not found after upload
Wait 1-2 minutes, PyPI needs time to index.

## 📚 Useful Commands

```bash
# Check package on PyPI
# Visit: https://pypi.org/project/postgres-backup-plugin/

# Install from PyPI
pip install postgres-backup-plugin

# Install with extras
pip install postgres-backup-plugin[s3,django]

# Upgrade
pip install --upgrade postgres-backup-plugin

# View info
pip show postgres-backup-plugin
```

## 🎉 Success!

Your package is now on PyPI! Anyone can install with:

```bash
pip install postgres-backup-plugin
```

**Package URL:** https://pypi.org/project/postgres-backup-plugin/

---

## 📖 Detailed Guide

For more details, see [PYPI_PUBLISHING.md](PYPI_PUBLISHING.md)
