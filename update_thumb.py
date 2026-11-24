import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_FILE = 'token.json'
if not os.path.exists(TOKEN_FILE):
    print("token.json not found")
    exit(1)

creds = Credentials.from_authorized_user_file(TOKEN_FILE)
if creds and creds.expired and creds.refresh_token:
    try:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            f.write(creds.to_json())
    except Exception as e:
        print("Refresh error:", e)

youtube = build('youtube', 'v3', credentials=creds)

video_id = 'sCGMaKVCJDw'
thumb_path = 'jtmh_hero_final.jpg'

if os.path.exists(thumb_path):
    try:
        print(f"Setting custom thumbnail for {video_id}...")
        res = youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumb_path, mimetype='image/jpeg')
        ).execute()
        print("Thumbnail updated successfully:", res)
    except Exception as e:
        print("Thumbnail error:", e)
else:
    print(f"Thumbnail file {thumb_path} not found!")

# Add to Playlist PLFCTerpJfOZc (Late Night Bollywood & Indie Lo-Fi)
playlist_id = 'PLFCTerpJfOZc'
try:
    print(f"Adding {video_id} to playlist {playlist_id}...")
    req = youtube.playlistItems().insert(
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
    pres = req.execute()
    print("Playlist item added successfully!")
except Exception as e:
    print("Playlist notice:", e)

print("Done update_thumb.py")
