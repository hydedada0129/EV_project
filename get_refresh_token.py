import os
import requests
import webbrowser
import threading
import time
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# Dropbox 設定
APP_KEY = os.getenv('DROPBOX_APP_KEY')
APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
REDIRECT_URI = 'http://localhost:8888'

AUTH_URL = 'https://www.dropbox.com/oauth2/authorize'
TOKEN_URL = 'https://api.dropboxapi.com/oauth2/token'

#接收Dropbox請求
class OAuthHandler(BaseHTTPRequestHandler):
    auth_code = None  # 類別變數：儲存授權碼
    def do_GET(self):
        #split out ?code=xxxx from reuqests URL
        query = self.path.split('?', 1)[-1]

        #convert query to dictionary format
        params = dict(qc.split('=') for qc in query.split('&') if '=' in qc)

        #grant dropbox auth code, and save it
        OAuthHandler.auth_code = params.get('code')

        # 回傳 200 OK 響應給瀏覽器(tells the browser the auth code has been received by the application)
        self.send_response(200)
        
        self.end_headers()  #HTTP headers : metadata for your web communication
        
        # 顯示簡單訊息讓使用者知道授權成功
        self.wfile.write(b'Authorization Succeeds! Please close this web page.')

#授權碼取得: AUTH_URL 'https://www.dropbox.com/oauth2/authorize'
'''https://www.dropbox.com/oauth2/authorize?client_id=<your_client_id>&response_type=code&redirect_uri=<your_redirect_uri>&token_access_type=offline'''
def get_authorization_code():
    #提供dropbox app 資料，送入AUTH_URL，並打開授權頁面
    params = {
        'client_id': APP_KEY,                    # 應用程式的 APP KEY
        'response_type': 'code',                 # 要求回傳授權碼 (authorization code)
        'redirect_uri': REDIRECT_URI,            # 授權後 Dropbox 導回的 URI
        'token_access_type': 'offline'           # 要求 refresh_token，可長期存取
    }

    # 將參數組合成完整授權網址
    auth_url = f"{AUTH_URL}?{urlencode(params)}"
    #open browser for your authorization page
    webbrowser.open(auth_url)

    #啟動本地伺服器以接收 Dropbox 回傳的授權碼 
    server = HTTPServer(('localhost', 8888), OAuthHandler)

    # 使用 Thread 啟動伺服器
    def run_server():
        server.handle_request()

    thread = threading.Thread(target=run_server)
    thread.start()

    # 等待 OAuthHandler.auth_code 被設定（最多 30 秒）
    for _ in range(300):
        if OAuthHandler.auth_code:
            break
        time.sleep(0.1)

    #回傳擷取到的授權碼
    return OAuthHandler.auth_code

# grant "refresh token" via TOKEN_URL : 'https://api.dropboxapi.com/oauth2/token'
def exchange_code_for_refresh_token(auth_code):
    # 向 Dropbox 發送 POST 請求，用授權碼換取 access_token 與 refresh_token
    response = requests.post(TOKEN_URL, data={
        'code': auth_code,                      # 從 Dropbox 回傳的授權碼
        'grant_type': 'authorization_code',     # 授權流程類型
        'client_id': APP_KEY,                   # 應用程式的 APP KEY
        'client_secret': APP_SECRET,           # 應用程式的 APP SECRET
        'redirect_uri': REDIRECT_URI            # 必須與 AUTH_URL 中一致
    })
    print(response.status_code)         # 印出狀態碼
    print(response.json())              # 看整個回傳內容

    # 如果請求失敗則拋出例外
    response.raise_for_status()

    # 從回應中取得 refresh_token 並回傳
    return response.json().get('refresh_token')

#自動儲存 refresh_token 到 .env
def save_refresh_token_to_env(token):
    from pathlib import Path
    
    env_path = Path('.env')

    # 若.env已存在，先讀取內容
    if env_path.exists():
        with open(env_path, 'r') as file:
            lines = file.readlines()
    else:
        lines = []

    # 移除舊的 REFRESH_TOKEN 行
    lines = [line for line in lines if not line.startswith('DROPBOX_REFRESH_TOKEN=')]

    # 加入新的 token
    lines.append(f'DROPBOX_REFRESH_TOKEN={token}\n')

    # 寫回 .env
    with open(env_path, 'w') as file:
        file.writelines(lines)

    print("已自動儲存 refresh token 到 .env")

def main():
    try:
        auth_code = get_authorization_code()
        print(f"auth code: {auth_code}")      # 印出確認

        if not auth_code:
            print('grants authorization code failed.')
            return
        
        # refresh_token = exchange_code_for_refresh_token(auth_code)
        refresh_token = exchange_code_for_refresh_token(auth_code)  # 換取 refresh_token
        print(f"Refresh Token: {refresh_token}")

        # 儲存到 .env
        save_refresh_token_to_env(refresh_token)

    except Exception as e:
        print(f"失敗: {e}")       

if __name__ == "__main__":
    main()