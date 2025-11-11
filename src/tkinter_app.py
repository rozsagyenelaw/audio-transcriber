#!/usr/bin/env python3
"""
Meeting Transcriber - Stable Tkinter GUI
No Qt threading issues, just works!
"""

import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
from pathlib import Path
import threading
import queue
import webbrowser
import urllib.parse

from config import Config
from audio_capture import AudioCapture
from transcription import TranscriptionEngine, TranscriptionSegment
from claude_integration import ClaudeAnalyzer


class TranscriberGUI:
    """Simple, stable GUI for meeting transcriber"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Meeting Transcriber")
        self.root.geometry("1000x700")

        # Load config
        self.config = Config()

        # Check if setup needed
        if self.config.needs_setup():
            messagebox.showwarning(
                "Setup Required",
                "Please configure your OpenAI API key.\n\nEdit: ~/.meeting-transcriber/config.json\n\nOr use the CLI setup."
            )

        # Initialize components
        self.audio_capture = None
        self.transcription_engine = None
        self.claude_analyzer = None

        self.is_recording = False
        self.session_start_time = None
        self.current_meeting_title = None

        # Queue for thread-safe GUI updates
        self.transcript_queue = queue.Queue()

        # Initialize backend
        self.init_components()

        # Build GUI
        self.create_widgets()

        # Start queue processor
        self.process_queue()

    def init_components(self):
        """Initialize backend components"""
        try:
            sample_rate = self.config.get('sample_rate', 16000)
            self.audio_capture = AudioCapture(sample_rate=sample_rate)
        except Exception as e:
            messagebox.showerror("Audio Error", f"Failed to initialize audio:\n{e}")
            sys.exit(1)

        # Transcription engine
        openai_key = self.config.get('openai_api_key')
        if openai_key:
            try:
                self.transcription_engine = TranscriptionEngine(
                    api_key=openai_key,
                    model='whisper-1',
                    buffer_duration=self.config.get('buffer_duration', 5),
                    sample_rate=sample_rate
                )
            except Exception as e:
                print(f"Error initializing transcription: {e}")

        # Claude analyzer
        anthropic_key = self.config.get('anthropic_api_key')
        if anthropic_key:
            try:
                self.claude_analyzer = ClaudeAnalyzer(
                    api_key=anthropic_key,
                    model=self.config.get('claude_model', 'claude-sonnet-4-20250514')
                )
            except Exception as e:
                print(f"Error initializing Claude: {e}")

    def create_widgets(self):
        """Create GUI widgets"""
        # Top control panel
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)

        # Record button
        self.record_btn = tk.Button(
            control_frame,
            text="▶ Start Recording",
            command=self.toggle_recording,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 14, "bold"),
            height=2,
            width=18,
            relief=tk.RAISED,
            borderwidth=3,
            activebackground="#45a049",
            activeforeground="white",
            cursor="hand2"
        )
        self.record_btn.pack(side=tk.LEFT, padx=5)

        # Device selector
        ttk.Label(control_frame, text="Microphone:").pack(side=tk.LEFT, padx=5)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(control_frame, textvariable=self.device_var, width=30)
        self.populate_devices()
        self.device_combo.pack(side=tk.LEFT, padx=5)

        # Duration label
        self.duration_label = ttk.Label(control_frame, text="00:00:00", font=("Arial", 14, "bold"))
        self.duration_label.pack(side=tk.RIGHT, padx=10)

        # Main content area
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left side: Transcript
        transcript_frame = ttk.LabelFrame(main_frame, text="Live Transcript", padding="10")
        transcript_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.transcript_text = scrolledtext.ScrolledText(
            transcript_frame,
            wrap=tk.WORD,
            font=("Courier", 11),
            height=25
        )
        self.transcript_text.pack(fill=tk.BOTH, expand=True)

        # Right side: Analysis
        analysis_frame = ttk.LabelFrame(main_frame, text="AI Analysis", padding="10")
        analysis_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.analysis_text = scrolledtext.ScrolledText(
            analysis_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            height=20
        )
        self.analysis_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Analysis buttons
        button_frame = ttk.Frame(analysis_frame)
        button_frame.pack(fill=tk.X)

        self.analyze_btn = ttk.Button(
            button_frame,
            text="Analyze Now",
            command=self.analyze_transcript,
            state=tk.DISABLED
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=5)

        self.summary_btn = ttk.Button(
            button_frame,
            text="Generate Summary",
            command=self.generate_summary,
            state=tk.DISABLED
        )
        self.summary_btn.pack(side=tk.LEFT, padx=5)

        # New row for Claude button
        claude_frame = ttk.Frame(analysis_frame)
        claude_frame.pack(fill=tk.X, pady=(5, 0))

        self.claude_btn = tk.Button(
            claude_frame,
            text="🤖 Open in Claude.ai",
            command=self.open_in_claude,
            bg="#6B46C1",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.RAISED,
            borderwidth=2,
            activebackground="#5835A1",
            activeforeground="white",
            cursor="hand2",
            state=tk.DISABLED
        )
        self.claude_btn.pack(side=tk.LEFT, padx=5)

        self.copy_btn = ttk.Button(
            claude_frame,
            text="📋 Copy Transcript",
            command=self.copy_transcript
        )
        self.copy_btn.pack(side=tk.LEFT, padx=5)

        # Bottom status bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=5, pady=5)

        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Transcript", command=self.save_transcript, accelerator="Cmd+S")
        file_menu.add_command(label="Export Analysis", command=self.export_analysis)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.quit_app, accelerator="Cmd+Q")

        # Keyboard shortcuts
        self.root.bind("<Command-s>", lambda e: self.save_transcript())
        self.root.bind("<Command-q>", lambda e: self.quit_app())

    def populate_devices(self):
        """Populate device combo box"""
        if self.audio_capture:
            devices = self.audio_capture.list_devices()
            device_names = [f"[{d['index']}] {d['name']}" for d in devices]
            self.device_combo['values'] = device_names
            if device_names:
                self.device_combo.current(0)

    def toggle_recording(self):
        """Toggle recording on/off"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording"""
        if not self.transcription_engine:
            messagebox.showwarning("Not Configured", "Please configure your OpenAI API key first.")
            return

        # Get device index from selection
        selection = self.device_var.get()
        if not selection:
            messagebox.showwarning("No Device", "Please select a microphone.")
            return

        device_index = int(selection.split('[')[1].split(']')[0])

        # Clear previous session
        self.transcript_text.delete(1.0, tk.END)
        self.analysis_text.delete(1.0, tk.END)

        # Start session
        self.is_recording = True
        self.session_start_time = datetime.now()
        self.current_meeting_title = f"Meeting_{self.session_start_time.strftime('%Y%m%d_%H%M%S')}"

        # Update UI
        self.record_btn.config(
            text="⏹ Stop Recording",
            bg="#f44336",
            activebackground="#da190b"
        )
        self.device_combo.config(state=tk.DISABLED)
        self.status_label.config(text="🎤 Recording...")

        if self.claude_analyzer:
            self.analyze_btn.config(state=tk.NORMAL)
            self.summary_btn.config(state=tk.NORMAL)

        # Enable Claude.ai button (always available)
        self.claude_btn.config(state=tk.NORMAL)

        # Start recording in background thread
        threading.Thread(target=self._recording_thread, args=(device_index,), daemon=True).start()

        # Start duration timer
        self.update_duration()

    def _recording_thread(self, device_index):
        """Background recording thread"""
        try:
            # Clear old callbacks to prevent duplicates
            self.transcription_engine.callbacks = []
            self.audio_capture.callbacks = []

            # Start transcription engine
            self.transcription_engine.start(on_segment=self._on_segment)

            # Start audio capture
            self.audio_capture.start_recording(
                device_index=device_index,
                on_audio_chunk=lambda chunk: self.transcription_engine.add_audio_chunk(chunk)
            )
        except Exception as e:
            self.transcript_queue.put(('error', str(e)))

    def _on_segment(self, segment: TranscriptionSegment):
        """Callback for new transcription segment"""
        if self.is_recording:  # Only process if still recording
            self.transcript_queue.put(('segment', segment))

    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        self.status_label.config(text="Stopping...")

        # Stop recording in background
        threading.Thread(target=self._stop_thread, daemon=True).start()

    def _stop_thread(self):
        """Background stop thread"""
        try:
            if self.audio_capture:
                self.audio_capture.stop_recording()
            if self.transcription_engine:
                self.transcription_engine.stop()

            self.transcript_queue.put(('stopped', None))
        except Exception as e:
            self.transcript_queue.put(('error', f"Stop error: {e}"))

    def process_queue(self):
        """Process messages from background threads"""
        try:
            while True:
                msg_type, data = self.transcript_queue.get_nowait()

                if msg_type == 'segment':
                    # Add segment to transcript
                    self.transcript_text.insert(tk.END, str(data) + "\n")
                    self.transcript_text.see(tk.END)

                elif msg_type == 'error':
                    messagebox.showerror("Error", data)
                    if self.is_recording:
                        self.stop_recording()

                elif msg_type == 'stopped':
                    # Update UI
                    self.record_btn.config(
                        text="▶ Start Recording",
                        bg="#4CAF50",
                        activebackground="#45a049"
                    )
                    self.device_combo.config(state=tk.NORMAL)
                    self.status_label.config(text="✓ Recording stopped")

                elif msg_type == 'analysis':
                    # Update analysis panel
                    self.analysis_text.delete(1.0, tk.END)
                    self.analysis_text.insert(1.0, data)
                    self.status_label.config(text="Analysis complete")

        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.process_queue)

    def update_duration(self):
        """Update recording duration"""
        if self.is_recording and self.session_start_time:
            duration = datetime.now() - self.session_start_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            seconds = int(duration.total_seconds() % 60)
            self.duration_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_duration)

    def analyze_transcript(self):
        """Analyze transcript with Claude"""
        if not self.claude_analyzer:
            messagebox.showwarning("Not Configured", "Please configure your Anthropic API key.")
            return

        if not self.transcription_engine or not self.transcription_engine.segments:
            messagebox.showinfo("No Content", "No transcript to analyze yet.")
            return

        self.status_label.config(text="Analyzing...")
        threading.Thread(target=self._analyze_thread, daemon=True).start()

    def _analyze_thread(self):
        """Background analysis thread"""
        try:
            full_transcript = self.transcription_engine.get_full_transcript(False)
            analysis = self.claude_analyzer.analyze_transcript(
                full_transcript,
                context=f"Meeting: {self.current_meeting_title}"
            )

            if analysis:
                self.transcript_queue.put(('analysis', analysis))
            else:
                self.transcript_queue.put(('error', "Analysis failed"))
        except Exception as e:
            self.transcript_queue.put(('error', f"Analysis error: {e}"))

    def generate_summary(self):
        """Generate meeting summary"""
        if not self.claude_analyzer:
            messagebox.showwarning("Not Configured", "Please configure your Anthropic API key.")
            return

        if not self.transcription_engine or not self.transcription_engine.segments:
            messagebox.showinfo("No Content", "No transcript to summarize yet.")
            return

        self.status_label.config(text="Generating summary...")
        threading.Thread(target=self._summary_thread, daemon=True).start()

    def _summary_thread(self):
        """Background summary thread"""
        try:
            full_transcript = self.transcription_engine.get_full_transcript(False)
            summary = self.claude_analyzer.get_meeting_summary(
                full_transcript,
                meeting_title=self.current_meeting_title
            )

            if summary:
                self.transcript_queue.put(('analysis', summary))
            else:
                self.transcript_queue.put(('error', "Summary failed"))
        except Exception as e:
            self.transcript_queue.put(('error', f"Summary error: {e}"))

    def save_transcript(self):
        """Save transcript to file"""
        if not self.transcription_engine or not self.transcription_engine.segments:
            messagebox.showinfo("No Content", "No transcript to save.")
            return

        save_dir = self.config.get_save_directory()
        default_name = f"{self.current_meeting_title}_transcript.txt"

        filepath = filedialog.asksaveasfilename(
            initialdir=save_dir,
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filepath:
            try:
                format_type = 'json' if filepath.endswith('.json') else 'txt'
                self.transcription_engine.export_transcript(Path(filepath), format=format_type)
                self.status_label.config(text=f"Saved: {Path(filepath).name}")
                messagebox.showinfo("Saved", f"Transcript saved to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save:\n{e}")

    def export_analysis(self):
        """Export analysis to file"""
        analysis_text = self.analysis_text.get(1.0, tk.END).strip()

        if not analysis_text:
            messagebox.showinfo("No Content", "No analysis to export.")
            return

        save_dir = self.config.get_save_directory()
        default_name = f"{self.current_meeting_title}_analysis.txt"

        filepath = filedialog.asksaveasfilename(
            initialdir=save_dir,
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filepath:
            try:
                Path(filepath).write_text(analysis_text, encoding='utf-8')
                self.status_label.config(text=f"Exported: {Path(filepath).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export:\n{e}")

    def copy_transcript(self):
        """Copy transcript to clipboard"""
        if not self.transcription_engine or not self.transcription_engine.segments:
            messagebox.showinfo("No Content", "No transcript to copy yet.")
            return

        try:
            full_transcript = self.transcription_engine.get_full_transcript(include_timestamps=True)

            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(full_transcript)
            self.root.update()

            self.status_label.config(text="Transcript copied to clipboard!")
            messagebox.showinfo("Copied!", "Transcript copied to clipboard.\n\nYou can now paste it into Claude.ai or anywhere else!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy:\n{e}")

    def open_in_claude(self):
        """Open Claude.ai with transcript pre-filled"""
        if not self.transcription_engine or not self.transcription_engine.segments:
            messagebox.showinfo("No Content", "No transcript to send yet. Start recording first!")
            return

        try:
            full_transcript = self.transcription_engine.get_full_transcript(include_timestamps=True)

            # Create a helpful prompt
            prompt = f"""I'm in a meeting right now. Here's the transcript so far:

---
{full_transcript}
---

Can you help me analyze this meeting? I need:
1. Key points and action items
2. Important decisions made
3. Any concerns or risks mentioned
4. What I should follow up on

Please be concise since I'm still in the meeting!"""

            # URL encode the prompt
            encoded_prompt = urllib.parse.quote(prompt)

            # Open Claude.ai with the prompt
            # Note: Claude.ai doesn't support direct URL params, so we'll just open it and copy to clipboard
            webbrowser.open("https://claude.ai/new")

            # Also copy to clipboard so user can paste
            self.root.clipboard_clear()
            self.root.clipboard_append(prompt)
            self.root.update()

            self.status_label.config(text="Opened Claude.ai - Prompt copied to clipboard!")

            messagebox.showinfo(
                "Claude.ai Opened!",
                "✅ Claude.ai is opening in your browser\n"
                "✅ The transcript + prompt is copied to your clipboard\n\n"
                "Just paste (Cmd+V) into Claude.ai and hit Enter!\n\n"
                "Claude will help you analyze the meeting in real-time!"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Claude.ai:\n{e}")

    def quit_app(self):
        """Quit application"""
        if self.is_recording:
            if not messagebox.askyesno("Recording Active", "Recording is still active. Stop and quit?"):
                return
            self.stop_recording()

        self.root.quit()

    def run(self):
        """Run the application"""
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        # Start main loop
        self.root.mainloop()


def main():
    """Main entry point"""
    app = TranscriberGUI()
    app.run()


if __name__ == '__main__':
    main()
