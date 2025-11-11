"""
Configuration Manager for Meeting Transcriber
Handles all app settings and API keys
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Manages application configuration"""

    DEFAULT_CONFIG = {
        "openai_api_key": "",
        "anthropic_api_key": "",
        "google_drive_folder_id": "",
        "google_drive_credentials_path": "",
        "default_save_location": str(Path.home() / "Documents" / "Meeting Transcripts"),
        "auto_upload_drive": False,
        "auto_save": False,
        "mic_device_index": None,
        "speaker_detection": False,
        "keep_audio_file": False,
        "claude_model": "claude-sonnet-4-20250514",
        "whisper_model": "whisper-1",
        "buffer_duration": 5,  # seconds
        "sample_rate": 16000,
        "theme": "light",
        "window_geometry": None,
        "first_launch": True
    }

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration"""
        if config_path is None:
            config_dir = Path.home() / ".meeting-transcriber"
            config_dir.mkdir(exist_ok=True)
            self.config_path = config_dir / "config.json"
        else:
            self.config_path = Path(config_path)

        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                # Merge with defaults (in case new keys were added)
                config = self.DEFAULT_CONFIG.copy()
                config.update(loaded)
                return config
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()

    def save(self) -> bool:
        """Save current configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value

    def is_configured(self) -> bool:
        """Check if minimum configuration is complete"""
        return bool(self.config.get("openai_api_key"))

    def needs_setup(self) -> bool:
        """Check if setup wizard should run"""
        return self.config.get("first_launch", True) or not self.is_configured()

    def complete_setup(self) -> None:
        """Mark setup as complete"""
        self.config["first_launch"] = False
        self.save()

    def get_save_directory(self) -> Path:
        """Get and ensure save directory exists"""
        save_dir = Path(self.config["default_save_location"])
        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir
