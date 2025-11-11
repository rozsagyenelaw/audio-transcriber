#!/bin/bash
# Simple launcher for CLI version of Meeting Transcriber

cd "$(dirname "$0")/src"

echo "Starting Meeting Transcriber (CLI Mode)..."
echo ""
echo "Options:"
echo "  ./run_cli.sh          - Interactive device selection"
echo "  ./run_cli.sh --auto   - Auto-select default device"
echo "  ./run_cli.sh -d 2     - Use specific device"
echo "  ./run_cli.sh --list   - List devices only"
echo ""

python3 cli_transcriber.py "$@"
