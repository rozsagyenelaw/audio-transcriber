# Quick Start Guide

Get up and running with Meeting Transcriber in 5 minutes!

## Prerequisites

- macOS 10.13 or later
- OpenAI API key (get one at https://platform.openai.com/api-keys)

## Installation

### 1. Install Dependencies

```bash
cd ~/meeting-transcriber
pip3 install -r requirements.txt
brew install portaudio
```

### 2. Launch the App

```bash
./run.sh
```

Or run directly:
```bash
python3 src/main_window.py
```

## First Launch Setup

The setup wizard will guide you through:

1. **OpenAI API Key** (Required)
   - Paste your API key (starts with `sk-`)
   - Used for transcription

2. **Claude API Key** (Optional)
   - Paste your Anthropic API key (starts with `sk-ant-`)
   - Used for AI analysis
   - Skip if you only want transcription

3. **Google Drive** (Optional)
   - Skip for now, you can set up later
   - Required only if you want automatic cloud backup

4. **Preferences**
   - Choose where to save transcripts
   - Default settings work great!

## Using the App

### Record Your First Meeting

1. Select your microphone from the dropdown
2. Click **"Start Recording"** (green button)
3. Start speaking
4. Watch the transcript appear in real-time
5. Click **"Stop Recording"** (red button) when done

### Save Your Transcript

- Click **File → Save Transcript** (or press ⌘S)
- Choose format: TXT, JSON, or SRT
- Done!

### Get AI Analysis (if Claude is configured)

- Click **"Analyze Now"** for quick insights
- Click **"Generate Summary"** for a detailed report with action items

## Tips

- Use a good quality microphone for best results
- Keep background noise low
- The app processes audio every 5 seconds by default
- All data is stored locally unless you enable Google Drive

## Cost

- Transcription: ~$0.006 per minute ($0.36 for 1 hour)
- Claude analysis: ~$0.10-0.30 per hour of transcript

## Next Steps

- **Build Mac App**: Run `./build_app.sh` to create a standalone .app
- **Configure Settings**: Access via Settings → Preferences
- **Set up Google Drive**: For automatic cloud backup

## Troubleshooting

### No microphone detected
```bash
brew install portaudio
pip3 install --upgrade pyaudio
```

### API errors
- Verify your API key is correct
- Check you have credits in your OpenAI account

## Need Help?

See the full [README.md](README.md) for detailed documentation.

---

That's it! You're ready to transcribe meetings. 🎙️
