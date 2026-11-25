import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

BASE_DIR = 'D:/lofi-autopilot'
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, 'client_secrets.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

def authenticate():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"[ERROR] '{CLIENT_SECRETS_FILE}' not found!")
        sys.exit(1)

    print("Opening Google OAuth sign-in flow...")
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        SCOPES,
        redirect_uri='http://localhost:8080/'
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    print(f"\nAUTH_URL: {auth_url}\n")
    
    creds = flow.run_local_server(port=8080, open_browser=True)

    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        f.write(creds.to_json())

    print("\nSUCCESS! Saved updated token to:", TOKEN_FILE)

if __name__ == '__main__':
    authenticate()
