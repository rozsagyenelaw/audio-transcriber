# Meeting Transcriber

Real-time meeting transcription and legal analysis application for macOS.

## Features

- **Real-Time Transcription**: Live audio transcription using OpenAI Whisper API
- **AI-Powered Analysis**: Automatic legal analysis and meeting summaries using Claude AI
- **Professional GUI**: Clean, intuitive interface built with PyQt6
- **Google Drive Integration**: Automatic backup of transcripts and analyses
- **Multiple Export Formats**: Save transcripts as TXT, JSON, or SRT subtitle files
- **Standalone Mac App**: Double-click to launch, no terminal required

## Requirements

- macOS 10.13 or later
- Python 3.9 or later
- OpenAI API key (required for transcription)
- Anthropic API key (optional, for AI analysis)
- Google Cloud credentials (optional, for Drive backup)

## Installation

### Option 1: Run from Source (Development)

1. **Clone or download this repository**

2. **Install Python dependencies**:
   ```bash
   cd ~/meeting-transcriber
   pip3 install -r requirements.txt
   ```

3. **Install PortAudio** (required for PyAudio):
   ```bash
   brew install portaudio
   ```

4. **Run the application**:
   ```bash
   ./run.sh
   ```
   Or directly:
   ```bash
   python3 src/main_window.py
   ```

### Option 2: Build Mac .app Bundle (Production)

1. **Complete steps 1-3 from Option 1**

2. **Build the app**:
   ```bash
   ./build_app.sh
   ```

3. **Install the app**:
   - Open Finder and navigate to the `dist` folder
   - Drag `Meeting Transcriber.app` to your Applications folder
   - Double-click to launch!

   **Note**: On first launch, right-click the app and select "Open" to bypass macOS Gatekeeper security.

## First-Time Setup

When you launch the app for the first time, a setup wizard will guide you through configuration:

### 1. OpenAI API Key (Required)

- Get your API key from: https://platform.openai.com/api-keys
- The Whisper API costs approximately $0.006 per minute of audio
- Copy and paste your key (starts with `sk-`)

### 2. Anthropic API Key (Optional)

- Get your API key from: https://console.anthropic.com/settings/keys
- Required for AI-powered meeting analysis and summaries
- Recommended models:
  - `claude-sonnet-4-20250514` (best quality, recommended)
  - `claude-3-5-sonnet-20241022` (faster, lower cost)

### 3. Google Drive Integration (Optional)

To enable automatic backup to Google Drive:

