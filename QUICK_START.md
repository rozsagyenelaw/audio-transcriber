# Quick Start Guide - CLI Version

## ✅ Your Audio Devices:

```
[0] iPhone (3) Microphone
[1] Rozsa's iphone Microphone
[2] MacBook Pro Microphone (default)
```

---

## 🚀 How to Run

### Option 1: Interactive (Choose device manually)
```bash
./run_cli.sh
```
You'll be prompted to select a device.

### Option 2: Auto Mode (Use default device)
```bash
./run_cli.sh --auto
```
Automatically uses device [2] - MacBook Pro Microphone

### Option 3: Specific Device
```bash
./run_cli.sh -d 0    # Use iPhone (3) Microphone
./run_cli.sh -d 1    # Use Rozsa's iphone Microphone
./run_cli.sh -d 2    # Use MacBook Pro Microphone
```

### Option 4: List Devices Only
```bash
./run_cli.sh --list
```

---

## 📝 Full Workflow Example

```bash
cd /Users/rozsagyene/meeting-transcriber

# Start recording with auto-select
./run_cli.sh --auto

# OR start with specific device
./run_cli.sh -d 2

# Speak naturally...
# Transcript appears in real-time

# When done, press: Ctrl+C

# Save? y/n
# Type: y

# Done! Transcript saved to Documents/Meeting Transcripts/
```

---

## 💡 Tips

1. **Best device?** Usually device [2] (MacBook Pro Microphone) works best
2. **Press Ctrl+C** to stop recording anytime
3. **Transcripts auto-saved** to `~/Documents/Meeting Transcripts/`
4. **Cost:** ~$0.006/minute (60 minutes = $0.36)

---

## ⚡ Recommended Command

For the smoothest experience:

```bash
./run_cli.sh --auto
```

This automatically selects your MacBook Pro microphone and starts recording!

---

## 🐛 Troubleshooting

### "No audio input devices"
```bash
brew install portaudio
pip3 install --upgrade pyaudio
```

### "OpenAI API key not configured"
Run GUI once to set up:
```bash
python3 src/main_window.py
```
Or edit `~/.meeting-transcriber/config.json`

### Permission denied on ./run_cli.sh
```bash
chmod +x run_cli.sh
```

---

## ✨ Why CLI is Better

- ✅ No crashes (unlike GUI)
- ✅ Lightweight
- ✅ Same transcription quality
- ✅ Simple to use
- ✅ Works every time!

**Enjoy your stable, crash-free transcription!** 🎉
