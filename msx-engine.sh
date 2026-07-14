#!/bin/bash
VENV_DIR=".venv"

# Enable nullglob and dotglob so * catches hidden files and doesn't literalize if empty
shopt -s nullglob dotglob
files=( "$VENV_DIR"/* )
shopt -u nullglob dotglob

if [ ${#files[@]} -gt 0 ]; then
    ./$VENV_DIR/bin/python main.py "$@"
else
    # Create the virtual environment if it does not exist
    echo "Directory is empty, creating virtual environment..."
    python3 -m venv $VENV_DIR
fi
