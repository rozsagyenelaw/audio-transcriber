"""
Setup Wizard and Settings Dialog
First-time configuration and preferences management
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QCheckBox, QComboBox,
    QTextEdit, QMessageBox, QDialog, QDialogButtonBox, QGroupBox,
    QSpinBox, QFormLayout, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import Config


class WelcomePage(QWizardPage):
    """Welcome page for setup wizard"""

    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to Meeting Transcriber")

        layout = QVBoxLayout()

        welcome_text = QLabel(
            """<h2>Welcome!</h2>
            <p>This wizard will help you configure Meeting Transcriber.</p>
            <p>You will need:</p>
            <ul>
            <li><b>OpenAI API Key</b> - Required for transcription (Whisper API)</li>
            <li><b>Anthropic API Key</b> - Optional for AI analysis (Claude API)</li>
            <li><b>Google Drive Credentials</b> - Optional for cloud backup</li>
            </ul>
            <p>You can always change these settings later in Preferences.</p>
            """
        )
        welcome_text.setWordWrap(True)

        layout.addWidget(welcome_text)
        layout.addStretch()

        self.setLayout(layout)


class OpenAIPage(QWizardPage):
    """OpenAI API configuration page"""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

        self.setTitle("OpenAI API Configuration")
        self.setSubTitle("Required for audio transcription using Whisper")

        layout = QVBoxLayout()

        # API Key input
        key_label = QLabel("OpenAI API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        self.api_key_input.setText(config.get('openai_api_key', ''))

        # Show/hide button
        show_btn = QPushButton("Show")
        show_btn.setMaximumWidth(60)
        show_btn.clicked.connect(self.toggle_visibility)

        key_layout = QHBoxLayout()
        key_layout.addWidget(self.api_key_input)
        key_layout.addWidget(show_btn)

        layout.addWidget(key_label)
        layout.addLayout(key_layout)

        # Help text
        help_text = QLabel(
            """<p>Get your API key from: <a href="https://platform.openai.com/api-keys">
            https://platform.openai.com/api-keys</a></p>
            <p><b>Note:</b> Transcription costs approximately $0.006 per minute of audio.</p>
            """
        )
        help_text.setOpenExternalLinks(True)
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        # Model selection
        layout.addWidget(QLabel("\nWhisper Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["whisper-1"])
        layout.addWidget(self.model_combo)

        layout.addStretch()

        self.setLayout(layout)

        # Register field for validation
        self.registerField("openai_key*", self.api_key_input)

    def toggle_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.sender().setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.sender().setText("Show")

    def validatePage(self):
        """Validate before proceeding"""
        key = self.api_key_input.text().strip()

        if not key:
            QMessageBox.warning(self, "Required", "OpenAI API key is required.")
            return False

        if not key.startswith('sk-'):
            QMessageBox.warning(self, "Invalid", "OpenAI API keys should start with 'sk-'")
            return False

        self.config.set('openai_api_key', key)
        self.config.set('whisper_model', self.model_combo.currentText())
        return True


class ClaudePage(QWizardPage):
    """Claude API configuration page"""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

        self.setTitle("Claude AI Configuration (Optional)")
        self.setSubTitle("For intelligent meeting analysis and summaries")

        layout = QVBoxLayout()

        # Enable checkbox
        self.enable_check = QCheckBox("Enable Claude AI Analysis")
        self.enable_check.setChecked(bool(config.get('anthropic_api_key')))
        self.enable_check.stateChanged.connect(self.on_enable_changed)
        layout.addWidget(self.enable_check)

        # API Key input
        self.key_widget = QWidget()
        key_layout = QVBoxLayout()

        key_label = QLabel("Anthropic API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-ant-...")
        self.api_key_input.setText(config.get('anthropic_api_key', ''))

        # Show/hide button
        show_btn = QPushButton("Show")
        show_btn.setMaximumWidth(60)
        show_btn.clicked.connect(self.toggle_visibility)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.api_key_input)
        input_layout.addWidget(show_btn)

        key_layout.addWidget(key_label)
        key_layout.addLayout(input_layout)

        # Help text
        help_text = QLabel(
            """<p>Get your API key from: <a href="https://console.anthropic.com/settings/keys">
            https://console.anthropic.com/settings/keys</a></p>
            <p>Claude will provide real-time legal analysis, action items, and meeting summaries.</p>
            """
        )
        help_text.setOpenExternalLinks(True)
        help_text.setWordWrap(True)
        key_layout.addWidget(help_text)

        # Model selection
        key_layout.addWidget(QLabel("\nClaude Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229"
        ])
        current_model = config.get('claude_model', 'claude-sonnet-4-20250514')
        index = self.model_combo.findText(current_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        key_layout.addWidget(self.model_combo)

        self.key_widget.setLayout(key_layout)
        layout.addWidget(self.key_widget)

        layout.addStretch()

        self.setLayout(layout)

        self.on_enable_changed()

    def toggle_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.sender().setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.sender().setText("Show")

    def on_enable_changed(self):
        """Handle enable checkbox change"""
        self.key_widget.setEnabled(self.enable_check.isChecked())

    def validatePage(self):
        """Validate before proceeding"""
        if self.enable_check.isChecked():
            key = self.api_key_input.text().strip()

            if key and not key.startswith('sk-ant-'):
                QMessageBox.warning(self, "Invalid", "Anthropic API keys should start with 'sk-ant-'")
                return False

            self.config.set('anthropic_api_key', key)
            self.config.set('claude_model', self.model_combo.currentText())
        else:
            self.config.set('anthropic_api_key', '')

        return True


class GoogleDrivePage(QWizardPage):
    """Google Drive configuration page"""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

        self.setTitle("Google Drive Integration (Optional)")
        self.setSubTitle("Automatically backup transcripts to Google Drive")

        layout = QVBoxLayout()

        # Enable checkbox
        self.enable_check = QCheckBox("Enable Google Drive Auto-Upload")
        self.enable_check.setChecked(config.get('auto_upload_drive', False))
        self.enable_check.stateChanged.connect(self.on_enable_changed)
        layout.addWidget(self.enable_check)

        # Configuration widget
        self.config_widget = QWidget()
        config_layout = QVBoxLayout()

        # Credentials file
        creds_label = QLabel("OAuth Credentials File:")
        self.creds_input = QLineEdit()
        self.creds_input.setText(config.get('google_drive_credentials_path', ''))
        self.creds_input.setPlaceholderText("Path to credentials.json")

        creds_btn = QPushButton("Browse...")
        creds_btn.clicked.connect(self.browse_credentials)

        creds_layout = QHBoxLayout()
        creds_layout.addWidget(self.creds_input)
        creds_layout.addWidget(creds_btn)

        config_layout.addWidget(creds_label)
        config_layout.addLayout(creds_layout)

        # Folder ID
        config_layout.addWidget(QLabel("\nGoogle Drive Folder ID (optional):"))
        self.folder_input = QLineEdit()
        self.folder_input.setText(config.get('google_drive_folder_id', ''))
        self.folder_input.setPlaceholderText("Leave empty for root folder")
        config_layout.addWidget(self.folder_input)

        # Help text
        help_text = QLabel(
            """<p><b>Setup Instructions:</b></p>
            <ol>
            <li>Create a project at <a href="https://console.cloud.google.com">Google Cloud Console</a></li>
            <li>Enable the Google Drive API</li>
            <li>Create OAuth 2.0 credentials (Desktop app)</li>
            <li>Download the credentials JSON file</li>
            </ol>
            <p>The Folder ID can be found in the URL when viewing a folder in Google Drive.</p>
            """
        )
        help_text.setOpenExternalLinks(True)
        help_text.setWordWrap(True)
        config_layout.addWidget(help_text)

        self.config_widget.setLayout(config_layout)
        layout.addWidget(self.config_widget)

        layout.addStretch()

        self.setLayout(layout)

        self.on_enable_changed()

    def browse_credentials(self):
        """Browse for credentials file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Credentials File",
            str(Path.home()),
            "JSON Files (*.json)"
        )

        if filepath:
            self.creds_input.setText(filepath)

    def on_enable_changed(self):
        """Handle enable checkbox change"""
        self.config_widget.setEnabled(self.enable_check.isChecked())

    def validatePage(self):
        """Validate before proceeding"""
        if self.enable_check.isChecked():
            creds_path = self.creds_input.text().strip()

            if creds_path and not Path(creds_path).exists():
                QMessageBox.warning(self, "File Not Found", "Credentials file does not exist.")
                return False

            self.config.set('auto_upload_drive', True)
            self.config.set('google_drive_credentials_path', creds_path)
            self.config.set('google_drive_folder_id', self.folder_input.text().strip())
        else:
            self.config.set('auto_upload_drive', False)

        return True


