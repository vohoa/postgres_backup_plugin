# Publishing to PyPI - Complete Guide

Hướng dẫn chi tiết để đóng gói và publish `postgres-backup-plugin` lên PyPI.

## 📋 Yêu cầu trước khi bắt đầu

### 1. Tạo tài khoản PyPI

- **PyPI Production**: https://pypi.org/account/register/
- **TestPyPI (để test)**: https://test.pypi.org/account/register/

### 2. Cài đặt tools

```bash
# Install publishing tools
pip install --upgrade pip setuptools wheel twine build

# Verify installation
python -m pip --version
python -m twine --version
```

### 3. Setup API Token (Recommended)

Vào PyPI Account Settings → API tokens → "Add API token"

```bash
# Save token to ~/.pypirc
nano ~/.pypirc
```

Nội dung file `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # Your PyPI token

[testpypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...  # Your TestPyPI token
```

```bash
# Set permissions
chmod 600 ~/.pypirc
```

---

## 🔧 Chuẩn bị Package

### Bước 1: Cấu trúc thư mục chuẩn

```
postgres_backup_plugin/
├── postgres_backup_plugin/     # Package source code
│   ├── __init__.py
│   ├── core/
│   ├── filters/
│   └── exporters/
├── tests/                      # Test files
├── examples/                   # Example scripts
├── setup.py                    # Package configuration
├── pyproject.toml             # Modern Python packaging
├── MANIFEST.in                # Include non-Python files
├── README.md                  # Package description
├── LICENSE                    # License file
├── CHANGELOG.md               # Version history
└── requirements.txt           # Dependencies
```

### Bước 2: Tạo LICENSE file

```bash
# Create MIT License
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
```

### Bước 3: Tạo CHANGELOG.md

```bash
cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-01-28

### Added
- Initial release
- Direct streaming backup engine
- Filter system with pre-built filters
- S3 and local file exporters
- Django integration support
- Comprehensive documentation and examples

### Features
- PostgreSQL COPY format for fast backup/restore
- Low memory usage (handles TB-sized tables)
- Framework-agnostic design
- Flexible filtering per table
- Multiple export destinations
EOF
```

### Bước 4: Update setup.py

(Xem file setup.py đã được tạo, hoặc update theo bên dưới)

### Bước 5: Tạo pyproject.toml (Modern packaging)

```bash
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools-scm>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "postgres-backup-plugin"
version = "1.0.0"
description = "Framework-agnostic PostgreSQL backup library with filtering support"
readme = "README.md"
requires-python = ">=3.7"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["postgresql", "backup", "database", "postgres", "sql", "django"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Database",
    "Topic :: System :: Archiving :: Backup",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "psycopg2-binary>=2.8.0",
]

[project.optional-dependencies]
s3 = ["boto3>=1.20.0"]
django = ["django>=3.0"]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=3.0.0",
    "black>=22.0.0",
    "flake8>=4.0.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/postgres-backup-plugin"
Documentation = "https://github.com/yourusername/postgres-backup-plugin#readme"
Repository = "https://github.com/yourusername/postgres-backup-plugin"
Changelog = "https://github.com/yourusername/postgres-backup-plugin/blob/main/CHANGELOG.md"
"Bug Tracker" = "https://github.com/yourusername/postgres-backup-plugin/issues"
EOF
```

### Bước 6: Tạo MANIFEST.in

```bash
cat > MANIFEST.in << 'EOF'
# Include documentation
include README.md
include LICENSE
include CHANGELOG.md
include INSTALL.md
include PLUGIN_SUMMARY.md
include PYPI_PUBLISHING.md

# Include requirements
include requirements.txt
include requirements-dev.txt

# Include examples
recursive-include examples *.py

# Exclude unwanted files
global-exclude __pycache__
global-exclude *.py[co]
global-exclude .DS_Store
global-exclude *.swp
global-exclude .git*
EOF
```

---

## 📦 Build Package

### Bước 1: Clean old builds

```bash
# Remove old build artifacts
rm -rf build/ dist/ *.egg-info

# Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name '*.pyc' -delete
find . -type f -name '*.pyo' -delete
```

### Bước 2: Build distribution packages

