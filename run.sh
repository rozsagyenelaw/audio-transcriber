#!/bin/bash
# Run Meeting Transcriber in development mode

cd "$(dirname "$0")"

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

echo "Starting Meeting Transcriber..."
python3 src/main_window.py
