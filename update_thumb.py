import os
import json
import traceback
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

log_lines = []

def log(msg):
    print(msg)
    log_lines.append(str(msg))

TOKEN_FILE = 'token.json'
if not os.path.exists(TOKEN_FILE):
    log("token.json not found")
    with open('update_result.txt', 'w') as f:
        f.write('\n'.join(log_lines))
    exit(1)

try:
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    log(f"Credentials loaded. Expired: {creds.expired}, Valid: {creds.valid}")
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            log("Credentials successfully refreshed with Request()")
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                f.write(creds.to_json())
        except Exception as re:
            log(f"Refresh error: {re}\n{traceback.format_exc()}")

    youtube = build('youtube', 'v3', credentials=creds)

    video_id = 'sCGMaKVCJDw'
    thumb_path = 'jtmh_hero_final.jpg'

    if os.path.exists(thumb_path):
        log(f"Setting custom thumbnail for {video_id} with file {thumb_path} (size={os.path.getsize(thumb_path)} bytes)...")
        req = youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumb_path, mimetype='image/jpeg')
        )
        res = req.execute()
        log(f"SUCCESS: Thumbnail updated: {res}")
    else:
        log(f"ERROR: {thumb_path} does not exist!")

    # Add to Playlist
    playlist_id = 'PLFCTerpJfOZc'
    try:
        log(f"Adding {video_id} to playlist {playlist_id}...")
        preq = youtube.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
        )
        pres = preq.execute()
        log(f"SUCCESS: Playlist item added: {pres.get('id')}")
    except Exception as pe:
        log(f"Playlist notice: {pe}")

except Exception as e:
    log(f"FATAL ERROR: {e}\n{traceback.format_exc()}")

with open('update_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(log_lines))

print("Wrote update_result.txt")
