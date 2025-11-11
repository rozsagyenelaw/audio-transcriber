#!/usr/bin/env python3
"""
CLI Meeting Transcriber - Simple command-line version
No GUI, no threading issues, just works!
"""

import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

from config import Config
from audio_capture import AudioCapture
from transcription import TranscriptionEngine, TranscriptionSegment

def print_header():
    """Print application header"""
    print("\n" + "="*60)
    print("     MEETING TRANSCRIBER - CLI Version")
    print("="*60 + "\n")

def list_audio_devices(audio_capture):
    """List available audio devices"""
    print("Available Audio Devices:")
    print("-" * 40)
    devices = audio_capture.list_devices()
    for device in devices:
        print(f"  [{device['index']}] {device['name']}")
        print(f"      Channels: {device['channels']}, Rate: {device['sample_rate']} Hz")
    print()
    return devices

def select_device(audio_capture, auto_default=False):
    """Let user select audio device"""
    devices = list_audio_devices(audio_capture)

    if not devices:
        print("ERROR: No audio input devices found!")
        return None

    default = audio_capture.get_default_device()

    # Auto-select default if requested
    if auto_default:
        print(f"Auto-selecting default device: [{default}]")
        return default

    while True:
        try:
            choice = input(f"Select device [default: {default}]: ").strip()
            if not choice:
                return default

            device_index = int(choice)
            if any(d['index'] == device_index for d in devices):
                return device_index
            else:
                print(f"Invalid device index. Please choose from the list.")
        except ValueError:
            print("Please enter a valid number.")
        except (KeyboardInterrupt, EOFError):
            print("\n\nUsing default device...")
            return default

def on_transcription_segment(segment: TranscriptionSegment):
    """Callback for new transcription segments"""
    timestamp = segment.timestamp.strftime('%H:%M:%S')
    print(f"[{timestamp}] {segment.text}")
    sys.stdout.flush()

def main():
    """Main CLI application"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Meeting Transcriber - CLI Version')
    parser.add_argument('-d', '--device', type=int, help='Audio device index to use')
    parser.add_argument('-a', '--auto', action='store_true', help='Auto-select default device')
    parser.add_argument('-l', '--list', action='store_true', help='List audio devices and exit')
    args = parser.parse_args()

    print_header()

    # Load configuration
    config = Config()

    # Check for OpenAI API key
    openai_key = config.get('openai_api_key')
    if not openai_key:
        print("ERROR: OpenAI API key not configured!")
        print("\nPlease run the GUI version first to set up your API keys:")
        print("  python3 src/main_window.py")
        print("\nOr manually edit: ~/.meeting-transcriber/config.json")
        return 1

    print(f"✓ OpenAI API key configured")

    # Initialize audio capture
    try:
        sample_rate = config.get('sample_rate', 16000)
        audio_capture = AudioCapture(sample_rate=sample_rate)
        print(f"✓ Audio system initialized (sample rate: {sample_rate} Hz)\n")
    except Exception as e:
        print(f"ERROR: Failed to initialize audio system: {e}")
        return 1

    # Handle --list option
    if args.list:
        list_audio_devices(audio_capture)
        return 0

    # Select audio device
    if args.device is not None:
        device_index = args.device
        print(f"Using specified device: [{device_index}]\n")
    else:
        device_index = select_device(audio_capture, auto_default=args.auto)
        if device_index is None:
            return 1
        print(f"\n✓ Selected device: {device_index}\n")

    # Initialize transcription engine
    try:
        transcription_engine = TranscriptionEngine(
            api_key=openai_key,
            model=config.get('whisper_model', 'whisper-1'),
            buffer_duration=config.get('buffer_duration', 5),
            sample_rate=sample_rate
        )
        print(f"✓ Transcription engine ready")
        print(f"  Buffer: {config.get('buffer_duration', 5)} seconds\n")
    except Exception as e:
        print(f"ERROR: Failed to initialize transcription: {e}")
        return 1

    # Start session
    session_start = datetime.now()
    meeting_title = f"Meeting_{session_start.strftime('%Y%m%d_%H%M%S')}"

    print("="*60)
    print(f"SESSION: {meeting_title}")
    print(f"STARTED: {session_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("\nTranscript will appear below:")
    print("-"*60 + "\n")

    # Start transcription with simple callback
    transcription_engine.start(on_segment=on_transcription_segment)

    # Start audio recording
    try:
        audio_capture.start_recording(
            device_index=device_index,
            on_audio_chunk=lambda chunk: transcription_engine.add_audio_chunk(chunk)
        )
    except Exception as e:
        print(f"\nERROR: Failed to start recording: {e}")
        return 1

    print("🎤 RECORDING... (Press Ctrl+C to stop)\n")

    # Keep running until user stops
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n" + "-"*60)
        print("Stopping recording...")

    # Stop recording
    try:
        audio_capture.stop_recording()
        transcription_engine.stop()
    except Exception as e:
        print(f"Warning: Error stopping: {e}")

    # Save transcript
    session_end = datetime.now()
    duration = (session_end - session_start).total_seconds()

    print("\n" + "="*60)
    print(f"SESSION ENDED: {session_end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"DURATION: {int(duration // 60)}m {int(duration % 60)}s")
    print(f"SEGMENTS: {len(transcription_engine.segments)}")
    print("="*60 + "\n")

    # Save options
    if transcription_engine.segments:
        save_dir = config.get_save_directory()

        while True:
            save = input("Save transcript? (y/n): ").strip().lower()
            if save == 'y':
                # Generate filename
                filepath = save_dir / f"{meeting_title}_transcript.txt"

                try:
                    transcription_engine.export_transcript(filepath, format='txt')
                    print(f"\n✓ Transcript saved to: {filepath}")
                except Exception as e:
                    print(f"\n✗ Error saving: {e}")
                break
            elif save == 'n':
                print("\nTranscript not saved.")
                break
    else:
        print("No transcript to save (no segments recorded).")

    print("\nThank you for using Meeting Transcriber CLI!\n")
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
