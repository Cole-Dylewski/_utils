#!/bin/bash
# Cross-platform virtual environment activation script
# Works on Linux, macOS, and Windows (Git Bash/WSL)

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Run 'python setup-venv.py' or 'python3 setup-venv.py' to create it."
    exit 1
fi

# Determine the activation script based on the shell
if [ -f "$VENV_DIR/bin/activate" ]; then
    # Linux/macOS
    source "$VENV_DIR/bin/activate"
    echo "✓ Virtual environment activated"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    # Windows (Git Bash)
    source "$VENV_DIR/Scripts/activate"
    echo "✓ Virtual environment activated"
else
    echo "Error: Could not find activation script"
    exit 1
fi

