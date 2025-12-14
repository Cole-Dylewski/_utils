# Quick Start Guide

Get up and running with _utils development in minutes!

## Prerequisites

- Python 3.10 or higher
- Git

## One-Command Setup

### All Platforms

```bash
python setup-venv.py
```

That's it! This single command will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Set up pre-commit hooks

## Activate Virtual Environment

After setup, activate the virtual environment:

### Linux / macOS
```bash
source .venv/bin/activate
```

### Windows PowerShell
```powershell
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt
```cmd
.venv\Scripts\activate.bat
```

## Verify Installation

```bash
# Check Python
python --version

# Run tests
pytest

# Check code quality
ruff check .
```

## Common Commands

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=_utils --cov-report=html

# Lint code
ruff check .

# Format code
ruff format .

# Type check
mypy python

# Run all quality checks (if Make is available)
make quality
```

## Next Steps

- Read [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Check [VENV_SETUP.md](VENV_SETUP.md) for detailed setup instructions
- Review [README.md](README.md) for project overview

## Need Help?

- Check [VENV_SETUP.md](VENV_SETUP.md) for troubleshooting
- Open an issue on GitHub
- Review existing issues and PRs

Happy coding! 🚀

