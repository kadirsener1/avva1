import re
import requests

# Kanal listesini oku
with open("YouTube/channels.txt", "r", encoding="utf-8") as f:
    raw_lines = [line.strip() for line in f if line.strip()]

# ytdlp.online üzerinden session al
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0 Safari/537.36"
}
session = None
try:
    home_resp = requests.get("https://ytdlp.online/tr/", headers=headers)
    set_cookie = home_resp.headers.get("set-cookie", "")
    match = re.search(r"session=([^;]+)", set_cookie)
    if match:
        session = match.group(1)
except Exception as e:
    print(f"Session alınamadı: {e}")
    exit(1)

if not session:
    print("Session bulunamadı, çıkılıyor.")
    exit(1)


def extract_video_id(url_or_id):
    """
    Farklı YouTube URL formatlarından video ID'sini çıkarır.
    
    Desteklenen formatlar:
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID
    - https://www.youtube.com/live/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    - Direkt VIDEO_ID
    """
    url_or_id = url_or_id.strip()
    
    # youtu.be kısa link formatı
    match = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url_or_id)
    if match:
        return match.group(1), "video"
    
    # youtube.com/watch?v= formatı
    match = re.search(r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})', url_or_id)
    if match:
        return match.group(1), "video"
    
    # youtube.com/live/ formatı
    match = re.search(r'youtube\.com/live/([a-zA-Z0-9_-]{11})', url_or_id)
    if match:
        return match.group(1), "video"
    
    # youtube.com/channel/ formatı (kanal ID)
    match = re.search(r'youtube\.com/channel/([a-zA-Z0-9_-]+)', url_or_id)
    if match:
        return match.group(1), "channel"
    
    # youtube.com/@username formatı
    match = re.search(r'youtube\.com/@([a-zA-Z0-9_-]+)', url_or_id)
    if match:
        return match.group(1), "handle"
    
    # Direkt video ID (11 karakter)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id, "video"
    
    # Direkt kanal ID (UC ile başlayan)
    if url_or_id.startswith("UC") and len(url_or_id) == 24:
        return url_or_id, "channel"
    
    # Bilinmeyen format - olduğu gibi döndür
    return url_or_id, "unknown"


def get_video_info(video_id):
    """Video bilgilerini YouTube oEmbed API'den al"""
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        resp = requests.get(oembed_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "title": data.get("title", video_id),
                "logo": data.get("thumbnail_url", "")
            }
    except:
        pass
    return {"title": video_id, "logo": ""}


def get_channel_info(channel_id):
    """Kanal bilgilerini YouTube oEmbed API'den al"""
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/channel/{channel_id}&format=json"
    try:
        resp = requests.get(oembed_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "title": data.get("title", channel_id),
                "logo": data.get("thumbnail_url", "")
            }
    except:
        pass
    return {"title": channel_id, "logo": ""}


playlist_lines = ["#EXTM3U"]
success = 0

for line in raw_lines:
    # Virgülle ayrılmışsa: isim, URL; değilse tüm satırı URL olarak al
    if ',' in line:
        name_part, url_part = line.split(',', 1)
        custom_name = name_part.strip()
        url_or_id = url_part.strip()
    else:
        url_or_id = line
        custom_name = None

    # Video/Kanal ID'sini ve tipini çıkar
    extracted_id, id_type = extract_video_id(url_or_id)
    
    # Bilgileri al
    logo = ""
    if id_type == "video":
        info = get_video_info(extracted_id)
        name = custom_name or info["title"]
        logo = info["logo"]
        # Video için API komutu
        command = f"--get-url https://www.youtube.com/watch?v={extracted_id}"
    elif id_type == "channel":
        info = get_channel_info(extracted_id)
        name = custom_name or info["title"]
        logo = info["logo"]
        # Kanal canlı yayını için API komutu
        command = f"--get-url https://m.youtube.com/channel/{extracted_id}/live"
    elif id_type == "handle":
        # Handle için direkt URL kullan
        name = custom_name or extracted_id
        command = f"--get-url https://www.youtube.com/@{extracted_id}/live"
    else:
        # Bilinmeyen format - kanal olarak dene
        info = get_channel_info(extracted_id)
        name = custom_name or info["title"]
        logo = info["logo"]
        command = f"--get-url https://m.youtube.com/channel/{extracted_id}/live"

    # m3u8 manifest linkini al
    api_url = "https://ytdlp.online/api/v1/stream?command=" + requests.utils.quote(command)

    stream_headers = {
        "accept": "text/event-stream",
        "cookie": f"session={session}",
        "referer": "https://ytdlp.online/tr/",
        "user-agent": headers["user-agent"]
    }

    try:
        stream_resp = requests.get(api_url, headers=stream_headers, timeout=30)
        text = stream_resp.text

        url_match = re.search(r'https://manifest\.googlevideo\.com/[^\s"\'<>]+', text)
        if url_match:
            manifest_url = url_match.group(0)
            playlist_lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="YouTube",{name}')
            playlist_lines.append(manifest_url)
            success += 1
            print(f"✅ {name} ({extracted_id}) → başarılı")
        else:
            print(f"⚠️ {name} ({extracted_id}) → canlı yayın bulunamadı")
    except Exception as e:
        print(f"❌ {name} ({extracted_id}) → hata: {e}")

# Dosyaya yaz
with open("YouTube/playlist.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(playlist_lines))

print(f"\n🎯 Toplam {len(raw_lines)} kanaldan {success} tanesi canlı, playlist.m3u oluşturuldu.")
