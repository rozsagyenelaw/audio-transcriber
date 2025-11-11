#!/bin/bash
# Script to create an Automator .app launcher for Meeting Transcriber

APP_NAME="Meeting Transcriber.app"
APP_PATH="$HOME/Desktop/$APP_NAME"

# Create the Automator app using osascript
osascript <<EOF
tell application "Automator"
    set newWorkflow to make new workflow

    tell newWorkflow
        -- Add "Run Shell Script" action
        set shellAction to make new action with properties {name:"Run Shell Script"}

        tell shellAction
            -- Set the shell to bash
            set value of setting "COMMAND_STRING" to "cd ~/meeting-transcriber && ./run.sh"
            set value of setting "shell" to "/bin/bash"
        end tell

        -- Save as application
        save in POSIX file "$APP_PATH" as "application"
    end tell

    quit
end tell
EOF

if [ -f "$APP_PATH/Contents/MacOS/Application Stub" ]; then
    echo "✓ Launcher created successfully!"
    echo ""
    echo "Location: $APP_PATH"
    echo ""
    echo "You can now:"
    echo "  1. Double-click 'Meeting Transcriber.app' on your Desktop"
    echo "  2. Drag it to your Applications folder"
    echo "  3. Drag it to your Dock for quick access"
    echo ""
    echo "The app will launch Meeting Transcriber automatically!"
else
    echo "✗ Failed to create launcher. Creating alternative..."
fi
