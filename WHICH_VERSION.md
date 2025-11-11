# Which Version Should You Use?

## 🎯 RECOMMENDATION: Use CLI Version

The **CLI (terminal) version is much more stable** and won't crash!

---

## Two Versions Available

### 1. 🟢 **CLI Version (RECOMMENDED)**

**Run with:**
```bash
./run_cli.sh
```

**Pros:**
- ✅ **No crashes!** - Rock solid stability
- ✅ Simple terminal interface
- ✅ Lower resource usage
- ✅ Same transcription quality
- ✅ Easy to use
- ✅ Works in SSH/remote sessions

**Cons:**
- ❌ No AI analysis (yet)
- ❌ No Google Drive upload (yet)
- ❌ Terminal only (no fancy UI)

**Best for:**
- Reliable transcription
- Quick meetings
- Users who want "it just works"
- When GUI keeps crashing

---

### 2. 🔴 **GUI Version (Has Issues)**

**Run with:**
```bash
python3 src/main_window.py
```

**Pros:**
- ✅ Nice graphical interface
- ✅ Real-time AI analysis (Claude)
- ✅ Google Drive integration
- ✅ Visual transcript display
- ✅ Multiple export formats

**Cons:**
- ❌ **Crashes frequently** (Qt threading issues)
- ❌ Segmentation faults
- ❌ Complex to debug
- ❌ Higher resource usage
- ❌ macOS compatibility issues

**Best for:**
- When you need AI analysis
- When you need Google Drive upload
- When stability isn't critical (testing/development)

---

## Quick Comparison

| Feature | CLI ✅ | GUI ⚠️ |
|---------|-------|-------|
| **Stability** | Excellent | Poor (crashes) |
| **Real-time transcription** | Yes | Yes |
| **Device selection** | Yes | Yes |
| **Save transcripts** | Yes | Yes |
| **AI analysis** | No | Yes |
| **Google Drive** | No | Yes |
| **Setup complexity** | Low | Medium |
| **Resource usage** | Low | High |

---

## Setup Instructions

### CLI Version Setup:

1. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   brew install portaudio
   ```

2. **Run the GUI once** to configure API keys:
   ```bash
   python3 src/main_window.py
   ```
   (Enter your OpenAI key in the setup wizard, then close it)

3. **Run CLI version:**
   ```bash
   ./run_cli.sh
   ```

### Full Documentation:
- CLI Version: See `CLI_QUICKSTART.md`
- GUI Version: See `README.md`

---

## Common Issues

### "GUI keeps crashing"
➜ **Use CLI version instead!** It's designed to avoid Qt threading issues.

### "I need AI analysis"
**Option 1:** Save transcript from CLI, paste into ChatGPT/Claude manually
**Option 2:** Try GUI version but expect crashes

### "No audio devices found"
```bash
brew install portaudio
pip3 install --upgrade pyaudio
```

---

## Cost (Same for Both)

- OpenAI Whisper API: **$0.006 per minute**
- Example: 1 hour meeting = $0.36
- Claude AI (GUI only): ~$0.10-0.30 per meeting analysis

---

## **TL;DR - What Should I Do?**

1. **Need reliable transcription?** ➜ Use CLI version (`./run_cli.sh`)
2. **Need AI analysis?** ➜ Try GUI, but it may crash
3. **GUI crashed again?** ➜ Switch to CLI version
4. **Want it to just work?** ➜ **Use CLI version!**

---

## Future Plans

We're working on:
- [ ] Adding AI analysis to CLI version
- [ ] Fixing GUI threading issues properly
- [ ] Web-based version (Flask/FastAPI)
- [ ] Electron app (more stable than Qt)

For now: **CLI version is your best bet for stability!**
