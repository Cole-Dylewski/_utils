# Fish shell virtual environment activation script

set -l SCRIPT_DIR (dirname (status --current-filename))
set -l VENV_DIR "$SCRIPT_DIR/.venv"
set -l ACTIVATE_SCRIPT "$VENV_DIR/bin/activate.fish"

if not test -d "$VENV_DIR"
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Run 'python setup-venv.py' or 'python3 setup-venv.py' to create it."
    exit 1
end

if test -f "$ACTIVATE_SCRIPT"
    source "$ACTIVATE_SCRIPT"
    echo "✓ Virtual environment activated"
else
    echo "Error: Could not find activation script at $ACTIVATE_SCRIPT"
    exit 1
end

