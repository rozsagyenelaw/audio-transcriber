#!/usr/bin/osascript
# AppleScript launcher for Meeting Transcriber

on run
    tell application "Terminal"
        activate
        do script "cd ~/meeting-transcriber && ./run.sh"
    end tell
end run
