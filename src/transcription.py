"""
Transcription Engine Module
Handles real-time audio transcription using OpenAI Whisper API
"""

import io
import wave
import time
import threading
import queue
from pathlib import Path
from typing import Callable, Optional, List, Dict
from datetime import datetime, timedelta
from openai import OpenAI
import tempfile


class TranscriptionSegment:
    """Represents a segment of transcribed text"""

    def __init__(self, text: str, timestamp: datetime, duration: float = 0.0):
        self.text = text
        self.timestamp = timestamp
        self.duration = duration
        self.speaker = None  # For future speaker detection

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'text': self.text,
            'timestamp': self.timestamp.isoformat(),
            'duration': self.duration,
            'speaker': self.speaker
        }

    def __repr__(self):
        time_str = self.timestamp.strftime('%H:%M:%S')
        return f"[{time_str}] {self.text}"


class TranscriptionEngine:
    """Real-time audio transcription engine using OpenAI Whisper"""

    def __init__(self, api_key: str, model: str = "whisper-1",
                 buffer_duration: int = 5, sample_rate: int = 16000):
        """
        Initialize transcription engine

        Args:
            api_key: OpenAI API key
            model: Whisper model to use
            buffer_duration: Seconds of audio to buffer before transcribing
            sample_rate: Audio sample rate
        """
        self.api_key = api_key
        self.model = model
        self.buffer_duration = buffer_duration
        self.sample_rate = sample_rate

        self.client = OpenAI(api_key=api_key)

        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        self.is_transcribing = False
        self.transcription_thread = None

        self.segments: List[TranscriptionSegment] = []
        self.callbacks = []

        self.start_time = None
        self.last_transcription_time = None

    def start(self, on_segment: Optional[Callable] = None):
        """
        Start transcription processing

        Args:
            on_segment: Callback function called with each new TranscriptionSegment
        """
        if self.is_transcribing:
            return

        self.is_transcribing = True
        self.start_time = datetime.now()
        self.last_transcription_time = time.time()
        self.segments = []

        if on_segment:
            self.callbacks.append(on_segment)

        # Start transcription processing thread
        self.transcription_thread = threading.Thread(target=self._transcription_loop)
        self.transcription_thread.daemon = True
        self.transcription_thread.start()

    def stop(self):
        """Stop transcription processing"""
        self.is_transcribing = False

        if self.transcription_thread:
            self.transcription_thread.join(timeout=5)

        # Process any remaining audio in buffer
        if len(self.audio_buffer) > 0:
            self._process_buffer()

    def add_audio_chunk(self, audio_data: bytes):
        """
        Add audio chunk to buffer for transcription

        Args:
            audio_data: Raw audio data bytes
        """
        with self.buffer_lock:
            self.audio_buffer.append(audio_data)

    def _transcription_loop(self):
        """Main transcription processing loop"""
        while self.is_transcribing:
            try:
                current_time = time.time()

                # Check if enough time has passed to transcribe
                if current_time - self.last_transcription_time >= self.buffer_duration:
                    if len(self.audio_buffer) > 0:
                        self._process_buffer()
                        self.last_transcription_time = current_time

                time.sleep(0.5)  # Check every 0.5 seconds

            except Exception as e:
                print(f"Error in transcription loop: {e}")
                time.sleep(1)

    def _process_buffer(self):
        """Process accumulated audio buffer and transcribe"""
        try:
            # Get audio from buffer
            with self.buffer_lock:
                if not self.audio_buffer:
                    return

                audio_data = b''.join(self.audio_buffer)
                self.audio_buffer = []

            # Skip if audio is too short (less than 0.5 seconds)
            min_size = int(self.sample_rate * 0.5 * 2)  # 0.5 sec * 2 bytes per sample
            if len(audio_data) < min_size:
                return

            # Create temporary WAV file for Whisper API
            audio_file = self._create_wav_file(audio_data)

            if audio_file is None:
                return

            # Transcribe using Whisper API
            text = self._transcribe_audio(audio_file)

            if text and text.strip():
                # Create transcription segment
                timestamp = datetime.now()
                duration = len(audio_data) / (self.sample_rate * 2)  # 2 bytes per sample

                segment = TranscriptionSegment(
                    text=text.strip(),
                    timestamp=timestamp,
                    duration=duration
                )

                self.segments.append(segment)

                # Call callbacks
                for callback in self.callbacks:
                    try:
                        callback(segment)
                    except Exception as e:
                        print(f"Error in transcription callback: {e}")

        except Exception as e:
            print(f"Error processing audio buffer: {e}")

    def _create_wav_file(self, audio_data: bytes) -> Optional[io.BytesIO]:
        """
        Create WAV file from raw audio data

        Args:
            audio_data: Raw audio bytes

        Returns:
            BytesIO object containing WAV file, or None on error
        """
        try:
            wav_buffer = io.BytesIO()

            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)

            wav_buffer.seek(0)
            wav_buffer.name = "audio.wav"  # Whisper API needs a filename

            return wav_buffer

        except Exception as e:
            print(f"Error creating WAV file: {e}")
            return None

    def _transcribe_audio(self, audio_file: io.BytesIO, retry_count: int = 3) -> Optional[str]:
        """
        Transcribe audio using OpenAI Whisper API

        Args:
            audio_file: Audio file as BytesIO
            retry_count: Number of retries on failure

        Returns:
            Transcribed text or None
        """
        for attempt in range(retry_count):
            try:
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    response_format="text",
                    language="en"  # Can be made configurable
                )

                return response

            except Exception as e:
                print(f"Transcription attempt {attempt + 1} failed: {e}")

                if attempt < retry_count - 1:
                    time.sleep(1)  # Wait before retry
                else:
                    print(f"Failed to transcribe after {retry_count} attempts")
                    return None

        return None

    def get_full_transcript(self, include_timestamps: bool = True) -> str:
        """
        Get full transcript as formatted text

        Args:
            include_timestamps: Whether to include timestamps

        Returns:
            Formatted transcript string
        """
        if not self.segments:
            return ""

        lines = []
        for segment in self.segments:
            if include_timestamps:
                time_str = segment.timestamp.strftime('%H:%M:%S')
                lines.append(f"[{time_str}] {segment.text}")
            else:
                lines.append(segment.text)

        return "\n".join(lines)

    def get_segments(self) -> List[TranscriptionSegment]:
        """Get all transcription segments"""
        return self.segments.copy()

    def clear_segments(self):
        """Clear all transcription segments"""
        self.segments = []

    def get_duration(self) -> float:
        """Get total transcription duration in seconds"""
        if not self.start_time:
            return 0.0

        return (datetime.now() - self.start_time).total_seconds()

    def export_transcript(self, filepath: Path, format: str = "txt"):
        """
        Export transcript to file

        Args:
            filepath: Path to save transcript
            format: Export format (txt, json, srt)
        """
        if format == "txt":
            self._export_txt(filepath)
        elif format == "json":
            self._export_json(filepath)
        elif format == "srt":
            self._export_srt(filepath)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_txt(self, filepath: Path):
        """Export as plain text"""
        transcript = self.get_full_transcript(include_timestamps=True)
        filepath.write_text(transcript, encoding='utf-8')

    def _export_json(self, filepath: Path):
        """Export as JSON"""
        import json

        data = {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'duration': self.get_duration(),
            'segments': [seg.to_dict() for seg in self.segments]
        }

        filepath.write_text(json.dumps(data, indent=2), encoding='utf-8')

    def _export_srt(self, filepath: Path):
        """Export as SRT subtitle format"""
        lines = []

        for i, segment in enumerate(self.segments, 1):
            # Calculate start and end times
            start_time = segment.timestamp - self.start_time if self.start_time else timedelta(0)
            end_time = start_time + timedelta(seconds=segment.duration)

            # Format times as SRT timestamps
            start_str = self._format_srt_time(start_time)
            end_str = self._format_srt_time(end_time)

            lines.append(f"{i}")
            lines.append(f"{start_str} --> {end_str}")
            lines.append(segment.text)
            lines.append("")  # Empty line between entries

        filepath.write_text("\n".join(lines), encoding='utf-8')

    def _format_srt_time(self, td: timedelta) -> str:
        """Format timedelta as SRT timestamp (HH:MM:SS,mmm)"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        milliseconds = int(td.microseconds / 1000)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
