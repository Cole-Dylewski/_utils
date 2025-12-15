# Installation

## Requirements

- Python 3.10 or higher
- pip

## Quick Installation

### Install All Dependencies

```bash
pip install -r requirements.txt
```

### Install Package in Editable Mode

```bash
pip install -e .
```

This installs the package in development mode, allowing you to make changes without reinstalling.

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Cole-Dylewski/_utils.git
cd _utils
```

### 2. Set Up Virtual Environment

```bash
# Create and configure virtual environment
python setup.py
```

This will:
- Check Python version (requires 3.10+)
- Create a `.venv` virtual environment
- Install all dependencies
- Install pre-commit hooks

### 3. Activate Virtual Environment

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**
```cmd
.venv\Scripts\activate.bat
```

### 4. Verify Installation

```bash
python -c "import _utils; print(_utils.__version__)"
```

## All Dependencies Included

All dependencies are installed by default when you install the package. This includes:
- AWS services (boto3, botocore)
- Database operations (SQLAlchemy, psycopg, asyncpg)
- Alpaca trading APIs (alpaca-trade-api)
- FastAPI support (fastapi, pydantic, uvicorn)
- Machine learning utilities (numpy, pandas, scikit-learn)
- Tableau integration (tableauserverclient)
- Testing and development tools (pytest, ruff, mypy, etc.)

## Troubleshooting

### Python Version Issues

Ensure Python 3.10+ is installed:
```bash
python --version
```

### Virtual Environment Issues

If virtual environment creation fails:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
```

### Permission Errors

On Linux/macOS, you may need to make scripts executable:
```bash
chmod +x setup.py
```

### PowerShell Execution Policy

On Windows, if you get execution policy errors:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
