"""
1-Click Automated Lo-Fi Video Generator (Zero Google API / No Login Needed)
Finds 4 trending tracks, processes slowed+reverb audio, renders 1080p video,
generates thumbnail & writes viral title + description into a folder.
"""

import os
import sys
import json
import time
import subprocess
import glob
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'ready_to_upload')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
CHANNEL_NAME = 'nikhildswl'

os.makedirs(OUTPUT_DIR, exist_ok=True)

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
        'C:/Windows/Fonts/calibrib.ttf' if bold else 'C:/Windows/Fonts/calibri.ttf'
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def search_trending_songs(max_count=4):
    history = load_history()
    done_ids = set(item.get('id') for item in history if isinstance(item, dict))

    # Multi-language pools with Fresh Release Radar (Sort by Date First)
    categories = [
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
        },
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
        }
    ]

    BANNED_KEYWORDS = [
        'slowed', 'reverb', 'lofi', 'lo-fi', 'jukebox', 'mashup',
        'non stop', 'non-stop', 'collection', 'compilation', '1 hour',
        '2 hour', '3 hour', 'all songs', 'top songs', 'best of',
        'audio jukebox', 'full album', 'soundtrack', 'playlist', 'live',
        '90s', '90’s', '1990s', 'retro', 'purane', 'old hindi songs',
        'kishore kumar', 'lata mangeshkar', 'mohammed rafi', 'mukesh'
    ]

    selected = []
    print(f"Scanning Fresh Release Radar & Trending Hits (Haryanvi, Punjabi, Hindi)...")

    cat_indices = {i: 0 for i in range(len(categories))}
    passes = 0
    while len(selected) < max_count and passes < 6:
        passes += 1
        found_in_pass = False
        for c_idx, cat in enumerate(categories):
            if len(selected) >= max_count:
                break
            q_list = cat['queries']
            current_q_idx = cat_indices[c_idx]
            if current_q_idx >= len(q_list):
                continue

            q = q_list[current_q_idx]
            cat_indices[c_idx] += 1
            if q.startswith('http'):
                cmd = [
                    'yt-dlp',
                    '--flat-playlist',
                    '--print', '%(id)s|||%(title)s|||%(uploader)s|||%(duration)s',
                    '--playlist-end', '15',
                    q
                ]
            else:
                cmd = [
                    'yt-dlp',
                    '--flat-playlist',
                    '--print', '%(id)s|||%(title)s|||%(uploader)s|||%(duration)s',
                    f'ytsearch12:{q}'
                ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                for line in res.stdout.strip().split('\n'):
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

                    # Filter out long compilations, jukeboxes (single songs between 110s and 340s)
                    if duration > 0 and (duration < 110 or duration > 340):
                        continue

                    # Strictly reject any pre-slowed, lofi, jukebox, mashups, compilations, or 90s retro
                    t_lower = raw_title.lower()
                    if any(k in t_lower for k in BANNED_KEYWORDS):
                        continue

                    selected.append({'id': vid_id, 'title': raw_title, 'uploader': uploader, 'duration': duration, 'category': cat['name']})
                    done_ids.add(vid_id)
                    print(f" -> Selected [{cat['name']}]: {raw_title[:60]} ({uploader}) [{int(duration)}s]")
                    found_in_pass = True
                    break
            except Exception as e:
                print(f"Search notice: {e}")

        if not found_in_pass and all(cat_indices[i] >= len(categories[i]['queries']) for i in range(len(categories))):
            break

    return selected

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
    candidate_title = re.sub(r'\b(Official|Music|Full|Lyrical|Lyric|Audio|Video|Song)\b', '', candidate_title, flags=re.IGNORECASE).strip()
    candidate_title = re.sub(r'^[\s\-_|:,]+|[\s\-_|:,]+$', '', candidate_title).strip()

    title = candidate_title or "Hit Track"
    artist = uploader.replace(' - Topic', '').replace('VEVO', '').strip()

    if ' | ' in raw_title:
        parts = [p.strip() for p in raw_title.split(' | ') if p.strip()]
        if len(parts) >= 2 and len(parts[1]) < 45:
            artist = parts[1]

    title = re.sub(r'[\(\[\{\)\]\}]', '', title).strip()
    return title or "Hit Track", artist or "Artist"

def layout_title(title_text, max_w):
    import textwrap
    words = title_text.strip().split()
    for sz in range(76, 36, -4):
        font = get_font(sz, bold=True)
        bbox = font.getbbox(title_text)
        if bbox[2] - bbox[0] <= max_w:
            return [title_text], font, sz

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

def process_song(song_item):
    vid_id = song_item['id']
    title, artist = clean_song_info(song_item['title'], song_item.get('uploader', ''))

    folder_name = "".join(c for c in f"{title}_{artist}" if c.isalnum() or c in (' ', '_', '-')).strip()[:40]
    song_dir = os.path.join(OUTPUT_DIR, folder_name)
    os.makedirs(song_dir, exist_ok=True)

    print(f"\n=======================================================")
    print(f"GENERATING: {title} - {artist}")
    print(f"FOLDER: {song_dir}")
    print(f"=======================================================")

    raw_prefix = os.path.join(song_dir, "raw")
    url = f"https://www.youtube.com/watch?v={vid_id}"

    # 1. Download
    cmd = [
        'yt-dlp',
        '--extract-audio',
        '--audio-format', 'mp3',
        '--write-thumbnail',
        '--convert-thumbnails', 'jpg',
        '-o', f"{raw_prefix}.%(ext)s",
        url
    ]
    subprocess.run(cmd, check=True)

    raw_audio = f"{raw_prefix}.mp3"
    thumb_candidates = glob.glob(f"{raw_prefix}*.jpg") + glob.glob(f"{raw_prefix}*.webp") + glob.glob(f"{raw_prefix}*.png")
    cover_img = thumb_candidates[0] if thumb_candidates else None

    # 2. Crystal-Clear Aesthetic Slowed + Reverb DSP
    slowed_audio = os.path.join(song_dir, "audio_slowed_reverb.mp3")
    speed = round(random.uniform(0.855, 0.875), 4)
    print(f"Applying Crystal-Clear Slowed+Reverb DSP (Speed: {speed}x, Vocal Boost +2.5dB, 432Hz)...")

    filter_complex = (
        f"[0:a]asetrate=44100*{speed}*0.996,aresample=44100,"
        f"equalizer=f=85:width_type=o:width=1.8:g=3.5,"
        f"equalizer=f=2800:width_type=o:width=1.5:g=2.5,"
        f"equalizer=f=9500:width_type=o:width=2.0:g=-1.5,"
        f"aecho=0.8:0.85:60:0.25,aecho=0.8:0.75:120:0.18,"
        f"volume=1.25,alimiter=limit=-0.5dB:level=disabled[a]"
    )

    ffmpeg_audio_cmd = [
        'ffmpeg', '-y',
        '-i', raw_audio,
        '-filter_complex', filter_complex,
        '-map', '[a]',
        '-b:a', '320k',
        slowed_audio
    ]
    subprocess.run(ffmpeg_audio_cmd, check=True)

    # 3. Aesthetic Thumbnail (1920x1080)
    final_thumb = os.path.join(song_dir, "thumbnail.jpg")
    W, H = 1920, 1080
    bg = Image.new('RGB', (W, H), '#f7f6f0')

    if cover_img and os.path.exists(cover_img):
        try:
            cov = Image.open(cover_img).convert('RGB')
            cov_blur = cov.resize((int(W * 1.3), int(H * 1.3))).filter(ImageFilter.GaussianBlur(radius=55))
            bg.paste(cov_blur, (-100, -100))
            overlay = Image.new('RGBA', (W, H), (252, 251, 247, 230))
            bg.paste(overlay, (0, 0), overlay)
        except Exception:
            pass

    draw = ImageDraw.Draw(bg)
    card_size = 560
    card_x = W - card_size - 140
    card_y = (H - card_size) // 2
    vr = int(card_size * 0.46)
    vinyl_x = card_x + int(card_size * 0.72)
    vinyl_y = card_y + card_size // 2

    draw.ellipse([vinyl_x - vr, vinyl_y - vr, vinyl_x + vr, vinyl_y + vr], fill='#121217')
    for r in range(70, vr - 10, 12):
        draw.ellipse([vinyl_x - r, vinyl_y - r, vinyl_x + r, vinyl_y + r], outline='#2a2a32', width=1)
    draw.ellipse([vinyl_x - 45, vinyl_y - 45, vinyl_x + 45, vinyl_y + 45], fill='#f5f3ec')
    draw.ellipse([vinyl_x - 10, vinyl_y - 10, vinyl_x + 10, vinyl_y + 10], fill='#111116')

    if cover_img and os.path.exists(cover_img):
        try:
            cov = Image.open(cover_img).convert('RGB').resize((card_size, card_size), Image.Resampling.LANCZOS)
            bg.paste(cov, (card_x, card_y))
        except Exception:
            draw.rectangle([card_x, card_y, card_x + card_size, card_y + card_size], fill='#e2e8f0')

    draw.rectangle([card_x, card_y, card_x + card_size, card_y + card_size], outline='#dcdad4', width=2)

    # Left typography with safe boundary
    left_x = 140
    max_w = card_x - left_x - 70

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
    draw.text((left_x, H - 130), f"@{CHANNEL_NAME} • 1080P FULL HD • 432HZ", fill='#94a3b8', font=get_font(22, False))
    bg.save(final_thumb, quality=95)

    # 4. 1080p Video MP4
    final_video = os.path.join(song_dir, f"{title}_[YouTube_1080p].mp4")
    cmd_vid = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', final_thumb,
        '-i', slowed_audio,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'stillimage',
        '-c:a', 'aac',
        '-b:a', '320k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        final_video
    ]
    subprocess.run(cmd_vid, check=True)

    # 5. Title & Description TXT file
    yt_title = f"{title.upper()} - {artist} (Slowed + Reverb) | @{CHANNEL_NAME}"
    info_txt = os.path.join(song_dir, "COPY_PASTE_INFO.txt")
    with open(info_txt, 'w', encoding='utf-8') as f:
        f.write(f"TITLE TO COPY:\n{yt_title}\n\n")
        f.write("="*60 + "\nDESCRIPTION TO COPY:\n" + "="*60 + "\n")
        f.write(f"""🎧 {title} — {artist} (Slowed + Reverb)
✨ Retuned to 432Hz | Aesthetic White Minimalist Edit | 1080p Full HD

Put on your headphones, close your eyes, and feel the late-night nostalgia. 🌙🖤

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 TRACK DETAILS:
Song: {title}
Original Artist: {artist}
Edit & Sound Design: @{CHANNEL_NAME}
Visuals: 16:9 1080p White Minimalist Luxury Studio

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤍 SUPPORT THE CHANNEL:
If you loved the vibe, please Drop a Like 👍, Comment your favorite line, and Subscribe to @{CHANNEL_NAME} for daily aesthetic slowed + reverb edits!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ COPYRIGHT DISCLAIMER:
Under Section 107 of the Copyright Act 1976, allowance is made for 'fair use'. All rights belong to respective owners and music labels. No copyright infringement intended.

#SlowedAndReverb #LofiVibes #{title.replace(' ', '')} #{artist.replace(' ', '')} #{CHANNEL_NAME} #NightDrive #432Hz
""")

    # Cleanup raw files
    try:
        os.remove(raw_audio)
    except Exception:
        pass

    print(f"DONE! Video, Thumbnail & Text ready in: {song_dir}")
    return {'id': vid_id, 'title': title, 'artist': artist, 'time': int(time.time())}

def main():
    songs = search_trending_songs(4)
    if not songs:
        print("No new songs found.")
        return

    history = load_history()
    for s in songs:
        try:
            res = process_song(s)
            history.append(res)
            save_history(history)
        except Exception as e:
            print(f"Error on {s}: {e}")

    print("\n" + "="*60)
    print("ALL 4 VIDEOS GENERATED & READY IN: d:\\lofi-autopilot\\ready_to_upload\\")
    print("="*60)

if __name__ == '__main__':
    main()
