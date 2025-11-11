"""
py2app setup script for Meeting Transcriber
Creates a standalone Mac .app bundle
"""

from setuptools import setup

APP = ['src/main_window.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': 'Meeting Transcriber',
        'CFBundleDisplayName': 'Meeting Transcriber',
        'CFBundleGetInfoString': 'Real-time meeting transcription and analysis',
        'CFBundleIdentifier': 'com.rozsagyene.meetingtranscriber',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 Rozsa Gyene. All rights reserved.',
        'NSMicrophoneUsageDescription': 'Meeting Transcriber needs access to your microphone to record and transcribe meetings.',
        'LSMinimumSystemVersion': '10.13.0',
    },
    'packages': [
        'PyQt6',
        'openai',
        'anthropic',
        'google',
        'googleapiclient',
        'google_auth_oauthlib',
        'numpy',
        'pyaudio',
    ],
    'includes': [
        'config',
        'audio_capture',
        'transcription',
        'claude_integration',
        'gdrive_uploader',
        'setup_wizard',
    ],
    'excludes': [
        'matplotlib',
        'scipy',
        'pandas',
        'tkinter',
    ],
    'resources': [],
    'frameworks': [],
    'optimize': 2,
}

setup(
    name='Meeting Transcriber',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
