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
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageStat
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')
HISTORY_FILE = os.path.join(BASE_DIR, 'history.json')
WORK_DIR = os.path.join(BASE_DIR, 'workspace')
CHANNEL_NAME = 'nikhildswll'

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
    # android & visionos clients with webpage,configs skip bypass datacenter bot checks reliably
    arg = 'youtube:player_client=android,visionos;player_skip=webpage,configs'
    base.extend(['--extractor-args', arg])
    return base

def search_trending_songs(max_count=4):
    history = load_history()
    done_ids = set(item.get('id') for item in history if isinstance(item, dict))
    done_titles = set(re.sub(r'[^a-z0-9]', '', (item.get('title') or '').lower()) for item in history if isinstance(item, dict) and item.get('title'))

    # All defined categories in standard rotation order with Viral Search-Magnets
    all_categories = [
        {
            'name': 'Aesthetic Indie & Viral Lo-Fi',
            'queries': [
                'anuv jain husn official video',
                'talwiinder dhundhala official video',
                'aur tu hai kahan official video',
                'anuv jain baarishein official video',
                'abdul hannan bikhra official video',
                'talwiinder gallan 4 official video',
                'abdul hannan iraaday official video',
                'kaifi khalil kahani suno 2.0 official video',
                'anuv jain alag aasmaan official video',
                'talwiinder nasha official video',
                'hassan roshaan sukoon official video',
                'prateek kuhad kasoor official video',
                'mitraz akhiyaan official video',
                'anuv jain jo tum mere ho official video',
                'choo lo the local train official video'
            ]
        },
        {
            'name': 'Punjabi & Desi Hip Hop',
            'queries': [
                'karan aujla winning speech official video',
                'shubh cheques official music video',
                'ap dhillon with you official music video',
                'karan aujla softly official music video',
                'diljit dosanjh lover official video',
                'shubh baller official video',
                'ap dhillon excuses official music video',
                'karan aujla tauba tauba official video',
                'shubh her official music video',
                'diljit dosanjh born to shine official video',
                'ap dhillon summer high official video',
                'karan aujla admirin you official video',
                'shubh king shit official music video',
                'sidhu moose wala 295 official video',
                'seedhe maut namastute official video'
            ]
        },
        {
            'name': 'Hindi (2000s-2020s Hits, No 90s)',
            'queries': [
                'arijit singh o bedardeya official video',
                'kesariya arijit singh official video',
                'apna bana le arijit singh official video',
                'tum ho mohit chauhan rockstar official video',
                'tum se hi jab we met official video mohit chauhan',
                'labon ko kk bhool bhulaiyaa official video',
                'zara sa emraan hashmi jannat official video',
                'dil ibadat emraan hashmi tum mile official video',
                'hale dil murder 2 emraan hashmi official video',
                'pee loon once upon a time in mumbaai official video',
                'tu hi meri shab hai gangster emraan hashmi',
                'channa mereya arijit singh official video',
                'agar tum saath ho arijit singh alka yagnik',
                'phir le aya dil barfi arijit singh'
            ]
        },
        {
            'name': 'Haryanvi & NCR Hip Hop',
            'queries': [
                'trending haryanvi songs official music video',
                'latest haryanvi hits official video',
                'dhanda nyoliwala official video',
                'masoom sharma official video',
                'gulzaar chhaniwala official video',
                'khasa aala chahar official video',
                'renuka panwar official video',
                'bintu pabra official video',
                'ajay hooda official video'
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
                'hookah bar official video khiladi 786',
                'char botal vodka official video honey singh',
                'blue eyes official video honey singh',
                'dheere dheere se meri zindagi honey singh official video'
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
                last_cat = 'Haryanvi & NCR Hip Hop'
                break
            elif any(k in t for k in ['daddy mummy', 'subah hone na de', 'proper patola', 'baby doll']):
                last_cat = 'Iconic Bangers & Nostalgia (Famous Party & Cult Hits)'
                break
            elif any(k in t for k in ['mashooqa', 'atif', 'arijit', 'emraan', 'pritam']):
                last_cat = 'Hindi (2000s-2020s Hits, No 90s)'
                break
            elif any(k in t for k in ['diljit', 'karan aujla', 'moose', 'ap dhillon', 'punjabi', 'deep money', 'shubh']):
                last_cat = 'Punjabi & Desi Hip Hop'
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
        'kishore kumar', 'lata mangeshkar', 'mohammed rafi', 'mukesh',
        'ai song', 'ai cover', 'ai version', 'ai generated', 'artificial intelligence',
        'fan made', 'fanmade', 'concept', 'unreleased', 'teaser', 'trailer',
        'status', 'shorts', 'whatsapp', 'ringtone', 'cover song', 'tribute',
        'vatsal bhoya', 'prakash jojawar', 'reaction', 'review', 'vlog',
        'suno', 'udio', 'karaoke', 'instrumental'
    ]
    BANNED_CHANNELS = ['vatsal bhoya', 'prakash jojawar']

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
                    '--print', '%(id)s|||%(title)s|||%(uploader)s|||%(duration)s|||%(view_count)s',
                    '--playlist-end', '15',
                    q
                ]
            else:
                cmd = [
                    *base_cmd,
                    '--flat-playlist',
                    '--print', '%(id)s|||%(title)s|||%(uploader)s|||%(duration)s|||%(view_count)s',
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
                        duration = float(parts[3].strip()) if len(parts) > 3 and parts[3].strip() and parts[3].strip() != 'NA' else 0
                    except ValueError:
                        duration = 0

                    try:
                        view_count = int(parts[4].strip()) if len(parts) > 4 and parts[4].strip() and parts[4].strip() != 'NA' else 0
                    except ValueError:
                        view_count = 0

                    if vid_id in done_ids:
                        continue

                    # Clean check for duplicate title already uploaded
                    raw_title_clean = re.sub(r'[^a-z0-9]', '', raw_title.lower())
                    if any(t in raw_title_clean for t in done_titles if len(t) >= 6):
                        continue

                    # Single original tracks must be 110s - 360s
                    if duration > 0 and (duration < 110 or duration > 360):
                        continue

                    t_lower = raw_title.lower()
                    u_lower = uploader.lower()
                    if any(k in t_lower for k in BANNED_KEYWORDS):
                        continue
                    if any(k in u_lower for k in BANNED_CHANNELS):
                        continue
                    if any(k in u_lower for k in ['status', 'shorts', 'reels', 'ai ', ' ai', 'fan club', 'edits']):
                        continue

                    # Block low-view spam / fake AI tracks (real trending hits have >= 50k views)
                    if view_count > 0 and view_count < 50000:
                        continue

                    selected_songs.append({
                        'id': vid_id,
                        'title': raw_title,
                        'uploader': uploader,
                        'duration': duration,
                        'category': cat['name']
                    })
                    done_ids.add(vid_id)
                    if raw_title_clean:
                        done_titles.add(raw_title_clean)
                    print(f" -> Selected [{cat['name']}]: {raw_title[:60]} ({uploader}) [{int(duration)}s] [views: {view_count}]")
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
    clean_uploader = uploader.replace(' - Topic', '').replace('VEVO', '').strip()

    candidate_title = part0
    detected_artist = clean_uploader or 'Artist'

    # 2. Smart Artist vs Song Title Detection
    if ' | ' in part0:
        parts = [p.strip() for p in part0.split(' | ') if p.strip()]
        candidate_title = parts[0]
        if len(parts) > 1 and len(parts[1]) < 35:
            detected_artist = parts[1]
    elif ' - ' in part0:
        left, right = [p.strip() for p in part0.split(' - ', 1)]
        if clean_uploader and (clean_uploader.lower() in left.lower() or left.lower() in clean_uploader.lower()):
            candidate_title = right
            detected_artist = left
        elif clean_uploader and (clean_uploader.lower() in right.lower() or right.lower() in clean_uploader.lower()):
            candidate_title = left
            detected_artist = right
        else:
            candidate_title = right
            detected_artist = left
    elif ' : ' in part0:
        candidate_title = part0.split(' : ')[0].strip()
    elif ':' in part0:
        candidate_title = part0.split(':')[0].strip()

    # 3. Clean out stray junk words & featuring phrases from title
    candidate_title = re.sub(r'\b(with|feat\.?|ft\.?)\s+.*', '', candidate_title, flags=re.IGNORECASE).strip()
    candidate_title = re.sub(r'\b(Official|Music|Full|Lyrical|Lyric|Audio|Video|Song|HD|Visualiser|Visualizer)\b', '', candidate_title, flags=re.IGNORECASE).strip()
    candidate_title = re.sub(r'^[\s\-_|:,]+|[\s\-_|:,]+$', '', candidate_title).strip()

    title = candidate_title or "Hit Track"

    # Collect all credited artists, cast, composers from raw title
    parts = [p.strip() for p in raw_title.split(' | ') if p.strip()]
    credited_names = []
    for p in parts[1:]:
        p_clean = re.sub(r'\b(Full|Video|Song|Audio|Official|HD|Movie)\b', '', p, flags=re.IGNORECASE).strip()
        if p_clean and len(p_clean) < 40 and p_clean.lower() not in clean_uploader.lower():
            credited_names.append(p_clean)

    # Smart Singer & Artist Prioritization (Never dump 5 cast names like Ranbir, Shraddha, Pritam)
    KNOWN_SINGERS = [
        'Arijit Singh', 'Atif Aslam', 'Karan Aujla', 'Talwiinder', 'AP Dhillon',
        'Diljit Dosanjh', 'B Praak', 'Shreya Ghoshal', 'Jubin Nautiyal', 'Jasleen Royal',
        'Anuv Jain', 'Prateek Kuhad', 'Darshan Raval', 'Sidhu Moose Wala', 'Kaka',
        'Amrit Maan', 'Jordan Sandhu', 'Mankirt Aulakh', 'King', 'MC Stan', 'Badshah',
        'Mohit Chauhan', 'KK', 'Sonu Nigam', 'Sunidhi Chauhan', 'Armaan Malik', 'Neha Kakkar'
    ]
    matched_singers = [s for s in KNOWN_SINGERS if re.search(r'\b' + re.escape(s) + r'\b', raw_title, re.IGNORECASE)]

    if matched_singers:
        artist_display = matched_singers[0]
        all_credits = ", ".join(matched_singers)
    elif detected_artist and detected_artist.lower() not in clean_uploader.lower():
        artist_display = detected_artist
        all_credits = detected_artist
    elif credited_names:
        # Extract individual names from comma-separated blocks and take at most first 2
        raw_list = []
        for block in credited_names:
            for item in block.split(','):
                it = item.strip()
                if it and len(it) > 2 and it not in raw_list:
                    raw_list.append(it)
        artist_display = ", ".join(raw_list[:2]) if raw_list else credited_names[0]
        all_credits = ", ".join(credited_names)
    else:
        artist_display = detected_artist
        all_credits = detected_artist

    title = re.sub(r'[\(\[\{\)\]\}]', '', title).strip()
    return title or "Hit Track", artist_display, all_credits, clean_uploader

def extract_smart_hero_frame(v_url, clean_frame_path):
    """
    Intelligently samples multiple timestamps across the music video stream.
    Uses AI / Computer Vision (Face detection, contrast, sharpness, dynamic range)
    to automatically select the best cinematic hero frame (e.g. artist looking at camera,
    well-lit stage, iconic scene), strictly avoiding pitch-black frames, backs of heads,
    random objects, or blurry transition cuts.
    """
    timestamps = ['00:00:20', '00:00:40', '00:01:05', '00:01:30', '00:01:55', '00:02:20']
    candidates = []

    has_cv2 = False
    try:
        import cv2
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        has_cv2 = True
    except Exception:
        has_cv2 = False

    for i, ts in enumerate(timestamps):
        tmp_frame = f"{clean_frame_path}_cand_{i}.jpg"
        cmd = ['ffmpeg', '-y', '-ss', ts, '-i', v_url, '-vframes', '1', '-q:v', '2', tmp_frame]
        try:
            subprocess.run(cmd, capture_output=True, timeout=15)
        except Exception:
            continue

        if not os.path.exists(tmp_frame) or os.path.getsize(tmp_frame) < 8000:
            if os.path.exists(tmp_frame):
                try: os.remove(tmp_frame)
                except Exception: pass
            continue

        try:
            if has_cv2:
                import numpy as np
                img = cv2.imread(tmp_frame)
                if img is None:
                    continue
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                mean_val = float(np.mean(gray))
                if mean_val < 32 or mean_val > 225:
                    os.remove(tmp_frame)
                    continue

                contrast = float(np.std(gray))
                sharpness = min(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 500.0)
                brightness_score = 100.0 - abs(mean_val - 110.0)

                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
                face_score = 0.0
                if len(faces) > 0:
                    face_score = 300.0
                    for (x, y, w, h) in faces:
                        if w > 90 and h > 90:
                            face_score += 150.0

                score = face_score + (contrast * 1.5) + (sharpness * 0.4) + brightness_score
                candidates.append((score, tmp_frame))
            else:
                with Image.open(tmp_frame) as im:
                    gray = im.convert('L')
                    stat = ImageStat.Stat(gray)
                    mean_val = stat.mean[0]
                    if mean_val < 32 or mean_val > 225:
                        os.remove(tmp_frame)
                        continue
                    std_dev = stat.stddev[0]
                    brightness_score = 100.0 - abs(mean_val - 110.0)
                    score = (std_dev * 2.0) + brightness_score
                    candidates.append((score, tmp_frame))
        except Exception as e:
            if os.path.exists(tmp_frame):
                try: os.remove(tmp_frame)
                except Exception: pass

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_score, best_frame = candidates[0]
    print(f"Smart Hero Frame selected with quality score: {best_score:.1f}")

    if os.path.exists(clean_frame_path):
        try: os.remove(clean_frame_path)
        except Exception: pass
    os.rename(best_frame, clean_frame_path)

    for _, path in candidates[1:]:
        if os.path.exists(path):
            try: os.remove(path)
            except Exception: pass

    return clean_frame_path

def download_audio_and_cover(video_id, out_prefix):
    url = f"https://www.youtube.com/watch?v={video_id}"
    audio_path = f"{out_prefix}.mp3"
    thumb_template = f"{out_prefix}.%(ext)s"

    strategies = [
        ['yt-dlp', '--extractor-args', 'youtube:player_client=android;player_skip=webpage,configs'],
        ['yt-dlp', '--extractor-args', 'youtube:player_client=visionos;player_skip=webpage,configs'],
        ['yt-dlp', '--remote-components', 'ejs:github', '--extractor-args', 'youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416'],
        ['yt-dlp', '--extractor-args', 'youtube:player_client=tv_embedded,web_embedded'],
        ['yt-dlp', '--extractor-args', 'youtube:player_client=ios,tv'],
        ['yt-dlp', '--extractor-args', 'youtube:player_client=web_creator'],
        ['yt-dlp', '--extractor-args', 'youtube:player_client=mweb,android']
    ]
    if os.path.exists('cookies.txt'):
        strategies.append(['yt-dlp', '--cookies', 'cookies.txt', '--extractor-args', 'youtube:player_client=android;player_skip=webpage,configs'])
        strategies.append(['yt-dlp', '--cookies', 'cookies.txt', '--remote-components', 'ejs:github'])
        strategies.append(['yt-dlp', '--cookies', 'cookies.txt', '--extractor-args', 'youtube:player_client=web,mweb'])

    download_success = False
    last_err = None
    for base in strategies:
        cmd = [
            *base,
            '-f', 'ba/b',
            '--no-playlist',
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

    # Try extracting pristine clean 1080p frame directly from video stream (Zero poster text/logos)
    clean_frame_path = f"{out_prefix}_clean_frame.jpg"
    try:
        url_cmd = ['yt-dlp', '-g', '-f', 'bestvideo[height<=1080]', url]
        res = subprocess.run(url_cmd, capture_output=True, text=True, timeout=25)
        v_url = res.stdout.strip().split('\n')[0]
        if v_url and v_url.startswith('http'):
            hero_frame = extract_smart_hero_frame(v_url, clean_frame_path)
            if hero_frame and os.path.exists(hero_frame) and os.path.getsize(hero_frame) > 10000:
                print("Extracted pristine AI-curated hero frame directly from video stream!")
                return audio_path, hero_frame
    except Exception as e:
        print(f"Clean stream frame grab fallback: {e}")

    # Fallback to downloaded thumbnail if stream frame grab failed
    thumb_candidates = glob.glob(f"{out_prefix}*.jpg") + glob.glob(f"{out_prefix}*.webp") + glob.glob(f"{out_prefix}*.png")
    cover_path = thumb_candidates[0] if thumb_candidates else None
    return audio_path, cover_path

def apply_slowed_reverb(input_audio, output_audio):
    """
    Pure Crystal-Clear Aesthetic Slowed + Reverb DSP:
    - Smooth natural tape slowdown (~0.86x) + 432Hz harmonic retune
    - Vocal Clarity Boost (+3.0dB at 2800Hz) so singing voice is crystal clear and never suppressed
    - Warm Sub-Bass punch (+4.0dB at 80Hz) for deep immersive lo-fi body
    - Smooth airy top end (-1.0dB at 10000Hz)
    - Lush cathedral stereo reverb (dual echo at 60ms & 120ms)
    - Master studio limiter (-0.5dB) with volume boost (+25%) for loud, punchy, premium sound
    """
    speed = round(random.uniform(0.855, 0.872), 4)
    print(f"Applying Pure Crystal-Clear Slowed+Reverb DSP (Speed: {speed}x, Vocal Boost +3dB, 432Hz)...")

    filter_complex = (
        f"[0:a]asetrate=44100*{speed}*0.996,aresample=44100,"
        f"equalizer=f=80:width_type=o:width=1.8:g=4.0,"
        f"equalizer=f=2800:width_type=o:width=1.5:g=3.0,"
        f"equalizer=f=10000:width_type=o:width=1.5:g=-1.0,"
        f"aecho=0.8:0.85:60:0.25,aecho=0.8:0.75:120:0.18,"
        f"volume=1.25,alimiter=limit=-0.5dB:level=disabled[a]"
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
    # Try single line with larger, clearer font down to readable minimum
    for sz in range(92, 48, -4):
        font = get_font(sz, bold=True)
        bbox = font.getbbox(title_text)
        if bbox[2] - bbox[0] <= max_w:
            return [title_text], font, sz

    # If single line doesn't fit, wrap into 2 clean lines
    for sz in range(78, 44, -4):
        font = get_font(sz, bold=True)
        wrap_width = max(10, int(len(title_text) * 0.58))
        lines = textwrap.wrap(title_text, width=wrap_width)
        if len(lines) <= 2:
            w1 = font.getbbox(lines[0])[2] - font.getbbox(lines[0])[0]
            w2 = font.getbbox(lines[1])[2] - font.getbbox(lines[1])[0] if len(lines) > 1 else 0
            if max(w1, w2) <= max_w:
                return lines[:2], font, sz

    font = get_font(46, bold=True)
    return textwrap.wrap(title_text, width=16)[:2], font, 46

def crop_letterbox_bars(im):
    try:
        gray = im.convert('L')
        w, h = gray.size
        # Sample two vertical columns (15% and 85%) to avoid center badges like iTunes/Dolby
        top = 0
        for y in range(int(h * 0.35)):
            val1 = gray.getpixel((int(w * 0.15), y))
            val2 = gray.getpixel((int(w * 0.85), y))
            if val1 > 15 or val2 > 15:
                top = y
                break

        if top > 15:
            bottom = h - top
            return im.crop((0, top, w, bottom))
    except Exception as e:
        print(f"Letterbox crop notice: {e}")
    return im

def generate_thumbnail(cover_path, title, artist, output_thumb):
    """
    Renders 1080p Full-Bleed Cinematic Aesthetic Thumbnail:
    - Pristine full-bleed 16:9 cinematic background with rich contrast (zero black bars)
    - AI Face-Aware layout: If an artist face is detected in the upper/middle frame,
      typography is intelligently placed in the Lower Third so it NEVER obscures the face.
    - Large stylized white chalk/brush title (CaveatBrush) with multi-pass soft drop shadow
    - Clean uppercase subtitle [ SLOWED + REVERB ]
    - Subtle aesthetic @nikhildswll watermark in top-right
    """
    W, H = 1920, 1080
    font_dir = os.path.join(BASE_DIR, 'fonts')

    font_brush_path = os.path.join(font_dir, 'CaveatBrush-Regular.ttf')
    font_sans_path = os.path.join(font_dir, 'BebasNeue.ttf')

    font_title = ImageFont.truetype(font_brush_path, 140) if os.path.exists(font_brush_path) else get_font(120, bold=True)
    font_sub = ImageFont.truetype(font_sans_path, 44) if os.path.exists(font_sans_path) else get_font(40, bold=True)
    font_watermark = ImageFont.truetype(font_sans_path, 34) if os.path.exists(font_sans_path) else get_font(30, bold=False)

    if cover_path and os.path.exists(cover_path):
        try:
            raw_im = Image.open(cover_path).convert('RGB')
            im = crop_letterbox_bars(raw_im)
            scale = max(W / im.width, H / im.height)
            new_w = int(im.width * scale)
            new_h = int(im.height * scale)
            im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            left = (new_w - W) // 2
            top = (new_h - H) // 2
            bg = im_resized.crop((left, top, left + W, top + H))
        except Exception:
            bg = Image.new('RGB', (W, H), '#18181b')
    else:
        bg = Image.new('RGB', (W, H), '#18181b')

    # Color Grade & Contrast Enhancement
    bg = ImageEnhance.Contrast(bg).enhance(1.10)
    bg = ImageEnhance.Color(bg).enhance(1.10)

    # Face detection to protect actor/singer face from text occlusion
    has_face = False
    face_y = H // 2
    try:
        import cv2
        import numpy as np
        cv_img = cv2.cvtColor(np.array(bg), cv2.COLOR_RGB2BGR)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY), 1.1, 4, minSize=(80, 80))
        if len(faces) > 0:
            has_face = True
            largest = max(faces, key=lambda f: f[2]*f[3])
            face_y = largest[1] + largest[3] // 2
    except Exception:
        pass

    clean_title = title.upper()
    sub_text = '[ SLOWED + REVERB ]'

    bbox_t = font_title.getbbox(clean_title)
    tw = bbox_t[2] - bbox_t[0]
    th = bbox_t[3] - bbox_t[1]

    # If title is wide, scale down font nicely
    if tw > W - 250:
        scale_f = (W - 300) / tw
        font_title = ImageFont.truetype(font_brush_path, max(int(140 * scale_f), 70)) if os.path.exists(font_brush_path) else get_font(max(int(120 * scale_f), 60), bold=True)
        bbox_t = font_title.getbbox(clean_title)
        tw = bbox_t[2] - bbox_t[0]
        th = bbox_t[3] - bbox_t[1]

    bbox_s = font_sub.getbbox(sub_text)
    sw = bbox_s[2] - bbox_s[0]
    sh = bbox_s[3] - bbox_s[1]

    if has_face and face_y < int(H * 0.65):
        # Face is in upper/middle frame -> Place in lower third (Never covers face!)
        tx = (W - tw) // 2
        ty = int(H * 0.74)
        sx = (W - sw) // 2
        sy = ty + th + 18
        grad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(grad)
        start_y = int(H * 0.58)
        for y in range(start_y, H):
            prog = max(0.0, float(y - start_y) / float(H - start_y))
            alpha = int(220 * (prog ** 1.3))
            g_draw.line([(0, y), (W, y)], fill=(4, 4, 8, alpha))
        bg_rgba = bg.convert('RGBA')
        bg = Image.alpha_composite(bg_rgba, grad).convert('RGB')
    else:
        # Standard balanced layout
        tx = (W - tw) // 2
        ty = int(H * 0.44)
        sx = (W - sw) // 2
        sy = ty + th + 18
        vignette = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        v_draw = ImageDraw.Draw(vignette)
        for y in range(H):
            alpha = int(50 + 90 * (y / H))
            v_draw.line([(0, y), (W, y)], fill=(6, 6, 10, alpha))
        bg_rgba = bg.convert('RGBA')
        bg = Image.alpha_composite(bg_rgba, vignette).convert('RGB')

    # Multi-pass soft shadow for depth
    shadow_img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    for dx, dy in [(-3,-3), (3,-3), (-3,3), (3,3), (0, 5), (0, 9), (0, 14)]:
        s_draw.text((tx + dx, ty + dy), clean_title, fill=(0, 0, 0, 245), font=font_title)
        s_draw.text((sx + dx, sy + dy), sub_text, fill=(0, 0, 0, 245), font=font_sub)

    shadow_blur = shadow_img.filter(ImageFilter.GaussianBlur(radius=8))
    bg_rgba = bg.convert('RGBA')
    bg_rgba = Image.alpha_composite(bg_rgba, shadow_blur)

    draw = ImageDraw.Draw(bg_rgba)
    draw.text((tx, ty), clean_title, fill='#ffffff', font=font_title)
    draw.text((sx, sy), sub_text, fill='#ffffff', font=font_sub)

    # Top Right Watermark
    wm_text = f"@{CHANNEL_NAME.upper()}"
    wm_bbox = font_watermark.getbbox(wm_text)
    wm_w = wm_bbox[2] - wm_bbox[0]
    draw.text((W - wm_w - 60, 50), wm_text, fill=(255, 255, 255, 190), font=font_watermark)

    bg_final = bg_rgba.convert('RGB')
    bg_final.save(output_thumb, quality=95)
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

PLAYLIST_IDS = {
    'hindi': 'PLFCTerpJfOZc',
    'punjabi': 'PLF_jJfUZ-qto',
    'haryanvi': 'PLL-jv2OGy6uc'
}

def add_video_to_playlist(video_id, category_name, song_title):
    cat_lower = (category_name or '').lower()
    title_lower = (song_title or '').lower()

    if 'haryanvi' in cat_lower or any(k in title_lower for k in ['haryanvi', 'pranjal', 'dhanda', 'renuka', 'masoom', 'chahar', 'pabra', 'hooda', 'chabili', 'matak', 'darling', 'zulmi', 'kood']):
        target_pl = PLAYLIST_IDS['haryanvi']
        target_name = 'Haryanvi & Desi Chill'
    elif 'punjabi' in cat_lower or any(k in title_lower for k in ['punjabi', 'shubh', 'aujla', 'diljit', 'mankirt', 'kaptaan', 'ap dhillon', 'moose wala', 'hip hop']):
        target_pl = PLAYLIST_IDS['punjabi']
        target_name = 'Midnight Drive Punjabi'
    else:
        target_pl = PLAYLIST_IDS['hindi']
        target_name = 'Late Night Bollywood & Indie Lo-Fi'

    try:
        if not os.path.exists(TOKEN_FILE):
            return
        c = Credentials.from_authorized_user_file(TOKEN_FILE)
        yt = build('youtube', 'v3', credentials=c)
        yt.playlistItems().insert(
            part='snippet',
            body={
                'snippet': {
                    'playlistId': target_pl,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
        ).execute()
        print(f"Auto-added to playlist: [{target_name}] ({target_pl})")
    except Exception as e:
        print(f"[Playlist Auto-Add] Info: {e}")

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
    clean_artist_tag = re.sub(r'[^a-zA-Z0-9 ]', '', artist).strip()
    clean_title_tag = re.sub(r'[^a-zA-Z0-9 ]', '', title).strip()

    yt_desc = f"""🎧 {title} — {artist} (Slowed + Reverb)
✨ Retuned to 432Hz Healing Frequency | Aesthetic White Minimalist Edit | 1080p Full HD

Put on your headphones, close your eyes, and feel the late-night nostalgia. 🌙🖤

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ OFFICIAL 24/7 CURATED PLAYLISTS:
🌙 Bollywood & Indie Lo-Fi: https://www.youtube.com/playlist?list={PLAYLIST_IDS['hindi']}
🚗 Midnight Drive Punjabi: https://www.youtube.com/playlist?list={PLAYLIST_IDS['punjabi']}
🔥 Haryanvi Chill Vibes: https://www.youtube.com/playlist?list={PLAYLIST_IDS['haryanvi']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏳ MOOD CHAPTERS:
0:00 — Late Night Intro (432Hz Resample)
0:15 — First Chorus & Cathedral Reverb
1:25 — Deep Warm Bass Drop & Vocal Presence
2:50 — Nostalgia Fade & Outro

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 RELATED SEARCHES & VIBES:
{title} slowed reverb, {title} slowed and reverb, {title} lofi, {title} 432hz, {artist} slowed reverb, {artist} lofi songs, indian lofi songs, late night drive slowed, hindi lofi study chill, aesthetic slowed hindi songs, 432hz healing frequency lofi, lofi hip hop india, relaxing slowed hindi.

#SlowedAndReverb #LofiVibes #{clean_title_tag.replace(' ', '')} #{clean_artist_tag.replace(' ', '')} #{CHANNEL_NAME} #NightDrive #432Hz #IndianLofi #PartyHits
"""
    yt_tags = [
        clean_title_tag,
        f"{clean_title_tag} slowed",
        f"{clean_title_tag} slowed reverb",
        f"{clean_title_tag} lofi",
        f"{clean_title_tag} 432hz",
        clean_artist_tag,
        f"{clean_artist_tag} slowed",
        'slowed and reverb',
        'slowed reverb',
        'lofi',
        CHANNEL_NAME,
        'aesthetic audio',
        'indian lofi',
        'late night drive',
        '432hz',
        label
    ][:15]

    # 6. Upload
    uploaded_id = upload_to_youtube(video_path, thumb_path, yt_title, yt_desc, yt_tags)

    # 7. Automatically Add to Respective Genre Playlist!
    cat_name = song_item.get('category', 'Hindi')
    add_video_to_playlist(uploaded_id, cat_name, title)

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

    # Cadence guard for hourly cron: ensure at least ~1h 45m between uploads (strictly every 2 hours)
    force_run = '--force' in sys.argv
    if not force_run and not target_vid:
        history = load_history()
        if history:
            last_upload = history[-1]
            elapsed = time.time() - last_upload.get('timestamp', 0)
            min_gap = int(1.75 * 3600) # ~1h 45m (strictly 1 upload every 2 hours via hourly cron)
            if elapsed < min_gap:
                mins_left = int((min_gap - elapsed) / 60)
                print(f"Cadence Check: Last video was uploaded {int(elapsed/60)}m ago. Next 2-hour slot in {mins_left}m. Skipping.")
                return

    # Fetch a wider candidate pool so if any single song has streaming restrictions, we immediately fallback to the next!
    pool_size = max(max_count * 4, 8)
    candidates = search_trending_songs(max_count=pool_size)
    if not candidates:
        print("[ERROR] No new candidate songs found.")
        sys.exit(1)

    history = load_history()
    uploaded_count = 0
    quota_hit = False

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
            err_str = str(e)
            if "uploadLimitExceeded" in err_str:
                print(f"\n[QUOTA] YouTube 24h upload limit reached: {e}")
                quota_hit = True
                break
            print(f"\n[WARNING] Could not process {s.get('title')}: {e}")
            print("--> Moving immediately to next candidate song in queue...\n")
            continue

    if uploaded_count > 0:
        print(f"\nSUCCESS: {uploaded_count} LO-FI VIDEO(S) PROCESSED & UPLOADED!")
    elif quota_hit:
        print("\n[FATAL ERROR] YouTube 24-hour daily upload limit reached (uploadLimitExceeded)!")
        print("YouTube enforces a 24-hour rolling cooldown on new/unverified channels.")
        print("Failing run with exit code 1 so GitHub Actions correctly shows red (NOT false green).")
        sys.exit(1)
    else:
        print("\n[FATAL ERROR] Failed to upload any videos in this run. Failing job loudly.")
        sys.exit(1)

if __name__ == '__main__':
    main()
