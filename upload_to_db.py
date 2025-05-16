import os
import json
import dropbox
from secrets_loader import get_secret

def upload_file_to_dropbox(local_path: str, dropbox_folder: str = '/upload reports') -> str:
    """
    將本地檔案上傳到 Dropbox 的指定資料夾，返回 Dropbox 上的完整路徑。
    使用 Refresh Token 認證，憑證從 AWS Secrets Manager 載入。
    模式：覆蓋同名檔案。
    """    
    if not os.path.isfile(local_path):  #OUTPUT_PATH : Generated Excel File
        raise FileNotFoundError(f"本地檔案不存在：{local_path}")    
    
    # loads tokens from Secrets Managers
    try:
        secret = json.loads(get_secret()) #把一個 JSON 格式的字串 轉成 Python 字典（dict）
        app_key = secret['DROPBOX_APP_KEY']
        app_secret = secret['DROPBOX_APP_SECRET']
        refresh_token = secret['DROPBOX_REFRESH_TOKEN']
    except Exception as e:
        raise RuntimeError(f'Loading Dropbox token failed: {e}')
    
    #initializa Dropbox Client
    try:
        dbx = dropbox.Dropbox(
            app_key=app_key,
            app_secret=app_secret,
            oauth2_refresh_token=refresh_token
        )
        dbx.users_get_current_account() #verify connection
    except Exception as e:
        raise RecursionError(f'Dropbox Verification Failed: {e}')
    
    #Dropbox path for uploading file
    filename = os.path.basename(local_path)
    dropbox_path = os.path.join(dropbox_folder, filename).replace("\\", "/")

    #uploads file
    try:
        with open(local_path, 'rb') as f:
            dbx.files_upload(f.read(), dropbox_path)    #f.read(): read it as binary and out into memory
        print(f'Uploaded to Dropbox: {dropbox_path}')
        return dropbox_path     #return to main(), tells main() where it uploaded.
    except Exception as e:
        raise RuntimeError(f'upload failed: {e}')