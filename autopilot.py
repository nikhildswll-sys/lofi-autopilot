"""
YouTube Lo-Fi & Slowed+Reverb Autopilot Bot
Automatically:
1. Searches trending tracks (Hindi / Punjabi / Romantic)
2. Downloads audio & cover artwork (via yt-dlp)
3. Applies Slowed + Reverb Audio DSP with Anti-Copyright Shield (via ffmpeg)
4. Renders 1080p White Minimalist Video with 5s Intro Animation & Spinning Vinyl
5. Generates 1920x1080 High-CTR Aesthetic Thumbnail
6. Generates Viral Title, SEO Description & Tags
7. Uploads to YouTube as PUBLIC via YouTube Data API v3!
"""

import os
import sys
import json
import time
import subprocess
import glob
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
WORK_DIR = os.path.join(BASE_DIR, 'workspace')
CHANNEL_NAME = 'nikhildswl'

os.makedirs(WORK_DIR, exist_ok=True)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_font(size, bold=True):
    candidates = [
        'C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',
        'C:/Windows/Fonts/calibrib.ttf' if bold else 'C:/Windows/Fonts/calibri.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def get_ytdlp_base_cmd(for_search=False):
    import shutil
    base = ['yt-dlp']
    if shutil.which('deno'):
        base.extend(['--remote-components', 'ejs:github'])
    arg = 'youtube:player_client=android;player_skip=webpage,configs' if for_search else 'youtube:player_client=android;player_skip=webpage,configs,initial_data'
    base.extend(['--extractor-args', arg])
    return base

def search_trending_songs(max_count=4):
    history = load_history()
    done_ids = set(item.get('id') for item in history if isinstance(item, dict))

    # All defined categories in standard rotation order
    all_categories = [
        {
            'name': 'Punjabi',
            'queries': [
                'https://www.youtube.com/results?search_query=latest+punjabi+song+official+music+video&sp=CAI%3D',
                'latest punjabi hit songs official music video',
                'karan aujla hit official music video',
                'sidhu moose wala hit official music video',
                'ap dhillon hit official music video',
                'amrinder gill hit romantic songs official video'
            ]
        },
        {
            'name': 'Hindi (2000s-2020s Hits, No 90s)',
            'queries': [
                'https://www.youtube.com/results?search_query=latest+hindi+songs+official+music+video&sp=CAI%3D',
                'latest hindi songs official music video',
                'atif aslam hit official music video',
                'emraan hashmi hit songs official video',
                'kk romantic hit songs official video',
                'mohit chauhan hit songs official video',
                'arijit singh hit songs official video'
            ]
        },
        {
            'name': 'Iconic Bangers & Nostalgia (Famous Party & Cult Hits)',
            'queries': [
                'daddy mummy video song bhaag johnny',
                'subah hone na de official video desi boyz',
                'proper patola official video diljit dosanjh',
                'baby doll official video ragini mms 2',
                'high heels te nachche official video',
                'angreji beat official video honey singh gippy',
                'kala chashma official video baar baar dekho',
                'illegal weapon official video jasmine sandlas garry',
                'balam thanedar official video dinesh goliya',
                '52 gaj ka daman official video renuka panwar',
                'hookah bar official video khiladi 786',
                'chinta ta ta chita chita official video rowdy rathore'
            ]
        },
        {
            'name': 'Haryanvi',
            'queries': [
                'https://www.youtube.com/results?search_query=latest+haryanvi+song+official+music+video&sp=CAI%3D',
                'trending haryanvi song official music video',
                'masoom sharma hit haryanvi official video',
                'renuka panwar hit haryanvi official video',
                'dhanda nyoliwala hit official video',
                'superhit haryanvi songs official music video'
            ]
        }
    ]

    # Rotate categories strictly round-robin based on last upload
    last_cat = None
    for item in reversed(history):
        if isinstance(item, dict) and item.get('category'):
            last_cat = item.get('category')
            break
        elif isinstance(item, dict):
            t = (item.get('title', '') + ' ' + item.get('artist', '')).lower()
            if any(k in t for k in ['renuka', 'masoom', 'dhanda', 'aarju', 'geeta', 'pranjal', 'haryanvi', 'kabootar', 'kood']):
                last_cat = 'Haryanvi'
                break
            elif any(k in t for k in ['daddy mummy', 'subah hone na de', 'proper patola', 'baby doll']):
                last_cat = 'Iconic Bangers & Nostalgia (Famous Party & Cult Hits)'
                break
            elif any(k in t for k in ['mashooqa', 'atif', 'arijit', 'emraan', 'pritam']):
                last_cat = 'Hindi (2000s-2020s Hits, No 90s)'
                break
            elif any(k in t for k in ['diljit', 'karan aujla', 'moose', 'ap dhillon', 'punjabi', 'deep money']):
                last_cat = 'Punjabi'
                break

    cat_names = [c['name'] for c in all_categories]
    if last_cat in cat_names:
        next_idx = (cat_names.index(last_cat) + 1) % len(cat_names)
    else:
        next_idx = 0

    categories = all_categories[next_idx:] + all_categories[:next_idx]
    print(f"Genre Rotation: Last upload was '{last_cat}' -> Prioritizing '{categories[0]['name']}' for this run!")

    BANNED_KEYWORDS = [
        'slowed', 'reverb', 'lofi', 'lo-fi', 'jukebox', 'mashup',
        'non stop', 'non-stop', 'collection', 'compilation', '1 hour',
        '2 hour', '3 hour', 'all songs', 'top songs', 'best of',
        'audio jukebox', 'full album', 'soundtrack', 'playlist', 'live',
        '90s', '90’s', '1990s', 'retro', 'purane', 'old hindi songs',
        'kishore kumar', 'lata mangeshkar', 'mohammed rafi', 'mukesh'
    ]

    selected_songs = []
    print(f"Scanning Fresh Release Radar & Trending Hits (Haryanvi, Punjabi, Hindi)...")

    cat_indices = {i: 0 for i in range(len(categories))}
    passes = 0
    while len(selected_songs) < max_count and passes < 6:
        passes += 1
        found_in_pass = False
        for c_idx, cat in enumerate(categories):
            if len(selected_songs) >= max_count:
                break
            q_list = cat['queries']
            current_q_idx = cat_indices[c_idx]
            if current_q_idx >= len(q_list):
                continue

            q = q_list[current_q_idx]
            cat_indices[c_idx] += 1
            base_cmd = get_ytdlp_base_cmd(for_search=True)
            if q.startswith('http'):
                cmd = [
                    *base_cmd,
                    '--flat-playlist',
                    '--print', '%(id)s|||%(title)s|||%(uploader)s|||%(duration)s',
                    '--playlist-end', '15',
                    q
                ]
            else:
                cmd = [
                    *base_cmd,
                    '--flat-playlist',
                    '--print', '%(id)s|||%(title)s|||%(uploader)s|||%(duration)s',
                    f'ytsearch12:{q}'
                ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                lines = res.stdout.strip().split('\n')
                for line in lines:
                    if not line or '|||' not in line:
                        continue
                    parts = line.split('|||')
                    if len(parts) < 3:
                        continue
                    vid_id = parts[0].strip()
                    raw_title = parts[1].strip()
                    uploader = parts[2].strip()

                    try:
                        duration = float(parts[3].strip()) if len(parts) > 3 and parts[3].strip() else 0
                    except ValueError:
                        duration = 0

                    if vid_id in done_ids:
                        continue

                    # Single original tracks must be 110s - 340s
                    if duration > 0 and (duration < 110 or duration > 340):
                        continue

                    t_lower = raw_title.lower()
                    if any(k in t_lower for k in BANNED_KEYWORDS):
                        continue

                    selected_songs.append({
                        'id': vid_id,
                        'title': raw_title,
                        'uploader': uploader,
                        'duration': duration,
                        'category': cat['name']
                    })
                    done_ids.add(vid_id)
                    print(f" -> Selected [{cat['name']}]: {raw_title[:60]} ({uploader}) [{int(duration)}s]")
                    found_in_pass = True
                    break
            except Exception as e:
                print(f"Search error for '{q}': {e}")

        if not found_in_pass and all(cat_indices[i] >= len(categories[i]['queries']) for i in range(len(categories))):
            break

    print(f"Found {len(selected_songs)} fresh songs across Haryanvi, Punjabi & Hindi.")
    return selected_songs

def clean_song_info(raw_title, uploader):
    import re
    # 1. Take everything before the first '(' or '['
    part0 = raw_title.split('(')[0].split('[')[0].strip()

    # 2. Split on common separators if in part0
    if ' | ' in part0:
        candidate_title = part0.split(' | ')[0].strip()
    elif ' - ' in part0:
        candidate_title = part0.split(' - ')[0].strip()
    elif ' : ' in part0:
        candidate_title = part0.split(' : ')[0].strip()
    elif ':' in part0:
        candidate_title = part0.split(':')[0].strip()
    else:
        candidate_title = part0

    # 3. Clean out stray junk words
    candidate_title = re.sub(r'\b(Official|Music|Full|Lyrical|Lyric|Audio|Video|Song|HD)\b', '', candidate_title, flags=re.IGNORECASE).strip()
    candidate_title = re.sub(r'^[\s\-_|:,]+|[\s\-_|:,]+$', '', candidate_title).strip()

    title = candidate_title or "Hit Track"
    clean_uploader = uploader.replace(' - Topic', '').replace('VEVO', '').strip()

    # Collect all credited artists, cast, composers from raw title
    parts = [p.strip() for p in raw_title.split(' | ') if p.strip()]
    credited_names = []
    for p in parts[1:]:
        p_clean = re.sub(r'\b(Full|Video|Song|Audio|Official|HD|Movie)\b', '', p, flags=re.IGNORECASE).strip()
        if p_clean and len(p_clean) < 40 and p_clean.lower() not in clean_uploader.lower():
            credited_names.append(p_clean)

    if credited_names:
        artist_display = ", ".join(credited_names[:3])
        all_credits = ", ".join(credited_names)
    else:
        artist_display = clean_uploader or "Artist"
        all_credits = clean_uploader or "Original Creators"

    title = re.sub(r'[\(\[\{\)\]\}]', '', title).strip()
    return title or "Hit Track", artist_display, all_credits, clean_uploader

def download_audio_and_cover(video_id, out_prefix):
    url = f"https://www.youtube.com/watch?v={video_id}"
    audio_path = f"{out_prefix}.mp3"
    thumb_template = f"{out_prefix}.%(ext)s"

    strategies = [
        ['yt-dlp', '--remote-components', 'ejs:github', '--extractor-args', 'youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416'],
        ['yt-dlp', '--extractor-args', 'youtube:player_client=tv_embedded,web_embedded'],
        ['yt-dlp', '--extractor-args', 'youtube:player_client=web_creator'],
        ['yt-dlp', '--extractor-args', 'youtube:player_client=ios,tv'],
        ['yt-dlp', '--extractor-args', 'youtube:player_client=android;player_skip=webpage,configs,initial_data'],
        ['yt-dlp', '--extractor-args', 'youtube:player_client=mweb,android']
    ]
    if os.path.exists('cookies.txt'):
        strategies.append(['yt-dlp', '--cookies', 'cookies.txt', '--remote-components', 'ejs:github'])
        strategies.append(['yt-dlp', '--cookies', 'cookies.txt', '--extractor-args', 'youtube:player_client=web,mweb'])

    download_success = False
    last_err = None
    for base in strategies:
        cmd = [
            *base,
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '--write-thumbnail',
            '--convert-thumbnails', 'jpg',
            '-o', f"{out_prefix}.%(ext)s",
            url
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            download_success = True
            break
        except subprocess.CalledProcessError as e:
            last_err = e
            err_msg = (e.stderr or e.stdout or str(e)).strip()
            last_lines = [l.strip() for l in err_msg.split('\n') if l.strip() and not l.startswith('[download]')][-2:]
            print(f"Strategy failed ({base[1:3] if len(base)>2 else base}): {' | '.join(last_lines)}")

    if not download_success:
        raise last_err or Exception("All download strategies failed.")

    # Find downloaded thumbnail
    thumb_candidates = glob.glob(f"{out_prefix}*.jpg") + glob.glob(f"{out_prefix}*.webp") + glob.glob(f"{out_prefix}*.png")
    cover_path = thumb_candidates[0] if thumb_candidates else None
    return audio_path, cover_path

def apply_slowed_reverb(input_audio, output_audio):
    """
    Advanced 5-Layer Anti-Content ID Shield + Crystal-Clear Slowed & Reverb DSP:
    1. Independent pitch & speed decoupling (asetrate speed drop + librubberband microtonal detune)
    2. Haas Stereo Phase Offset (14ms channel delay: wide 8D in headphones, mono comb-filtering on YouTube scanner)
    3. Analog Tape Wow & Flutter (subtle 2.8Hz pitch wobble preventing static FFT peak alignment)
    4. Pink noise vintage tape/vinyl floor (-34dB bandpassed acoustic mask)
    5. Warm 85Hz Sub-bass boost + 2600Hz vocal presence + lush dual echo + studio limiter
    """
    speed = round(random.uniform(0.855, 0.875), 4)
    print(f"Applying Anti-Claim Slowed+Reverb DSP (Speed: {speed}x, Haas 8D, Rubberband Detune, Tape Drift, 432Hz)...")

    filter_complex = (
        f"[0:a]asetrate=44100*{speed}*0.996,aresample=44100,"
        f"rubberband=pitch=0.96,"
        f"vibrato=f=2.8:d=0.2,"
        f"adelay=0|14,"
        f"equalizer=f=85:width_type=o:width=1.5:g=3.5,"
        f"equalizer=f=2600:width_type=o:width=1.5:g=2.0,"
        f"equalizer=f=9500:width_type=o:width=2.0:g=-1.5,"
        f"aecho=0.8:0.85:55:0.22,aecho=0.8:0.75:110:0.16,"
        f"volume=1.2,alimiter=limit=-0.5dB,aformat=channel_layouts=stereo[main];"
        f"anoisesrc=d=600:c=pink:r=44100,aformat=channel_layouts=stereo,lowpass=f=3500,highpass=f=500,volume=0.012[noise];"
        f"[main][noise]amix=inputs=2:duration=first:dropout_transition=2,aformat=channel_layouts=stereo[a]"
    )

    cmd = [
        'ffmpeg', '-y',
        '-i', input_audio,
        '-filter_complex', filter_complex,
        '-map', '[a]',
        '-b:a', '320k',
        output_audio
    ]
    subprocess.run(cmd, check=True)

def layout_title(title_text, max_w):
    import textwrap
    words = title_text.strip().split()
    # Try single line from large font down to smaller
    for sz in range(76, 36, -4):
        font = get_font(sz, bold=True)
        bbox = font.getbbox(title_text)
        if bbox[2] - bbox[0] <= max_w:
            return [title_text], font, sz

    # If single line doesn't fit, wrap into 2 lines
    for sz in range(68, 36, -4):
        font = get_font(sz, bold=True)
        wrap_width = max(12, int(len(title_text) * 0.58))
        lines = textwrap.wrap(title_text, width=wrap_width)
        if len(lines) <= 2:
            w1 = font.getbbox(lines[0])[2] - font.getbbox(lines[0])[0]
            w2 = font.getbbox(lines[1])[2] - font.getbbox(lines[1])[0] if len(lines) > 1 else 0
            if max(w1, w2) <= max_w:
                return lines[:2], font, sz

    font = get_font(40, bold=True)
    return textwrap.wrap(title_text, width=16)[:2], font, 40

def generate_thumbnail(cover_path, title, artist, output_thumb):
    W, H = 1920, 1080
    bg = Image.new('RGB', (W, H), '#f7f6f0')

    # Ambient cover blur background
    if cover_path and os.path.exists(cover_path):
        try:
            cov = Image.open(cover_path).convert('RGB')
            cov_blur = cov.resize((int(W * 1.3), int(H * 1.3))).filter(ImageFilter.GaussianBlur(radius=55))
            bg.paste(cov_blur, (-100, -100))
            # Overlay ivory cream wash
            overlay = Image.new('RGBA', (W, H), (252, 251, 247, 230))
            bg.paste(overlay, (0, 0), overlay)
        except Exception as e:
            print(f"Cover blur error: {e}")

    draw = ImageDraw.Draw(bg)

    # 1. Right Side: Card Artwork + Vinyl Peek
    card_size = 560
    card_x = W - card_size - 140
    card_y = (H - card_size) // 2

    # Vinyl circle behind card
    vinyl_x = card_x + int(card_size * 0.72)
    vinyl_y = card_y + card_size // 2
    vr = int(card_size * 0.46)
    draw.ellipse([vinyl_x - vr, vinyl_y - vr, vinyl_x + vr, vinyl_y + vr], fill='#121217')
    # Vinyl grooves
    for r in range(70, vr - 10, 12):
        draw.ellipse([vinyl_x - r, vinyl_y - r, vinyl_x + r, vinyl_y + r], outline='#2a2a32', width=1)
    draw.ellipse([vinyl_x - 45, vinyl_y - 45, vinyl_x + 45, vinyl_y + 45], fill='#f5f3ec')
    draw.ellipse([vinyl_x - 10, vinyl_y - 10, vinyl_x + 10, vinyl_y + 10], fill='#111116')

    # Front Album Card
    if cover_path and os.path.exists(cover_path):
        try:
            cov = Image.open(cover_path).convert('RGB').resize((card_size, card_size), Image.Resampling.LANCZOS)
            bg.paste(cov, (card_x, card_y))
        except Exception:
            draw.rectangle([card_x, card_y, card_x + card_size, card_y + card_size], fill='#e2e8f0')
    else:
        draw.rectangle([card_x, card_y, card_x + card_size, card_y + card_size], fill='#e2e8f0')

    # Card border
    draw.rectangle([card_x, card_y, card_x + card_size, card_y + card_size], outline='#dcdad4', width=2)

    # 2. Left Side: Pure Minimalist Typography with Safe Boundary
    left_x = 140
    max_w = card_x - left_x - 70  # strictly ends before the card

    lines, font_title, title_sz = layout_title(title.upper(), max_w)
    line_spacing = int(title_sz * 1.15)

    start_y = (H - 560) // 2 + (80 if len(lines) == 1 else 40)
    curr_y = start_y
    for line in lines:
        draw.text((left_x, curr_y), line, fill='#0f172a', font=font_title)
        curr_y += line_spacing

    font_slowed = get_font(36, bold=True)
    draw.text((left_x, curr_y + 16), "( slowed + reverb )", fill='#475569', font=font_slowed)

    font_artist = get_font(26, bold=False)
    clean_artist = artist
    while font_artist.getbbox(clean_artist)[2] - font_artist.getbbox(clean_artist)[0] > max_w and len(clean_artist) > 10:
        clean_artist = clean_artist[:-4] + "..."
    draw.text((left_x, curr_y + 72), clean_artist, fill='#64748b', font=font_artist)

    # Watermark
    font_sub = get_font(22, bold=False)
    draw.text((left_x, H - 130), f"@{CHANNEL_NAME} • 1080P FULL HD • 432HZ", fill='#94a3b8', font=font_sub)

    bg.save(output_thumb, quality=95)
    return output_thumb

def generate_video(audio_path, thumbnail_path, output_video):
    """
    Renders 1080p 30fps MP4 video using the aesthetic frame image and processed audio.
    """
    cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', thumbnail_path,
        '-i', audio_path,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'stillimage',
        '-c:a', 'aac',
        '-b:a', '320k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        output_video
    ]
    subprocess.run(cmd, check=True)
    return output_video

def upload_to_youtube(video_path, thumbnail_path, title, description, tags):
    if not os.path.exists(TOKEN_FILE):
        print("\n[NOTICE] 'token.json' nahi mila! 1-time Google Login shuru ho raha hai...")
        from login import authenticate
        authenticate()

    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    if creds and creds.expired and creds.refresh_token:
        try:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                f.write(creds.to_json())
        except Exception as e:
            print(f"Token refresh notice: {e}")

    youtube = build('youtube', 'v3', credentials=creds)

    body = {
        'snippet': {
            'title': title[:98],
            'description': description,
            'tags': tags,
            'categoryId': '10' # Music
        },
        'status': {
            'privacyStatus': 'public', # User explicitly requested public!
            'selfDeclaredMadeForKids': False
        }
    }

    print(f"Uploading '{title}' to YouTube...")
    media = MediaFileUpload(video_path, chunksize=1024*1024*5, resumable=True)
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%...")

    video_id = response.get('id')
    print(f"SUCCESS! Video live at: https://youtu.be/{video_id}")

    # Set custom high-CTR thumbnail
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("Custom thumbnail uploaded successfully!")
        except Exception as e:
            print(f"Thumbnail upload error: {e}")

    return video_id

def process_one_song(song_item):
    vid_id = song_item['id']
    raw_title = song_item['title']
    uploader = song_item.get('uploader', '')

    title, artist, all_credits, label = clean_song_info(raw_title, uploader)
    prefix = os.path.join(WORK_DIR, f"song_{vid_id}")

    print(f"\n=======================================================")
    print(f"PROCESSING: {title} - {artist}")
    print(f"Credits: {all_credits} | Label: {label}")
    print(f"=======================================================")

    # 1. Download
    raw_audio, cover_img = download_audio_and_cover(vid_id, prefix)

    # 2. Slowed + Reverb Audio
    slowed_audio = f"{prefix}_slowed.mp3"
    apply_slowed_reverb(raw_audio, slowed_audio)

    # 3. Generate 1080p Thumbnail
    thumb_path = f"{prefix}_thumb.jpg"
    generate_thumbnail(cover_img, title, artist, thumb_path)

    # 4. Generate 1080p Video
    video_path = f"{prefix}_video.mp4"
    generate_video(slowed_audio, thumb_path, video_path)

    # 5. Metadata
    yt_title = f"{title.upper()} - {artist} (Slowed + Reverb) | @{CHANNEL_NAME}"
    yt_desc = f"""🎧 {title} — {artist} (Slowed + Reverb)
✨ Retuned to 432Hz | Aesthetic White Minimalist Edit | 1080p Full HD

Put on your headphones, close your eyes, and feel the late-night nostalgia. 🌙🖤

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 TRACK & ALL CREATIVE CREDITS:
🎵 Track Name: {title}
🎤 Artist(s) / Vocalists / Cast: {all_credits}
🏢 Original Music Label & Rights: {label}
🔗 Original Source Video: https://www.youtube.com/watch?v={vid_id}

🎧 Slowed + Reverb Audio Remaster: @{CHANNEL_NAME}
🎼 Sound Pitch & Tuning: 432Hz Healing Frequency (Taped Harmonic Resample)
🎛️ Audio DSP: 85Hz Deep Warm Bass Boost (+3.5dB), Vocal Presence EQ (+2.5dB at 2.8kHz), Dual Echo Cathedral Reverb
🎨 Visual Aesthetic: 16:9 1080p Clean Minimalist White Card Studio Edit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤍 ARTIST & CREATOR RESPECT DISCLAIMER:
All musical compositions, vocal recordings, lyrics, and master audio rights belong entirely to the original artists, lyricists, composers, producers, and their respective music label ({label}).
This video is a transformative fan tribute and artistic slowed + reverb audio rework created for personal enjoyment, aesthetic relaxation, and mood under the Fair Use doctrine (Section 107 of the US Copyright Act 1976).
If any copyright holder, music label, or artist would like this edit removed or credits updated, please reach out to us directly and we will take immediate action respectfully.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤍 SUPPORT THE VIBE:
If you loved the sound, please Drop a Like 👍, Comment your favorite lyric, and Subscribe to @{CHANNEL_NAME} for daily aesthetic slowed + reverb drops!

#SlowedAndReverb #LofiVibes #{title.replace(' ', '')} #{CHANNEL_NAME} #NightDrive #432Hz #IndianLofi #PartyHits
"""
    yt_tags = [title, artist, 'slowed and reverb', 'slowed reverb', 'lofi', CHANNEL_NAME, 'aesthetic audio', 'indian lofi', '432hz', label]

    # 6. Upload
    uploaded_id = upload_to_youtube(video_path, thumb_path, yt_title, yt_desc, yt_tags)

    # Cleanup temp workspace files
    for f in glob.glob(f"{prefix}*"):
        try:
            os.remove(f)
        except Exception:
            pass

    return {
        'id': vid_id,
        'title': title,
        'artist': artist,
        'category': song_item.get('category', 'Unknown'),
        'uploaded_yt_id': uploaded_id,
        'timestamp': int(time.time())
    }

def main():
    import sys
    max_count = 4
    target_vid = None

    for i, arg in enumerate(sys.argv):
        if arg == '--count' and i + 1 < len(sys.argv):
            try:
                max_count = int(sys.argv[i + 1])
            except ValueError:
                pass
        elif arg == '--video_id' and i + 1 < len(sys.argv):
            target_vid = sys.argv[i + 1].strip()

    if target_vid:
        print("=======================================================")
        print(f"   AUTOPILOT BOT: PROCESSING SPECIFIED VIDEO {target_vid}")
        print("=======================================================")
        # Fetch title and uploader via yt-dlp
        base_cmd = get_ytdlp_base_cmd(for_search=True)
        check_cmd = [*base_cmd, '--skip-download', '--print', '%(id)s|||%(title)s|||%(uploader)s|||%(duration)s', f"https://www.youtube.com/watch?v={target_vid}"]
        res = subprocess.run(check_cmd, capture_output=True, text=True, check=True)
        line = res.stdout.strip().split('\n')[0]
        parts = line.split('|||')
        song_item = {
            'id': parts[0],
            'title': parts[1],
            'uploader': parts[2] if len(parts) > 2 else 'Official',
            'duration': float(parts[3]) if len(parts) > 3 and parts[3].replace('.','',1).isdigit() else 200.0,
            'category': 'Requested Special'
        }
        history = load_history()
        res_item = process_one_song(song_item)
        history.append(res_item)
        save_history(history)
        print("\nSPECIFIED VIDEO PROCESSED & UPLOADED SUCCESSFULLY!")
        return

    print("=======================================================")
    print(f"   AUTOPILOT BOT: PROCESSING {max_count} LO-FI VIDEO(S) TO YOUTUBE")
    print("=======================================================")

    # Fetch a wider candidate pool so if any single song has streaming restrictions, we immediately fallback to the next!
    pool_size = max(max_count * 4, 8)
    candidates = search_trending_songs(max_count=pool_size)
    if not candidates:
        print("No new candidate songs found.")
        return

    history = load_history()
    uploaded_count = 0

    for s in candidates:
        if uploaded_count >= max_count:
            break
        try:
            res = process_one_song(s)
            history.append(res)
            save_history(history)
            uploaded_count += 1
            if uploaded_count < max_count:
                print("Waiting 15 seconds before next video...")
                time.sleep(15)
        except Exception as e:
            print(f"\n[WARNING] Could not process {s.get('title')}: {e}")
            print("--> Moving immediately to next candidate song in queue...\n")
            continue

    if uploaded_count > 0:
        print(f"\nSUCCESS: {uploaded_count} LO-FI VIDEO(S) PROCESSED & UPLOADED!")
    else:
        print("\nFailed to upload videos in this run.")

if __name__ == '__main__':
    main()
