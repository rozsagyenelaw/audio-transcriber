"""
Audio Capture Module
Handles real-time audio recording from microphone
"""

import pyaudio
import wave
import threading
import queue
import time
from pathlib import Path
from typing import Callable, Optional, List, Dict
import numpy as np


class AudioCapture:
    """Captures audio from microphone in real-time"""

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        """
        Initialize audio capture

        Args:
            sample_rate: Audio sample rate (Hz)
            chunk_size: Size of audio chunks to process
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.frames = []
        self.recording_thread = None
        self.callbacks = []

    def list_devices(self) -> List[Dict]:
        """Get list of available audio input devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': int(info['defaultSampleRate'])
                })
        return devices

    def get_default_device(self) -> Optional[int]:
        """Get default input device index"""
        try:
            return self.audio.get_default_input_device_info()['index']
        except:
            devices = self.list_devices()
            return devices[0]['index'] if devices else None

    def start_recording(self, device_index: Optional[int] = None,
                       on_audio_chunk: Optional[Callable] = None):
        """
        Start recording audio

        Args:
            device_index: Microphone device index (None for default)
            on_audio_chunk: Callback when new audio chunk is available
        """
        if self.is_recording:
            return

        if device_index is None:
            device_index = self.get_default_device()

        self.is_recording = True
        self.frames = []

        # Open audio stream (no callback, use blocking mode)
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size
        )

        if on_audio_chunk:
            self.callbacks.append(on_audio_chunk)

        # Start recording thread
        self.recording_thread = threading.Thread(target=self._record_loop)
        self.recording_thread.daemon = True
        self.recording_thread.start()

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)

    def _record_loop(self):
        """Main recording loop"""
        while self.is_recording:
            try:
                if self.stream and self.stream.is_active():
                    # Read audio data directly from stream
                    audio_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    self.frames.append(audio_data)

                    # Call callbacks with audio chunk
                    for callback in self.callbacks:
                        try:
                            callback(audio_data)
                        except Exception as e:
                            print(f"Error in audio callback: {e}")
                else:
                    time.sleep(0.01)
            except Exception as e:
                print(f"Error in recording loop: {e}")
                break

    def stop_recording(self) -> bytes:
        """Stop recording and return audio data"""
        self.is_recording = False

        # Wait for recording thread to finish
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=3)

        # Close stream safely
        if self.stream:
            try:
                # Give a moment for any pending operations
                time.sleep(0.1)

                if self.stream.is_active():
                    self.stream.stop_stream()
                    time.sleep(0.05)

                self.stream.close()
            except Exception as e:
                print(f"Error stopping stream: {e}")
            finally:
                self.stream = None

        # Clear callbacks
        self.callbacks = []

        # Return all frames as bytes
        audio_data = b''.join(self.frames) if self.frames else b''
        return audio_data

    def save_audio(self, filepath: Path, audio_data: Optional[bytes] = None):
        """
        Save recorded audio to WAV file

        Args:
            filepath: Path to save audio file
            audio_data: Audio data to save (or use current frames)
        """
        if audio_data is None:
            audio_data = b''.join(self.frames)

        with wave.open(str(filepath), 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)

    def get_audio_level(self) -> float:
        """Get current audio input level (0.0 to 1.0)"""
        if not self.frames:
            return 0.0

        try:
            # Get last chunk
            last_chunk = self.frames[-1]
            audio_array = np.frombuffer(last_chunk, dtype=np.int16)

            # Calculate RMS level
            rms = np.sqrt(np.mean(audio_array**2))

            # Normalize to 0-1 range
            normalized = min(rms / 32768.0, 1.0)
            return normalized
        except:
            return 0.0

    def cleanup(self):
        """Clean up resources"""
        if self.is_recording:
            self.stop_recording()

        if self.audio:
            self.audio.terminate()