```bash
# Build source distribution and wheel
python -m build

# Or using setup.py (old method)
python setup.py sdist bdist_wheel
```

Sẽ tạo ra:
```
dist/
├── postgres_backup_plugin-1.0.0-py3-none-any.whl  # Wheel file
└── postgres-backup-plugin-1.0.0.tar.gz            # Source distribution
```

### Bước 3: Verify build

```bash
# Check package contents
tar -tzf dist/postgres-backup-plugin-1.0.0.tar.gz | head -20

# Check wheel
unzip -l dist/postgres_backup_plugin-1.0.0-py3-none-any.whl | head -20

# Validate package
twine check dist/*
```

Expected output:
```
Checking dist/postgres_backup_plugin-1.0.0-py3-none-any.whl: PASSED
Checking dist/postgres-backup-plugin-1.0.0.tar.gz: PASSED
```

---

## 🧪 Test on TestPyPI (Recommended)

### Bước 1: Upload to TestPyPI

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Or with explicit credentials
twine upload --repository testpypi \
    --username __token__ \
    --password YOUR_TESTPYPI_TOKEN \
    dist/*
```

### Bước 2: Test installation from TestPyPI

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    postgres-backup-plugin

# Test import
python -c "from postgres_backup_plugin import PostgresBackupEngine; print('✅ Import successful!')"

# Deactivate and cleanup
deactivate
rm -rf test_env
```

### Bước 3: Fix issues if any

Nếu có vấn đề:
1. Fix code
2. Update version in setup.py và pyproject.toml
3. Rebuild: `python -m build`
4. Re-upload: `twine upload --repository testpypi dist/*`

---

## 🚀 Publish to Production PyPI

### Bước 1: Final checks

```bash
# 1. All tests pass
pytest tests/

# 2. Code quality
black postgres_backup_plugin/
flake8 postgres_backup_plugin/

# 3. Documentation complete
# Check README.md, CHANGELOG.md, etc.

# 4. Version is correct
grep version setup.py
grep version pyproject.toml
```

### Bước 2: Upload to PyPI

```bash
# Upload to production PyPI
twine upload dist/*

# Or with explicit credentials
twine upload --username __token__ \
    --password YOUR_PYPI_TOKEN \
    dist/*
```

### Bước 3: Verify publication

```bash
# Check on PyPI
# Visit: https://pypi.org/project/postgres-backup-plugin/

# Test installation
pip install postgres-backup-plugin

# Test import
python -c "from postgres_backup_plugin import PostgresBackupEngine; print('✅ Works!')"
```

---

## 📝 After Publishing

### 1. Tag release on Git

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### 2. Create GitHub Release

Go to GitHub → Releases → Create new release
- Tag: v1.0.0
- Title: Version 1.0.0
- Description: Copy from CHANGELOG.md

### 3. Update documentation

```bash
# Update INSTALL.md
echo "
## Install from PyPI

\`\`\`bash
pip install postgres-backup-plugin

# With extras
pip install postgres-backup-plugin[s3,django]
\`\`\`
" >> INSTALL.md
```

---

## 🔄 Publishing Updates

### For bug fixes (1.0.0 → 1.0.1)

```bash
# 1. Update version
sed -i 's/version = "1.0.0"/version = "1.0.1"/' setup.py
sed -i 's/version = "1.0.0"/version = "1.0.1"/' pyproject.toml

# 2. Update CHANGELOG.md
# Add section for 1.0.1

# 3. Rebuild and publish
rm -rf dist/
python -m build
twine check dist/*
twine upload dist/*
```

### For new features (1.0.0 → 1.1.0)

Same process, update version to 1.1.0

### For breaking changes (1.0.0 → 2.0.0)

Same process, update version to 2.0.0

---

## 🛠️ Automation Script

Create `publish.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Publishing postgres-backup-plugin to PyPI"

# Check if version argument provided
if [ -z "$1" ]; then
    echo "Usage: ./publish.sh <version>"
    exit 1
fi

VERSION=$1

echo "📝 Updating version to $VERSION..."
sed -i "s/version = \".*\"/version = \"$VERSION\"/" setup.py
sed -i "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

echo "🧹 Cleaning old builds..."
rm -rf build/ dist/ *.egg-info

echo "🔨 Building package..."
python -m build

echo "✅ Checking package..."
twine check dist/*

echo "🧪 Testing on TestPyPI? (y/n)"
read -r test_pypi
if [ "$test_pypi" = "y" ]; then
    echo "📤 Uploading to TestPyPI..."
    twine upload --repository testpypi dist/*
    echo "✅ Published to TestPyPI"
    echo "Test with: pip install --index-url https://test.pypi.org/simple/ postgres-backup-plugin"
    echo ""
    echo "Continue to production PyPI? (y/n)"
    read -r continue_prod
    if [ "$continue_prod" != "y" ]; then
        exit 0
    fi
fi

echo "📤 Uploading to PyPI..."
twine upload dist/*

echo "✅ Published to PyPI!"
echo "📦 Package: https://pypi.org/project/postgres-backup-plugin/$VERSION/"
echo ""
echo "📌 Don't forget to:"
echo "  - git tag -a v$VERSION -m 'Release $VERSION'"
echo "  - git push origin v$VERSION"
echo "  - Create GitHub release"
```

Make executable:
```bash
chmod +x publish.sh
```

Usage:
```bash
./publish.sh 1.0.1
```

---

## 📚 Useful Commands

```bash
# Check package on PyPI
pip search postgres-backup  # (deprecated, use website)

# View package info
pip show postgres-backup-plugin

# Download without installing
pip download postgres-backup-plugin

# Install specific version
pip install postgres-backup-plugin==1.0.0

# Upgrade
pip install --upgrade postgres-backup-plugin

# Uninstall
pip uninstall postgres-backup-plugin
```

---

## 🐛 Troubleshooting

### Error: "File already exists"

PyPI không cho upload cùng version 2 lần. Solutions:
1. Bump version number
2. Delete release on PyPI (not recommended)

### Error: "Invalid distribution"

```bash
# Validate package
twine check dist/*

# Check MANIFEST.in
python setup.py check

# Rebuild clean
rm -rf dist/ build/ *.egg-info
python -m build
```

### Error: "Authentication failed"

Check:
1. API token correct in ~/.pypirc
2. Token not expired
3. Token has upload permissions

### Error: "README rendering failed"

PyPI sử dụng strict Markdown. Validate:
```bash
# Install validation tool
pip install readme-renderer

# Check README
python -m readme_renderer README.md -o /tmp/test.html
```

---

## 🔐 Security Best Practices

1. **NEVER commit tokens to Git**
   ```bash
   # Add to .gitignore
   echo ".pypirc" >> .gitignore
   echo "dist/" >> .gitignore
   echo "build/" >> .gitignore
   ```

2. **Use API tokens, not passwords**

3. **Use token with limited scope**
   - Create per-project tokens
   - Set expiration dates

4. **Enable 2FA on PyPI account**

---

## 📊 Statistics & Monitoring

After publishing, monitor:

- **PyPI Stats**: https://pypistats.org/packages/postgres-backup-plugin
- **Download counts**: See on PyPI project page
- **GitHub Stars/Forks**: If using GitHub

---

## ✅ Checklist Before Publishing

- [ ] All tests pass
- [ ] Code quality checked (black, flake8)
- [ ] README.md complete and formatted
- [ ] CHANGELOG.md updated
- [ ] Version number updated in all files
- [ ] LICENSE file exists
- [ ] Dependencies correct in setup.py
- [ ] Examples work
- [ ] Documentation complete
- [ ] Tested on TestPyPI
- [ ] Git committed and pushed
- [ ] Ready to tag release

---

## 📖 Resources

- **PyPI**: https://pypi.org/
- **TestPyPI**: https://test.pypi.org/
- **Packaging Guide**: https://packaging.python.org/
- **Twine Docs**: https://twine.readthedocs.io/
- **Setuptools Docs**: https://setuptools.pypa.io/

---

## 🎉 Congratulations!

Your package is now on PyPI! Users can install with:

```bash
pip install postgres-backup-plugin
```

Share your package:
- Tweet about it
- Post on Reddit r/Python
- Add to awesome-python lists
- Write a blog post
