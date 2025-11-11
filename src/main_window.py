"""
Main Window for Meeting Transcriber Application
PyQt6 GUI for real-time transcription and analysis
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QStatusBar, QMenuBar, QMenu,
    QFileDialog, QMessageBox, QProgressBar, QSplitter, QGroupBox,
    QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QFont, QColor, QPalette

from config import Config
from audio_capture import AudioCapture
from transcription import TranscriptionEngine, TranscriptionSegment
from claude_integration import ClaudeAnalyzer, RealTimeAnalyzer
from gdrive_uploader import GDriveUploader


class TranscriptionWorker(QThread):
    """Worker thread for handling audio and transcription"""

    segment_ready = pyqtSignal(object)  # TranscriptionSegment
    error_occurred = pyqtSignal(str)

    def __init__(self, audio_capture: AudioCapture,
                 transcription_engine: TranscriptionEngine,
                 device_index: Optional[int] = None):
        super().__init__()
        self.audio_capture = audio_capture
        self.transcription_engine = transcription_engine
        self.device_index = device_index
        self.running = False

    def run(self):
        """Run the transcription worker"""
        try:
            self.running = True

            # Start audio capture with callback
            self.audio_capture.start_recording(
                device_index=self.device_index,
                on_audio_chunk=self._on_audio_chunk
            )

            # Start transcription engine
            self.transcription_engine.start(
                on_segment=self._on_segment
            )
        except Exception as e:
            self.error_occurred.emit(f"Error starting recording: {e}")

    def stop(self):
        """Stop the worker"""
        self.running = False
        self.transcription_engine.stop()
        self.audio_capture.stop_recording()

    def _on_audio_chunk(self, audio_data: bytes):
        """Handle audio chunk from capture"""
        if self.running:
            self.transcription_engine.add_audio_chunk(audio_data)

    def _on_segment(self, segment: TranscriptionSegment):
        """Handle new transcription segment"""
        if self.running:
            self.segment_ready.emit(segment)


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, config: Config):
        super().__init__()

        self.config = config
        self.audio_capture = None
        self.transcription_engine = None
        self.claude_analyzer = None
        self.realtime_analyzer = None
        self.gdrive_uploader = None
        self.worker = None

        self.is_recording = False
        self.current_meeting_title = None
        self.session_start_time = None

        self.init_components()
        self.init_ui()
        self.setup_timers()

        # Restore window geometry
        geometry = self.config.get('window_geometry')
        if geometry:
            self.restoreGeometry(geometry)

    def init_components(self):
        """Initialize backend components"""
        # Audio capture
        try:
            sample_rate = self.config.get('sample_rate', 16000)
            self.audio_capture = AudioCapture(sample_rate=sample_rate)
        except Exception as e:
            QMessageBox.critical(
                None,
                'Audio System Error',
                f'Failed to initialize audio system:\n{e}\n\nPlease check that your audio drivers are installed correctly.'
            )
            raise

        # Transcription engine
        openai_key = self.config.get('openai_api_key')
        if openai_key:
            try:
                self.transcription_engine = TranscriptionEngine(
                    api_key=openai_key,
                    model=self.config.get('whisper_model', 'whisper-1'),
                    buffer_duration=self.config.get('buffer_duration', 5),
                    sample_rate=sample_rate
                )
            except Exception as e:
                print(f"Error initializing transcription engine: {e}")

        # Claude analyzer
        anthropic_key = self.config.get('anthropic_api_key')
        if anthropic_key:
            try:
                self.claude_analyzer = ClaudeAnalyzer(
                    api_key=anthropic_key,
                    model=self.config.get('claude_model', 'claude-sonnet-4-20250514')
                )
                self.realtime_analyzer = RealTimeAnalyzer(self.claude_analyzer)
            except Exception as e:
                print(f"Error initializing Claude analyzer: {e}")

        # Google Drive uploader
        gdrive_creds = self.config.get('google_drive_credentials_path')
        gdrive_folder = self.config.get('google_drive_folder_id')
        if gdrive_creds:
            try:
                self.gdrive_uploader = GDriveUploader(
                    credentials_path=gdrive_creds,
                    folder_id=gdrive_folder
                )
            except Exception as e:
                print(f"Error initializing Google Drive uploader: {e}")

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle('Meeting Transcriber')
        self.setMinimumSize(1000, 700)

        # Create menu bar
        self.create_menu_bar()

        # Create main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Control panel at top
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

        # Create splitter for transcript and analysis
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Transcript
        transcript_group = QGroupBox("Live Transcript")
        transcript_layout = QVBoxLayout()

        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setFont(QFont("Courier", 11))
        transcript_layout.addWidget(self.transcript_text)

        transcript_group.setLayout(transcript_layout)
        splitter.addWidget(transcript_group)

        # Right side: Tabs for Analysis and Settings
        right_tabs = QTabWidget()

        # Analysis tab
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout()

        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setFont(QFont("Arial", 10))
        analysis_layout.addWidget(self.analysis_text)

        # Analysis controls
        analysis_controls = QHBoxLayout()

        self.analyze_btn = QPushButton('Analyze Now')
        self.analyze_btn.clicked.connect(self.analyze_transcript)
        self.analyze_btn.setEnabled(False)
        analysis_controls.addWidget(self.analyze_btn)

        self.summary_btn = QPushButton('Generate Summary')
        self.summary_btn.clicked.connect(self.generate_summary)
        self.summary_btn.setEnabled(False)
        analysis_controls.addWidget(self.summary_btn)

        analysis_controls.addStretch()
        analysis_layout.addLayout(analysis_controls)

        analysis_widget.setLayout(analysis_layout)
        right_tabs.addTab(analysis_widget, "Analysis")

        # Info tab
        info_widget = self.create_info_panel()
        right_tabs.addTab(info_widget, "Session Info")

        splitter.addWidget(right_tabs)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel('Ready')
        self.status_bar.addWidget(self.status_label)

        # Audio level indicator
        self.audio_level_bar = QProgressBar()
        self.audio_level_bar.setMaximum(100)
        self.audio_level_bar.setTextVisible(False)
        self.audio_level_bar.setMaximumWidth(100)
        self.status_bar.addPermanentWidget(QLabel('Audio Level:'))
        self.status_bar.addPermanentWidget(self.audio_level_bar)

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        new_action = QAction('New Session', self)
        new_action.triggered.connect(self.new_session)
        file_menu.addAction(new_action)

        save_action = QAction('Save Transcript...', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_transcript)
        file_menu.addAction(save_action)

        export_action = QAction('Export Analysis...', self)
        export_action.triggered.connect(self.export_analysis)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction('Quit', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Settings menu
        settings_menu = menubar.addMenu('Settings')

        config_action = QAction('Preferences...', self)
        config_action.triggered.connect(self.open_settings)
        settings_menu.addAction(config_action)

        devices_action = QAction('Audio Devices...', self)
        devices_action.triggered.connect(self.show_audio_devices)
        settings_menu.addAction(devices_action)

        # Help menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_control_panel(self) -> QWidget:
        """Create top control panel"""
        panel = QWidget()
        layout = QHBoxLayout(panel)

        # Record button
        self.record_btn = QPushButton('Start Recording')
        self.record_btn.setMinimumHeight(40)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.record_btn.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_btn)

        # Device selector
        layout.addWidget(QLabel('Microphone:'))
        self.device_combo = QComboBox()
        self.populate_devices()
        layout.addWidget(self.device_combo)

        layout.addStretch()

        # Duration label
        self.duration_label = QLabel('00:00:00')
        self.duration_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(self.duration_label)

        return panel

    def create_info_panel(self) -> QWidget:
        """Create session info panel"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFont(QFont("Arial", 10))

        layout.addWidget(self.info_text)
        widget.setLayout(layout)

        return widget

    def populate_devices(self):
        """Populate audio device combo box"""
        self.device_combo.clear()

        if self.audio_capture:
            devices = self.audio_capture.list_devices()

            for device in devices:
                self.device_combo.addItem(
                    f"{device['name']} ({device['channels']} ch)",
                    device['index']
                )

            # Select saved device if available
            saved_device = self.config.get('mic_device_index')
            if saved_device is not None:
                for i in range(self.device_combo.count()):
                    if self.device_combo.itemData(i) == saved_device:
                        self.device_combo.setCurrentIndex(i)
                        break

    def setup_timers(self):
        """Setup UI update timers"""
        # Duration timer
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self.update_duration)

        # Audio level timer
        self.audio_timer = QTimer()
        self.audio_timer.timeout.connect(self.update_audio_level)
        self.audio_timer.start(100)  # Update every 100ms

    def toggle_recording(self):
        """Toggle recording on/off"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording and transcription"""
        if not self.transcription_engine:
            QMessageBox.warning(
                self,
                'Configuration Required',
                'Please configure your OpenAI API key in Settings.'
            )
            return

        # Get selected device
        device_index = self.device_combo.currentData()

        # Clear previous session
        self.transcript_text.clear()
        self.analysis_text.clear()

        # Start session
        self.is_recording = True
        self.session_start_time = datetime.now()
        self.current_meeting_title = f"Meeting_{self.session_start_time.strftime('%Y%m%d_%H%M%S')}"

        # Create and start worker
        self.worker = TranscriptionWorker(
            self.audio_capture,
            self.transcription_engine,
            device_index=device_index
        )
        self.worker.segment_ready.connect(self.on_transcription_segment, Qt.ConnectionType.QueuedConnection)
        self.worker.error_occurred.connect(self.on_worker_error, Qt.ConnectionType.QueuedConnection)
        self.worker.start()

        # Start real-time analyzer if available
        if self.realtime_analyzer:
            self.realtime_analyzer.start(on_analysis=self.on_realtime_analysis)

        # Update UI
        self.record_btn.setText('Stop Recording')
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

        self.device_combo.setEnabled(False)
        self.analyze_btn.setEnabled(True)
        self.summary_btn.setEnabled(True)

        self.status_label.setText('Recording...')
        self.duration_timer.start(1000)

        self.update_session_info()

    def stop_recording(self):
        """Stop recording and transcription"""
        self.is_recording = False
        self.status_label.setText('Stopping recording...')
        QApplication.processEvents()

        # Stop analyzer first
        if self.realtime_analyzer:
            try:
                self.realtime_analyzer.stop()
            except Exception as e:
                print(f"Error stopping analyzer: {e}")

        # Stop worker and wait for it to finish
        if self.worker:
            try:
                self.worker.stop()
                # Wait for worker thread to finish with timeout
                if not self.worker.wait(5000):  # Wait up to 5 seconds
                    print("Warning: Worker thread did not finish in time")
                    # Force quit the thread if it doesn't respond
                    self.worker.terminate()
                    self.worker.wait(1000)
            except Exception as e:
                print(f"Error stopping worker: {e}")
            finally:
                self.worker = None

        # Update UI
        self.record_btn.setText('Start Recording')
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.device_combo.setEnabled(True)
        self.status_label.setText('Recording stopped')
        self.duration_timer.stop()

        # Auto-save if configured
        if self.config.get('auto_save', False):
            self.save_transcript()

        # Auto-upload if configured
        if self.config.get('auto_upload_drive', False):
            self.upload_to_drive()

    def on_transcription_segment(self, segment: TranscriptionSegment):
        """Handle new transcription segment"""
        try:
            # Append to transcript display
            self.transcript_text.append(str(segment))

            # Update real-time analyzer
            if self.realtime_analyzer and self.transcription_engine:
                full_transcript = self.transcription_engine.get_full_transcript(False)
                if full_transcript:
                    self.realtime_analyzer.update_transcript(full_transcript)

            self.update_session_info()
        except Exception as e:
            print(f"Error handling transcription segment: {e}")

    def on_realtime_analysis(self, analysis: str):
        """Handle real-time analysis update"""
        self.analysis_text.setPlainText(analysis)

    def on_worker_error(self, error_message: str):
        """Handle worker thread errors"""
        print(f"Worker error: {error_message}")
        self.status_label.setText(f'Error: {error_message}')
        QMessageBox.critical(
            self,
            'Recording Error',
            f'An error occurred during recording:\n{error_message}\n\nPlease try again.'
        )
        # Stop recording if error occurs
        if self.is_recording:
            self.stop_recording()

    def analyze_transcript(self):
        """Analyze current transcript"""
        if not self.claude_analyzer:
            QMessageBox.warning(
                self,
                'Configuration Required',
                'Please configure your Anthropic API key in Settings.'
            )
            return

        if not self.transcription_engine:
            QMessageBox.warning(self, 'No Engine', 'Transcription engine not initialized.')
            return

        full_transcript = self.transcription_engine.get_full_transcript(False)

        if not full_transcript:
            QMessageBox.information(self, 'No Content', 'No transcript to analyze yet.')
            return

        self.status_label.setText('Analyzing...')
        QApplication.processEvents()

        try:
            analysis = self.claude_analyzer.analyze_transcript(
                full_transcript,
                context=f"Meeting: {self.current_meeting_title}"
            )

            if analysis:
                self.analysis_text.setPlainText(analysis)
                self.status_label.setText('Analysis complete')
            else:
                self.status_label.setText('Analysis failed')
        except Exception as e:
            self.status_label.setText('Analysis error')
            QMessageBox.critical(self, 'Analysis Error', f'Failed to analyze transcript:\n{e}')

    def generate_summary(self):
        """Generate comprehensive meeting summary"""
        if not self.claude_analyzer:
            QMessageBox.warning(
                self,
                'Configuration Required',
                'Please configure your Anthropic API key in Settings.'
            )
            return

        if not self.transcription_engine:
            QMessageBox.warning(self, 'No Engine', 'Transcription engine not initialized.')
            return

        full_transcript = self.transcription_engine.get_full_transcript(False)

        if not full_transcript:
            QMessageBox.information(self, 'No Content', 'No transcript to summarize yet.')
            return

        self.status_label.setText('Generating summary...')
        QApplication.processEvents()

        try:
            summary = self.claude_analyzer.get_meeting_summary(
                full_transcript,
                meeting_title=self.current_meeting_title
            )

            if summary:
                self.analysis_text.setPlainText(summary)
                self.status_label.setText('Summary complete')
            else:
                self.status_label.setText('Summary failed')
        except Exception as e:
            self.status_label.setText('Summary error')
            QMessageBox.critical(self, 'Summary Error', f'Failed to generate summary:\n{e}')

    def update_duration(self):
        """Update recording duration display"""
        if self.session_start_time:
            duration = datetime.now() - self.session_start_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            seconds = int(duration.total_seconds() % 60)

            self.duration_label.setText(f'{hours:02d}:{minutes:02d}:{seconds:02d}')

    def update_audio_level(self):
        """Update audio level indicator"""
        if self.audio_capture and self.is_recording:
            level = self.audio_capture.get_audio_level()
            self.audio_level_bar.setValue(int(level * 100))

    def update_session_info(self):
        """Update session information display"""
        if not self.transcription_engine:
            return

        info = []
        info.append(f"Session: {self.current_meeting_title}")
        info.append(f"Started: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S') if self.session_start_time else 'N/A'}")
        info.append(f"\nSegments: {len(self.transcription_engine.segments)}")

        duration = self.transcription_engine.get_duration()
        info.append(f"Duration: {int(duration // 60)}m {int(duration % 60)}s")

        self.info_text.setPlainText('\n'.join(info))

    def save_transcript(self):
        """Save transcript to file"""
        if not self.transcription_engine or len(self.transcription_engine.segments) == 0:
            QMessageBox.information(self, 'No Content', 'No transcript to save.')
            return

        save_dir = self.config.get_save_directory()
        default_filename = f"{self.current_meeting_title}_transcript.txt"

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            'Save Transcript',
            str(save_dir / default_filename),
            'Text Files (*.txt);;JSON Files (*.json);;SRT Files (*.srt)'
        )

        if filepath:
            filepath = Path(filepath)
            format_map = {'.txt': 'txt', '.json': 'json', '.srt': 'srt'}
            format = format_map.get(filepath.suffix, 'txt')

            self.transcription_engine.export_transcript(filepath, format=format)
            self.status_label.setText(f'Transcript saved: {filepath.name}')

            QMessageBox.information(self, 'Saved', f'Transcript saved to:\n{filepath}')

    def export_analysis(self):
        """Export analysis to file"""
        analysis_text = self.analysis_text.toPlainText()

        if not analysis_text:
            QMessageBox.information(self, 'No Content', 'No analysis to export.')
            return

        save_dir = self.config.get_save_directory()
        default_filename = f"{self.current_meeting_title}_analysis.txt"

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            'Export Analysis',
            str(save_dir / default_filename),
            'Text Files (*.txt)'
        )

        if filepath:
            Path(filepath).write_text(analysis_text, encoding='utf-8')
            self.status_label.setText(f'Analysis exported: {Path(filepath).name}')

    def upload_to_drive(self):
        """Upload transcript and analysis to Google Drive"""
        if not self.gdrive_uploader:
            QMessageBox.warning(
                self,
                'Not Configured',
                'Google Drive upload is not configured.'
            )
            return

        # Save transcript temporarily
        save_dir = self.config.get_save_directory()
        transcript_path = save_dir / f"{self.current_meeting_title}_transcript.txt"
        self.transcription_engine.export_transcript(transcript_path, format='txt')

        # Save analysis if available
        analysis_path = None
        if self.analysis_text.toPlainText():
            analysis_path = save_dir / f"{self.current_meeting_title}_analysis.txt"
            Path(analysis_path).write_text(self.analysis_text.toPlainText(), encoding='utf-8')

        # Upload
        self.status_label.setText('Uploading to Google Drive...')
        QApplication.processEvents()

        result = self.gdrive_uploader.upload_transcript(
            str(transcript_path),
            str(analysis_path) if analysis_path else None,
            meeting_title=self.current_meeting_title
        )

        if result['transcript_id']:
            self.status_label.setText('Uploaded to Google Drive')
            QMessageBox.information(self, 'Success', 'Files uploaded to Google Drive!')
        else:
            self.status_label.setText('Upload failed')
            QMessageBox.warning(self, 'Error', 'Failed to upload to Google Drive.')

    def new_session(self):
        """Start new session"""
        if self.is_recording:
            reply = QMessageBox.question(
                self,
                'Recording in Progress',
                'Stop current recording and start new session?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.stop_recording()
            else:
                return

        self.transcript_text.clear()
        self.analysis_text.clear()
        self.info_text.clear()

        if self.transcription_engine:
            self.transcription_engine.clear_segments()

        if self.claude_analyzer:
            self.claude_analyzer.clear_history()

        self.status_label.setText('Ready for new session')

    def open_settings(self):
        """Open settings dialog"""
        from setup_wizard import SettingsDialog

        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # Reload components with new settings
            self.init_components()
            self.status_label.setText('Settings updated')

    def show_audio_devices(self):
        """Show audio device information"""
        if not self.audio_capture:
            return

        devices = self.audio_capture.list_devices()

        info = "Available Audio Input Devices:\n\n"
        for device in devices:
            info += f"[{device['index']}] {device['name']}\n"
            info += f"    Channels: {device['channels']}\n"
            info += f"    Sample Rate: {device['sample_rate']} Hz\n\n"

        QMessageBox.information(self, 'Audio Devices', info)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            'About Meeting Transcriber',
            '''Meeting Transcriber v1.0

Real-time meeting transcription and legal analysis application.

Features:
• Real-time audio transcription using OpenAI Whisper
• Automatic legal analysis using Claude AI
• Google Drive integration
• Export to multiple formats

Built with PyQt6, OpenAI, and Anthropic APIs.'''
        )

    def closeEvent(self, event):
        """Handle window close event"""
        if self.is_recording:
            reply = QMessageBox.question(
                self,
                'Recording in Progress',
                'Recording is still in progress. Do you want to stop and exit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            self.stop_recording()

        # Save window geometry
        self.config.set('window_geometry', self.saveGeometry())
        self.config.save()

        # Cleanup
        if self.audio_capture:
            self.audio_capture.cleanup()

        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName('Meeting Transcriber')

    # Load configuration
    config = Config()

    # Check if setup is needed
    if config.needs_setup():
        from setup_wizard import SetupWizard

        wizard = SetupWizard(config)
        if wizard.exec():
            config.complete_setup()
        else:
            sys.exit(0)

    # Create and show main window
    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
