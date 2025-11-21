import os
from typing import Optional
from dropbox import Dropbox, files, exceptions

from .paths import TASK_FILES, get_encrypted_file_path


def get_dropbox_token() -> Optional[str]:
    """Get Dropbox access token from .env file."""
    return os.getenv('MTD_DROPBOX_TOKEN')


def connect() -> Optional[Dropbox]:
    """Connect to Dropbox using access token from .env file."""
    token = get_dropbox_token()
    if not token:
        return None
    
    return Dropbox(token)


def upload_encrypted_files() -> bool:
    """Upload encrypted task files to Dropbox (excludes history.log)."""
    dbx = connect()
    if not dbx:
        print("No Dropbox token configured. Cannot upload encrypted files.")
        return False
    
    overwrite_mode = files.WriteMode.overwrite
    
    for plaintext_file in TASK_FILES:
        encrypted_path = get_encrypted_file_path(plaintext_file)
        
        assert os.path.exists(encrypted_path)
        dbx_path = f'/.mtd/encrypted/{os.path.basename(encrypted_path)}'
        
        try:
            with open(encrypted_path, 'rb') as f:
                data = f.read()
            
            dbx.files_upload(data, dbx_path, overwrite_mode)
        except exceptions.ApiError as err:
            print(f'Dropbox API error uploading {os.path.basename(encrypted_path)}: {err}')
            return False
    
    return True


def download_encrypted_files() -> bool:
    """Download encrypted task files from Dropbox (excludes history.log). Returns False if any files were not successfully downloaded."""
    dbx = connect()
    if not dbx:
        return False 
   
    success = True
    for plaintext_file in TASK_FILES:
        encrypted_path = get_encrypted_file_path(plaintext_file)
        dbx_path = f'/.mtd/encrypted/{os.path.basename(encrypted_path)}'
        
        try:
            _, data = dbx.files_download(dbx_path)
            
            os.makedirs(os.path.dirname(encrypted_path), exist_ok=True)
            
            with open(encrypted_path, 'wb') as f:
                f.write(data.content)
        except exceptions.ApiError as err:
            success = False
            if err.error.is_path() and err.error.get_path().is_not_found():
                print(f'File not found in Dropbox: {os.path.basename(encrypted_path)}!')
                continue

            print(f'Dropbox API error downloading {os.path.basename(encrypted_path)}: {err}.')
    
    return success