1. Create a project at [Google Cloud Console](https://console.cloud.google.com)
2. Enable the Google Drive API
3. Create OAuth 2.0 credentials (Desktop app type)
4. Download the credentials JSON file
5. In the setup wizard, browse to select your credentials file
6. (Optional) Specify a folder ID to upload to a specific Drive folder

To get a folder ID:
- Open the folder in Google Drive in your browser
- Copy the ID from the URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`

### 4. General Preferences

- **Save Location**: Where transcripts are saved locally
- **Transcription Buffer**: How many seconds of audio to buffer before transcribing (default: 5)
- **Auto-save**: Automatically save transcripts when recording stops
- **Keep Audio Files**: Save the original audio recording files

## Usage

### Basic Workflow

1. **Select Microphone**: Choose your input device from the dropdown
2. **Start Recording**: Click the green "Start Recording" button
3. **Speak Naturally**: The transcript appears in real-time on the left side
4. **AI Analysis**: If Claude is configured, analysis updates automatically on the right
5. **Stop Recording**: Click the red "Stop Recording" button when finished

### Manual Analysis

- **Analyze Now**: Get immediate AI analysis of the current transcript
- **Generate Summary**: Create a comprehensive meeting summary with action items

### Saving and Exporting

- **Save Transcript** (⌘S): Save the transcript in your chosen format
  - TXT: Plain text with timestamps
  - JSON: Structured data with metadata
  - SRT: Subtitle format for video

- **Export Analysis**: Save the AI analysis separately

- **Google Drive Upload**: If configured, files are uploaded automatically when recording stops

### Keyboard Shortcuts

- `⌘S` - Save transcript
- `⌘Q` - Quit application

## Configuration

### Changing Settings

Access settings at any time via **Settings → Preferences**

You can modify:
- API keys for OpenAI and Anthropic
- AI model selections
- Google Drive settings
- Save location and preferences

### Audio Devices

View available microphones via **Settings → Audio Devices**

## Project Structure

```
meeting-transcriber/
├── src/
│   ├── main_window.py          # Main application window
│   ├── config.py                # Configuration management
│   ├── audio_capture.py         # Audio recording
│   ├── transcription.py         # OpenAI Whisper integration
│   ├── claude_integration.py    # Claude AI analysis
│   ├── gdrive_uploader.py       # Google Drive upload
│   └── setup_wizard.py          # First-time setup wizard
├── transcripts/                 # Default save location
├── logs/                        # Application logs
├── icons/                       # App icons
├── requirements.txt             # Python dependencies
├── setup.py                     # py2app configuration
├── build_app.sh                 # Build script
├── run.sh                       # Development run script
└── README.md                    # This file
```

## Cost Estimates

### OpenAI Whisper API
- **Cost**: $0.006 per minute of audio
- **Example**: 1 hour meeting = $0.36

### Anthropic Claude API
- **Input**: ~$3 per million tokens
- **Output**: ~$15 per million tokens
- **Example**: Analyzing a 1-hour meeting transcript ≈ $0.10-0.30

### Google Drive API
- **Free**: 15 GB storage included with Google account

## Troubleshooting

### "Microphone not found" or no audio devices

**Solution**: Install PortAudio:
```bash
brew install portaudio
pip3 install --upgrade pyaudio
```

### "OpenAI API error: Invalid API key"

**Solution**:
- Verify your API key at https://platform.openai.com/api-keys
- Ensure it starts with `sk-`
- Check that your OpenAI account has credits

### "Google Drive authentication failed"

**Solution**:
- Ensure you've enabled the Google Drive API in your Cloud Console project
- Verify your credentials file is valid
- Try clearing credentials: Delete `~/.meeting-transcriber/gdrive_token.pickle` and re-authenticate

### Build fails with py2app

**Solution**:
```bash
pip3 install --upgrade py2app setuptools
rm -rf build dist
./build_app.sh
```

### App won't open on first launch

**Solution**:
- Right-click the app and select "Open" instead of double-clicking
- Or go to System Preferences → Security & Privacy → General → Click "Open Anyway"

### Poor transcription quality

**Tips**:
- Use a good quality microphone
- Minimize background noise
- Speak clearly and at a normal pace
- Increase the buffer duration in Settings for longer processing time

## Privacy & Security

- **API Keys**: Stored locally in `~/.meeting-transcriber/config.json`
- **Audio Data**: Sent to OpenAI for transcription, then discarded (unless you enable "Keep Audio Files")
- **Transcripts**: Stored locally by default
- **Google Drive**: Only uploaded if you enable auto-upload
- **No Tracking**: This app does not collect any analytics or usage data

## File Locations

- **Configuration**: `~/.meeting-transcriber/config.json`
- **Google Drive Token**: `~/.meeting-transcriber/gdrive_token.pickle`
- **Transcripts**: As configured in Settings (default: `~/Documents/Meeting Transcripts`)
- **Logs**: `~/meeting-transcriber/logs/`

## Development

### Running Tests

```bash
cd ~/meeting-transcriber
python3 src/main_window.py
```

### Building for Distribution

```bash
./build_app.sh
```

The app bundle will be created in `dist/Meeting Transcriber.app`

### Adding Features

The modular architecture makes it easy to extend:

- **Audio Processing**: Modify `src/audio_capture.py`
- **Transcription**: Customize `src/transcription.py`
- **AI Analysis**: Enhance `src/claude_integration.py`
- **UI**: Update `src/main_window.py` and `src/setup_wizard.py`

## API Documentation

### OpenAI Whisper API
- Docs: https://platform.openai.com/docs/guides/speech-to-text
- Pricing: https://openai.com/pricing

### Anthropic Claude API
- Docs: https://docs.anthropic.com/claude/reference/getting-started-with-the-api
- Pricing: https://www.anthropic.com/pricing

### Google Drive API
- Docs: https://developers.google.com/drive/api/guides/about-sdk
- Quota: https://developers.google.com/drive/api/guides/limits

## Version History

### v1.0.0 (2025)
- Initial release
- Real-time transcription with OpenAI Whisper
- Claude AI analysis integration
- Google Drive auto-upload
- Mac .app bundle
- First-launch setup wizard

## License

Copyright © 2025 Rozsa Gyene. All rights reserved.

This software is provided for personal use. Redistribution requires permission.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review API documentation links
3. Verify your API keys and credentials are valid

## Acknowledgments

Built with:
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [OpenAI Whisper API](https://openai.com/research/whisper) - Speech recognition
- [Anthropic Claude](https://www.anthropic.com/claude) - AI analysis
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) - Audio capture
- [Google Drive API](https://developers.google.com/drive) - Cloud storage

---

**Note**: This is a desktop application for macOS. It requires API keys from third-party services (OpenAI and optionally Anthropic and Google) which may incur costs based on usage.
