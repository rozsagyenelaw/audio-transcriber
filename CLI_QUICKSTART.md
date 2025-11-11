# CLI Meeting Transcriber - Quick Start

## Why Use CLI Version?

The CLI (Command Line Interface) version is **simpler and more stable** than the GUI version:
- ✅ No Qt threading issues
- ✅ No window crashes
- ✅ Lighter weight
- ✅ Works in terminal/SSH
- ✅ Same transcription quality

## Setup (First Time Only)

1. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   brew install portaudio
   ```

2. **Configure API keys:**

   Either run the GUI once to set up:
   ```bash
   python3 src/main_window.py
   ```

   OR manually edit `~/.meeting-transcriber/config.json`:
   ```json
   {
     "openai_api_key": "sk-your-key-here",
     "buffer_duration": 5,
     "sample_rate": 16000,
     "default_save_location": "/Users/yourname/Documents/Meeting Transcripts"
   }
   ```

## Usage

### Run CLI Version:
```bash
./run_cli.sh
```

Or directly:
```bash
python3 src/cli_transcriber.py
```

### Workflow:

1. **Select Microphone** - Choose from the list of audio devices
2. **Start Recording** - Automatic, just start speaking
3. **See Transcript** - Appears in real-time in the terminal
4. **Stop** - Press `Ctrl+C` when done
5. **Save** - Choose to save transcript to file

### Example Session:

```
============================================================
     MEETING TRANSCRIBER - CLI Version
============================================================

✓ OpenAI API key configured
✓ Audio system initialized (sample rate: 16000 Hz)

Available Audio Devices:
----------------------------------------
  [0] MacBook Pro Microphone
      Channels: 1, Rate: 48000 Hz
  [1] External USB Mic
      Channels: 2, Rate: 44100 Hz

Select device [default: 0]: 0

✓ Selected device: 0

✓ Transcription engine ready
  Buffer: 5 seconds

============================================================
SESSION: Meeting_20251111_173000
STARTED: 2025-11-11 17:30:00
============================================================

Transcript will appear below:
------------------------------------------------------------

🎤 RECORDING... (Press Ctrl+C to stop)

[17:30:05] Welcome everyone to today's meeting.
[17:30:12] Let's start by reviewing the action items from last week.
[17:30:20] John, can you give us an update on the project status?
...
```

## Features

- ✅ Real-time transcription
- ✅ Automatic audio chunking
- ✅ Save transcripts to TXT files
- ✅ Session timestamps
- ✅ Device selection
- ✅ No GUI crashes!

## Troubleshooting

### "No audio input devices found"
```bash
brew install portaudio
pip3 install --upgrade pyaudio
```

### "OpenAI API key not configured"
Run GUI setup first or edit config file manually.

### Audio not recording
- Check microphone permissions in System Preferences > Security & Privacy > Microphone
- Make sure correct device is selected

## Cost

Same as GUI version:
- OpenAI Whisper API: ~$0.006 per minute of audio
- Example: 1 hour meeting = $0.36

## Benefits vs GUI

| Feature | GUI | CLI |
|---------|-----|-----|
| Stability | ⚠️ Qt crashes | ✅ Rock solid |
| Resource usage | Higher | Lower |
| Setup complexity | More | Less |
| Real-time display | Yes | Yes |
| Claude AI analysis | Yes | Not yet (coming) |
| Google Drive | Yes | Not yet (coming) |

## Next Steps

Want AI analysis? You can:
1. Save transcript from CLI
2. Upload to ChatGPT or Claude.ai manually
3. Or use the GUI version (after we fix the threading issue)

---

**Recommendation: Use CLI version for reliable, crash-free transcription!**
