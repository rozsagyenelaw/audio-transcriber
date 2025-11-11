"""
Google Drive Uploader Module
Handles automatic upload of transcripts to Google Drive
"""

import os
import pickle
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


class GDriveUploader:
    """Handles Google Drive uploads for meeting transcripts"""

    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self, credentials_path: Optional[str] = None,
                 token_path: Optional[str] = None,
                 folder_id: Optional[str] = None):
        """
        Initialize Google Drive uploader

        Args:
            credentials_path: Path to OAuth credentials JSON
            token_path: Path to save/load token
            folder_id: Google Drive folder ID for uploads
        """
        self.credentials_path = credentials_path
        self.token_path = token_path or str(Path.home() / '.meeting-transcriber' / 'gdrive_token.pickle')
        self.folder_id = folder_id

        self.service = None
        self.creds = None

    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive

        Returns:
            True if authentication successful
        """
        try:
            # Load existing credentials
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)

            # Refresh if expired
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())

            # Need new authentication
            elif not self.creds or not self.creds.valid:
                if not self.credentials_path or not os.path.exists(self.credentials_path):
                    print("Google Drive credentials not found")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )

                # Use local server for authentication
                self.creds = flow.run_local_server(
                    port=8080,
                    success_message='Authentication successful! You can close this window.',
                    open_browser=True
                )

                # Save credentials for future use
                os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)

            # Build service
            self.service = build('drive', 'v3', credentials=self.creds)
            return True

        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def is_authenticated(self) -> bool:
        """Check if authenticated and service is ready"""
        return self.service is not None

    def upload_file(self, file_path: str,
                   folder_id: Optional[str] = None,
                   description: Optional[str] = None) -> Optional[str]:
        """
        Upload file to Google Drive

        Args:
            file_path: Path to file to upload
            folder_id: Folder ID (uses default if not specified)
            description: File description

        Returns:
            File ID if successful, None otherwise
        """
        if not self.is_authenticated():
            if not self.authenticate():
                return None

        try:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"File not found: {file_path}")
                return None

            # Use specified folder or default
            target_folder = folder_id or self.folder_id

            # File metadata
            file_metadata = {
                'name': file_path.name,
            }

            if target_folder:
                file_metadata['parents'] = [target_folder]

            if description:
                file_metadata['description'] = description

            # Determine MIME type
            mime_type = self._get_mime_type(file_path)

            # Upload file
            media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()

            print(f"Uploaded: {file.get('name')} (ID: {file.get('id')})")
            return file.get('id')

        except HttpError as e:
            print(f"Google Drive API error: {e}")
            return None
        except Exception as e:
            print(f"Upload error: {e}")
            return None

    def upload_transcript(self, transcript_path: str,
                         analysis_path: Optional[str] = None,
                         meeting_title: Optional[str] = None) -> Dict[str, Optional[str]]:
        """
        Upload transcript and optionally analysis to Google Drive

        Args:
            transcript_path: Path to transcript file
            analysis_path: Optional path to analysis file
            meeting_title: Meeting title for description

        Returns:
            Dictionary with file IDs for transcript and analysis
        """
        result = {
            'transcript_id': None,
            'analysis_id': None
        }

        # Create description
        description = f"Meeting transcript"
        if meeting_title:
            description = f"{meeting_title} - Transcript"

        description += f" - Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Upload transcript
        result['transcript_id'] = self.upload_file(
            transcript_path,
            description=description
        )

        # Upload analysis if provided
        if analysis_path and os.path.exists(analysis_path):
            analysis_desc = description.replace('Transcript', 'Analysis')
            result['analysis_id'] = self.upload_file(
                analysis_path,
                description=analysis_desc
            )

        return result

    def create_folder(self, folder_name: str,
                     parent_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Create folder in Google Drive

        Args:
            folder_name: Name of folder to create
            parent_folder_id: Parent folder ID

        Returns:
            Folder ID if successful
        """
        if not self.is_authenticated():
            if not self.authenticate():
                return None

        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]

            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name'
            ).execute()

            print(f"Created folder: {folder.get('name')} (ID: {folder.get('id')})")
            return folder.get('id')

        except Exception as e:
            print(f"Error creating folder: {e}")
            return None

    def get_or_create_folder(self, folder_name: str,
                            parent_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Get existing folder or create if it doesn't exist

        Args:
            folder_name: Folder name
            parent_folder_id: Parent folder ID

        Returns:
            Folder ID
        """
        if not self.is_authenticated():
            if not self.authenticate():
                return None

        try:
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"

            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"

            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])

            if files:
                return files[0]['id']
            else:
                return self.create_folder(folder_name, parent_folder_id)

        except Exception as e:
            print(f"Error getting/creating folder: {e}")
            return None

    def list_files(self, folder_id: Optional[str] = None,
                  max_results: int = 100) -> list:
        """
        List files in Google Drive folder

        Args:
            folder_id: Folder ID (None for root)
            max_results: Maximum number of results

        Returns:
            List of file metadata
        """
        if not self.is_authenticated():
            if not self.authenticate():
                return []

        try:
            query = "trashed=false"

            if folder_id:
                query += f" and '{folder_id}' in parents"

            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields='files(id, name, mimeType, createdTime, modifiedTime, webViewLink)'
            ).execute()

            return results.get('files', [])

        except Exception as e:
            print(f"Error listing files: {e}")
            return []

    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from Google Drive

        Args:
            file_id: File ID to delete

        Returns:
            True if successful
        """
        if not self.is_authenticated():
            if not self.authenticate():
                return False

        try:
            self.service.files().delete(fileId=file_id).execute()
            print(f"Deleted file: {file_id}")
            return True

        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def get_file_link(self, file_id: str) -> Optional[str]:
        """
        Get shareable link for file

        Args:
            file_id: File ID

        Returns:
            Web view link
        """
        if not self.is_authenticated():
            if not self.authenticate():
                return None

        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()

            return file.get('webViewLink')

        except Exception as e:
            print(f"Error getting file link: {e}")
            return None

    def _get_mime_type(self, file_path: Path) -> str:
        """Determine MIME type based on file extension"""
        extension = file_path.suffix.lower()

        mime_types = {
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.srt': 'text/plain',
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
        }

        return mime_types.get(extension, 'application/octet-stream')

    def set_folder_id(self, folder_id: str):
        """Set default folder ID for uploads"""
        self.folder_id = folder_id

    def clear_credentials(self):
        """Clear saved credentials (for re-authentication)"""
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
            print("Credentials cleared")