class PreferencesPage(QWizardPage):
    """General preferences page"""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

        self.setTitle("General Preferences")
        self.setSubTitle("Configure general application settings")

        layout = QFormLayout()

        # Save location
        self.save_location = QLineEdit()
        self.save_location.setText(config.get('default_save_location'))

        save_btn = QPushButton("Browse...")
        save_btn.clicked.connect(self.browse_save_location)

        save_layout = QHBoxLayout()
        save_layout.addWidget(self.save_location)
        save_layout.addWidget(save_btn)

        layout.addRow("Save Location:", save_layout)

        # Buffer duration
        self.buffer_spin = QSpinBox()
        self.buffer_spin.setRange(3, 30)
        self.buffer_spin.setValue(config.get('buffer_duration', 5))
        self.buffer_spin.setSuffix(" seconds")
        layout.addRow("Transcription Buffer:", self.buffer_spin)

        # Auto-save
        self.auto_save_check = QCheckBox("Automatically save transcripts when recording stops")
        self.auto_save_check.setChecked(config.get('auto_save', False))
        layout.addRow("", self.auto_save_check)

        # Keep audio file
        self.keep_audio_check = QCheckBox("Keep audio recording files")
        self.keep_audio_check.setChecked(config.get('keep_audio_file', False))
        layout.addRow("", self.keep_audio_check)

        self.setLayout(layout)

    def browse_save_location(self):
        """Browse for save directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Save Location",
            self.save_location.text()
        )

        if directory:
            self.save_location.setText(directory)

    def validatePage(self):
        """Validate and save preferences"""
        save_dir = self.save_location.text().strip()

        if not save_dir:
            QMessageBox.warning(self, "Required", "Please select a save location.")
            return False

        Path(save_dir).mkdir(parents=True, exist_ok=True)

        self.config.set('default_save_location', save_dir)
        self.config.set('buffer_duration', self.buffer_spin.value())
        self.config.set('auto_save', self.auto_save_check.isChecked())
        self.config.set('keep_audio_file', self.keep_audio_check.isChecked())

        return True


class CompletePage(QWizardPage):
    """Completion page"""

    def __init__(self):
        super().__init__()
        self.setTitle("Setup Complete!")

        layout = QVBoxLayout()

        complete_text = QLabel(
            """<h2>You're all set!</h2>
            <p>Meeting Transcriber is now configured and ready to use.</p>
            <p><b>Quick Start:</b></p>
            <ol>
            <li>Select your microphone from the dropdown</li>
            <li>Click "Start Recording" to begin</li>
            <li>Speak naturally - transcription happens in real-time</li>
            <li>Click "Stop Recording" when finished</li>
            <li>Use "Analyze" or "Generate Summary" for AI insights</li>
            </ol>
            <p>You can change these settings anytime in Settings → Preferences.</p>
            """
        )
        complete_text.setWordWrap(True)

        layout.addWidget(complete_text)
        layout.addStretch()

        self.setLayout(layout)


class SetupWizard(QWizard):
    """Main setup wizard"""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

        self.setWindowTitle("Meeting Transcriber Setup")
        self.setMinimumSize(600, 500)

        # Add pages
        self.addPage(WelcomePage())
        self.addPage(OpenAIPage(config))
        self.addPage(ClaudePage(config))
        self.addPage(GoogleDrivePage(config))
        self.addPage(PreferencesPage(config))
        self.addPage(CompletePage())

    def accept(self):
        """Save configuration and close"""
        self.config.save()
        super().accept()


class SettingsDialog(QDialog):
    """Settings dialog for changing preferences after setup"""

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config

        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout()

        # Create tabs
        tabs = QTabWidget()

        # API Keys tab
        api_tab = self.create_api_tab()
        tabs.addTab(api_tab, "API Keys")

        # Google Drive tab
        drive_tab = self.create_drive_tab()
        tabs.addTab(drive_tab, "Google Drive")

        # Preferences tab
        prefs_tab = self.create_preferences_tab()
        tabs.addTab(prefs_tab, "Preferences")

        layout.addWidget(tabs)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        self.setLayout(layout)

    def create_api_tab(self) -> QWidget:
        """Create API keys tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # OpenAI section
        openai_group = QGroupBox("OpenAI API")
        openai_layout = QFormLayout()

        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key.setText(self.config.get('openai_api_key', ''))
        openai_layout.addRow("API Key:", self.openai_key)

        self.whisper_model = QComboBox()
        self.whisper_model.addItems(["whisper-1"])
        openai_layout.addRow("Model:", self.whisper_model)

        openai_group.setLayout(openai_layout)
        layout.addWidget(openai_group)

        # Anthropic section
        anthropic_group = QGroupBox("Anthropic API (Claude)")
        anthropic_layout = QFormLayout()

        self.anthropic_key = QLineEdit()
        self.anthropic_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.anthropic_key.setText(self.config.get('anthropic_api_key', ''))
        anthropic_layout.addRow("API Key:", self.anthropic_key)

        self.claude_model = QComboBox()
        self.claude_model.addItems([
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229"
        ])
        current_model = self.config.get('claude_model', 'claude-sonnet-4-20250514')
        index = self.claude_model.findText(current_model)
        if index >= 0:
            self.claude_model.setCurrentIndex(index)
        anthropic_layout.addRow("Model:", self.claude_model)

        anthropic_group.setLayout(anthropic_layout)
        layout.addWidget(anthropic_group)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_drive_tab(self) -> QWidget:
        """Create Google Drive tab"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Enable auto-upload
        self.auto_upload = QCheckBox("Enable Google Drive Auto-Upload")
        self.auto_upload.setChecked(self.config.get('auto_upload_drive', False))
        layout.addWidget(self.auto_upload)

        # Configuration
        form = QFormLayout()

        self.gdrive_creds = QLineEdit()
        self.gdrive_creds.setText(self.config.get('google_drive_credentials_path', ''))

        creds_btn = QPushButton("Browse...")
        creds_btn.clicked.connect(self.browse_gdrive_creds)

        creds_layout = QHBoxLayout()
        creds_layout.addWidget(self.gdrive_creds)
        creds_layout.addWidget(creds_btn)

        form.addRow("Credentials:", creds_layout)

        self.gdrive_folder = QLineEdit()
        self.gdrive_folder.setText(self.config.get('google_drive_folder_id', ''))
        form.addRow("Folder ID:", self.gdrive_folder)

        layout.addLayout(form)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_preferences_tab(self) -> QWidget:
        """Create preferences tab"""
        widget = QWidget()
        layout = QFormLayout()

        # Save location
        self.save_location = QLineEdit()
        self.save_location.setText(self.config.get('default_save_location'))

        save_btn = QPushButton("Browse...")
        save_btn.clicked.connect(self.browse_save_location)

        save_layout = QHBoxLayout()
        save_layout.addWidget(self.save_location)
        save_layout.addWidget(save_btn)

        layout.addRow("Save Location:", save_layout)

        # Buffer duration
        self.buffer_duration = QSpinBox()
        self.buffer_duration.setRange(3, 30)
        self.buffer_duration.setValue(self.config.get('buffer_duration', 5))
        self.buffer_duration.setSuffix(" seconds")
        layout.addRow("Transcription Buffer:", self.buffer_duration)

        # Auto-save
        self.auto_save = QCheckBox("Automatically save transcripts when recording stops")
        self.auto_save.setChecked(self.config.get('auto_save', False))
        layout.addRow("", self.auto_save)

        # Keep audio
        self.keep_audio = QCheckBox("Keep audio recording files")
        self.keep_audio.setChecked(self.config.get('keep_audio_file', False))
        layout.addRow("", self.keep_audio)

        widget.setLayout(layout)
        return widget

    def browse_gdrive_creds(self):
        """Browse for Google Drive credentials"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Credentials File",
            str(Path.home()),
            "JSON Files (*.json)"
        )

        if filepath:
            self.gdrive_creds.setText(filepath)

    def browse_save_location(self):
        """Browse for save directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Save Location",
            self.save_location.text()
        )

        if directory:
            self.save_location.setText(directory)

    def accept(self):
        """Save settings and close"""
        # Save API keys
        self.config.set('openai_api_key', self.openai_key.text().strip())
        self.config.set('whisper_model', self.whisper_model.currentText())
        self.config.set('anthropic_api_key', self.anthropic_key.text().strip())
        self.config.set('claude_model', self.claude_model.currentText())

        # Save Google Drive settings
        self.config.set('auto_upload_drive', self.auto_upload.isChecked())
        self.config.set('google_drive_credentials_path', self.gdrive_creds.text().strip())
        self.config.set('google_drive_folder_id', self.gdrive_folder.text().strip())

        # Save preferences
        self.config.set('default_save_location', self.save_location.text().strip())
        self.config.set('buffer_duration', self.buffer_duration.value())
        self.config.set('auto_save', self.auto_save.isChecked())
        self.config.set('keep_audio_file', self.keep_audio.isChecked())

        self.config.save()

        super().accept()
