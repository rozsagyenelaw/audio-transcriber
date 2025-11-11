#!/bin/bash
# Build script for Meeting Transcriber Mac app

echo "Building Meeting Transcriber.app..."

# Clean previous build
if [ -d "build" ]; then
    echo "Cleaning previous build..."
    rm -rf build
fi

if [ -d "dist" ]; then
    echo "Cleaning previous dist..."
    rm -rf dist
fi

# Build the app
echo "Running py2app..."
python3 setup.py py2app

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Build successful!"
    echo ""
    echo "Your app is located at: dist/Meeting Transcriber.app"
    echo ""
    echo "To install:"
    echo "  1. Open Finder and navigate to the 'dist' folder"
    echo "  2. Drag 'Meeting Transcriber.app' to your Applications folder"
    echo "  3. Double-click to launch!"
    echo ""
    echo "Note: On first launch, you may need to right-click and select 'Open'"
    echo "      to bypass macOS Gatekeeper security."
else
    echo ""
    echo "✗ Build failed. Please check the error messages above."
    exit 1
fi
