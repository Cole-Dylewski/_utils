# Virtual Environment Setup Guide

This guide explains how to set up and activate the virtual environment for _utils development on different operating systems.

## Quick Start

### All Platforms (Recommended)

The easiest way to set up the virtual environment is using the cross-platform Python script:

```bash
python setup-venv.py
# or
python3 setup-venv.py
```

This script will:
1. Check that Python 3.10+ is installed
2. Create a `.venv` directory
3. Install the package with development dependencies
4. Install pre-commit hooks

## Platform-Specific Instructions

### Linux / macOS

#### Option 1: Python Script (Recommended)
```bash
python3 setup-venv.py
source .venv/bin/activate
```

#### Option 2: Shell Script
```bash
bash setup-dev.sh
source .venv/bin/activate
```

#### Option 3: Manual Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

### Windows

#### Option 1: Python Script (Recommended)
```powershell
python setup-venv.py
.venv\Scripts\Activate.ps1
```

#### Option 2: PowerShell Script
```powershell
.\setup-dev.ps1
.venv\Scripts\Activate.ps1
```

#### Option 3: Command Prompt
```cmd
python setup-venv.py
.venv\Scripts\activate.bat
```

#### Option 4: Manual Setup
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pre-commit install
```

## Activation Scripts

We provide convenient activation scripts for different shells:

### Linux / macOS
- **Bash/Zsh**: `source activate-venv.sh` or `source .venv/bin/activate`
- **Fish**: `source activate-venv.fish` or `source .venv/bin/activate.fish`
- **Csh**: `source .venv/bin/activate.csh`

### Windows
- **PowerShell**: `.\activate-venv.ps1` or `.venv\Scripts\Activate.ps1`
- **Command Prompt**: `activate-venv.bat` or `.venv\Scripts\activate.bat`
- **Git Bash**: `source activate-venv.sh` or `source .venv/Scripts/activate`

## Verification

After activation, verify the setup:

```bash
# Check Python version
python --version  # Should show Python 3.10+

# Check that package is installed
python -c "import _utils; print(_utils.__file__)"

# Check that dev tools are available
pytest --version
ruff --version
mypy --version
pre-commit --version
```

## Troubleshooting

### Python Version Issues

**Error**: `Python 3.10 or higher is required`

**Solution**: Install Python 3.10 or higher from [python.org](https://www.python.org/downloads/)

### Virtual Environment Not Found

**Error**: `Virtual environment not found`

**Solution**: Run `python setup-venv.py` to create the virtual environment

### Permission Errors (Linux/macOS)

**Error**: `Permission denied`

**Solution**: 
```bash
chmod +x setup-venv.py
chmod +x activate-venv.sh
```

### PowerShell Execution Policy (Windows)

**Error**: `cannot be loaded because running scripts is disabled`

**Solution**: Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### pip Install Errors

**Error**: `Failed to install package`

**Solution**: 
1. Upgrade pip: `python -m pip install --upgrade pip`
2. Check internet connection
3. Try installing without editable mode: `pip install -e ".[dev]" --no-cache-dir`

### Pre-commit Installation Fails

**Warning**: `pre-commit not available`

**Solution**: This is not critical. Pre-commit hooks are optional but recommended. You can install manually:
```bash
pip install pre-commit
pre-commit install
```

## Deactivating

To deactivate the virtual environment:

- **Linux/macOS/Windows (all shells)**: `deactivate`

## Recreating the Virtual Environment

To start fresh:

```bash
# Remove existing venv
rm -rf .venv  # Linux/macOS
rmdir /s .venv  # Windows Command Prompt
Remove-Item -Recurse -Force .venv  # Windows PowerShell

# Create new venv
python setup-venv.py
```

## IDE Integration

### VS Code

1. Open the project in VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type "Python: Select Interpreter"
4. Choose `.venv/bin/python` (Linux/macOS) or `.venv\Scripts\python.exe` (Windows)

### PyCharm

1. Open the project in PyCharm
2. Go to File → Settings → Project → Python Interpreter
3. Click the gear icon → Add
4. Select "Existing environment"
5. Choose `.venv/bin/python` (Linux/macOS) or `.venv\Scripts\python.exe` (Windows)

## Next Steps

After setting up the virtual environment:

1. **Run tests**: `pytest`
2. **Check code quality**: `make quality` or `ruff check . && mypy python/_utils`
3. **Format code**: `ruff format .`
4. **Run pre-commit hooks**: `pre-commit run --all-files`

See [CONTRIBUTING.md](CONTRIBUTING.md) for more development guidelines.

