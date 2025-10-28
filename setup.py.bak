"""
Setup script for postgres_backup_plugin
"""
from setuptools import setup, find_packages
import os

# Read README for long description
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version from __init__.py
version = {}
with open(os.path.join(here, "postgres_backup_plugin", "__init__.py")) as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line, version)
            break

setup(
    name="postgres-backup-plugin",
    version=version.get("__version__", "1.0.0"),
    author="Your Name",
    author_email="your.email@example.com",
    description="Framework-agnostic PostgreSQL backup library with filtering support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/postgres-backup-plugin",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/postgres-backup-plugin/issues",
        "Documentation": "https://github.com/yourusername/postgres-backup-plugin#readme",
        "Source Code": "https://github.com/yourusername/postgres-backup-plugin",
        "Changelog": "https://github.com/yourusername/postgres-backup-plugin/blob/main/CHANGELOG.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    include_package_data=True,
    keywords=[
        "postgresql", "postgres", "backup", "database", "sql", "copy",
        "django", "filter", "export", "s3", "restore", "dump"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: System :: Archiving :: Backup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 4.0",
    ],
    python_requires=">=3.7",
    install_requires=[
        "psycopg2-binary>=2.8.0",
    ],
    extras_require={
        "s3": ["boto3>=1.20.0"],
        "django": ["django>=3.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.990",
            "isort>=5.10.0",
        ],
        "all": [
            "boto3>=1.20.0",
            "django>=3.0",
        ],
    },
    # Remove CLI entry point if not implemented yet
    # entry_points={
    #     "console_scripts": [
    #         "pgbackup=postgres_backup_plugin.cli:main",
    #     ],
    # },
    license="MIT",
    zip_safe=False,
)
