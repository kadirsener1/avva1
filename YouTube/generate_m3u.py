import re
import yt_dlp

# Kanal listesini oku
try:
    with open("YouTube/channels.txt", "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("Hata: YouTube/channels.txt dosyası bulunamadı!")
    raw_lines = []

def extract_video_id(url_or_id):
    url_or_id = url_or_id.strip()
    if 'youtu.be/' in url_or_id or 'youtube.com' in url_or_id or 'm.youtube.com' in url_or_id:
        return url_or_id, "url"
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return f"https://www.youtube.com/watch?v={url_or_id}", "url"
    if url_or_id.startswith("UC") and len(url_or_id) == 24:
        return f"https://m.youtube.com/channel/{url_or_id}/live", "url"
    return url_or_id, "url"

def get_video_and_stream_info(target_url):
    ydl_opts = {
        'format': 'best',
        'geturl': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            title = info.get('title', 'YouTube Stream')
            thumbnail = info.get('thumbnail', '')
            stream_url = info.get('url')
            
            if not stream_url and 'entries' in info and len(info['entries']) > 0:
                entry = info['entries'][0]
                stream_url = entry.get('url')
                title = entry.get('title', title)
                thumbnail = entry.get('thumbnail', thumbnail)

            return title, thumbnail, stream_url
    except Exception as e:
        print(f"yt-dlp hata detayı: {e}")
        return None, None, None

playlist_lines = ["#EXTM3U"]
success = 0

for line in raw_lines:
    if ',' in line:
        name_part, url_part = line.split(',', 1)
        custom_name = name_part.strip()
        target_input = url_part.strip()
    else:
        target_input = line
        custom_name = None

    target_url, _ = extract_video_id(target_input)
    print(f"\nİşleniyor: {target_url}")

    title, logo, stream_url = get_video_and_stream_info(target_url)

    if stream_url:
        name = custom_name or title
        playlist_lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="YouTube",{name}')
        playlist_lines.append(stream_url)
        success += 1
        print(f"✅ {name} → Başarılı!")
    else:
        print(f"⚠️ {target_url} → Akış adresi alınamadı (Yayın kapalı veya erişilemiyor).")

# Dosyayı kaydet
with open("YouTube/playlist.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(playlist_lines))

print(f"\n🎯 Toplam {len(raw_lines)} kanaldan {success} tanesi eklendi, playlist.m3u güncellendi.")
