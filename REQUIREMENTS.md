# Requirements Files

This project uses multiple requirements files to support modular installation. All dependencies are defined in `pyproject.toml`, and these requirements files provide alternative installation methods.

## Available Requirements Files

### Base Requirements
- **`requirements.txt`** - Base package (currently no dependencies, package is modular)

### Optional Feature Requirements
- **`requirements-alpaca.txt`** - Alpaca trading API features
- **`requirements-aws.txt`** - AWS service utilities
- **`requirements-db.txt`** - Database operations (SQLAlchemy, PostgreSQL, asyncpg)
- **`requirements-fastapi.txt`** - FastAPI web framework support
- **`requirements-ml.txt`** - Machine learning utilities (numpy, pandas, scikit-learn)
- **`requirements-tableau.txt`** - Tableau integration

### Development Requirements
- **`requirements-dev.txt`** - Development dependencies (testing, linting, type checking, security scanning, build tools)

### All-in-One
- **`requirements-all.txt`** - All dependencies (all optional features + dev dependencies)

## Installation Methods

### Method 1: Using pip with requirements files

```bash
# Base installation (minimal)
pip install -r requirements.txt

# Install specific features
pip install -r requirements-aws.txt
pip install -r requirements-db.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install everything
pip install -r requirements-all.txt
```

### Method 2: Using pip with editable install and extras (Recommended)

```bash
# Base installation (minimal)
pip install -e .

# Install with specific features
pip install -e ".[aws]"
pip install -e ".[db,fastapi]"
pip install -e ".[alpaca,aws,ml]"

# Install with development dependencies
pip install -e ".[dev]"

# Install with all features and dev dependencies
pip install -e ".[alpaca,aws,db,fastapi,ml,tableau,dev]"
```

### Method 3: Using the setup script

```bash
# This automatically installs dev dependencies
python setup-venv.py
```

## Dependency Coverage

All dependencies from `pyproject.toml` are covered in these requirements files:

### Base Dependencies
- ✅ None (package is modular)

### Optional Dependencies
- ✅ `alpaca` - Alpaca trading API
- ✅ `aws` - AWS services
- ✅ `db` - Database operations
- ✅ `fastapi` - FastAPI framework
- ✅ `ml` - Machine learning
- ✅ `tableau` - Tableau integration

### Development Dependencies
- ✅ `dev` - All development tools

## Keeping Requirements in Sync

The requirements files are manually maintained to match `pyproject.toml`. To ensure they stay in sync:

1. Update dependencies in `pyproject.toml`
2. Update the corresponding requirements file(s)
3. Run `pip install -r requirements-<name>.txt` to verify

## Notes

- The `requirements.txt` files use the same version constraints as `pyproject.toml`
- All requirements files are compatible with pip
- The modular approach allows installing only what you need
- Development dependencies are separate to keep production installs minimal
