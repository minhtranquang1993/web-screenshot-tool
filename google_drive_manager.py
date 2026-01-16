import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes define the level of access
# drive.file only sees files created by this app
# drive allows full access to list and upload
SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDriveManager:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
    def authenticate(self):
        """Authenticates with Google Drive API."""
        creds = None
        # Load existing token
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception:
                # If token is invalid, ignore it
                creds = None

        # If no valid credentials, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    # If refresh fails, re-auth
                    creds = self._run_oauth_flow()
            else:
                creds = self._run_oauth_flow()
            
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())

        self.service = build('drive', 'v3', credentials=creds)
        return True

    def _run_oauth_flow(self):
        """Runs the OAuth2 flow to get credentials."""
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(f"Không tìm thấy file {self.credentials_file}. Vui lòng tải từ Google Cloud Console.")
            
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_file, SCOPES)
        return flow.run_local_server(port=0)

    def list_folders(self):
        """Lists all folders in the Drive."""
        if not self.service:
            return []
            
        try:
            # List all folders (not just root)
            results = self.service.files().list(
                q="mimeType='application/vnd.google-apps.folder' and trashed=false",
                pageSize=100,
                fields="nextPageToken, files(id, name)"
            ).execute()
            items = results.get('files', [])
            # Add root folder option at the beginning
            root_option = {'id': 'root', 'name': '📁 My Drive (Thư mục gốc)'}
            return [root_option] + items
        except Exception as e:
            print(f"Lỗi khi lấy danh sách folder: {e}")
            return [{'id': 'root', 'name': '📁 My Drive (Thư mục gốc)'}]
            
    def upload_file(self, file_path, folder_id):
        """Uploads a file to a specific folder."""
        if not self.service:
            return None
            
        file_name = os.path.basename(file_path)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='image/jpeg')
        
        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            return file.get('id')
        except Exception as e:
            print(f"Lỗi khi upload file: {e}")
            return None
