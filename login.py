import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, 'client_secrets.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

def authenticate():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"\n[ERROR] '{CLIENT_SECRETS_FILE}' file nahi mili!")
        print("Kripya Google Cloud Console se 'client_secret_....json' download karke")
        print("use rename karein: client_secrets.json aur 'D:\\lofi-autopilot\\' me rakhein.\n")
        sys.exit(1)

    print("\n=======================================================")
    print("   YOUTUBE 1-TIME GOOGLE ACCOUNT AUTHORIZATION")
    print("=======================================================")
    print("Default browser (Brave/Chrome) me Google Login khul raha hai...")
    print("1. Apna YouTube channel wala Google Account select karein.")
    print("2. 'Google hasn't verified this app' aane par 'Continue' par click karein.")
    print("3. Checkboxes ko tick karke 'Continue / Allow' dabayein.\n")

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        f.write(creds.to_json())

    print("\n=======================================================")
    print("✅ SUCCESS! YouTube Authentication 100% Complete!")
    print(f"✅ Saved permanent token to: {TOKEN_FILE}")
    print("Ab auto-upload bilkul bina kisi rukawat ke chalega!")
    print("=======================================================\n")

if __name__ == '__main__':
    authenticate()
