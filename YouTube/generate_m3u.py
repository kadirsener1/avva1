import os
import re
import requests

CHANNELS_FILE = "YouTube/channels.txt"
PLAYLIST_FILE = "playlist.m3u"   # Kök dizindeki dosya güncellenecek
APPEND_IF_NOT_FOUND = False      # Listede yoksa ekleme, sadece mevcut linki güncelle


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().casefold()


def load_playlist(path: str):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]
    else:
        lines = ["#EXTM3U"]

    if not lines:
        lines = ["#EXTM3U"]
    elif not lines[0].startswith("#EXTM3U"):
        lines.insert(0, "#EXTM3U")

    return lines


def build_name_index(lines):
    """
    playlist.m3u içindeki kanal adını bulur ve
    ilgili URL satırının index'ini döner.
    Sadece URL satırı değiştirilecek.
    """
    index = {}

    for i, line in enumerate(lines):
        if not line.startswith("#EXTINF"):
            continue

        parts = line.split(",", 1)
        if len(parts) != 2:
            continue

        channel_name = parts[1].strip()
        if not channel_name:
            continue

        url_idx = None
        for j in range(i + 1, len(lines)):
            candidate = lines[j].strip()

            if not candidate:
                continue
            if candidate.startswith("#"):
                continue

            url_idx = j
            break

        if url_idx is not None:
            index[normalize_name(channel_name)] = url_idx

    return index


def to_youtube_url(channel: str) -> str:
    channel = channel.strip()

    if channel.startswith("http://") or channel.startswith("https://"):
        return channel.rstrip("/")

    if channel.startswith("@"):
        return f"https://www.youtube.com/{channel}"

    return f"https://www.youtube.com/channel/{channel}"


def to_mobile_live_url(channel: str) -> str:
    url = to_youtube_url(channel)

    url = re.sub(r"^https?://(www\.)?youtube\.com", "https://m.youtube.com", url)
    url = re.sub(r"^https?://youtu\.be", "https://m.youtube.com", url)

    if not url.endswith("/live"):
        url += "/live"

    return url


def get_channel_name(channel: str, fallback_name=None):
    """
    İsmi channels.txt içinde yoksa YouTube oEmbed üzerinden almaya çalışır.
    Mevcut playlist'teki isimlere dokunulmaz, bu sadece eşleştirme içindir.
    """
    if fallback_name:
        return fallback_name.strip()

    youtube_url = to_youtube_url(channel)
    oembed_url = f"https://www.youtube.com/oembed?url={requests.utils.quote(youtube_url, safe=':/?=&')}&format=json"

    try:
        resp = requests.get(
            oembed_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return (data.get("title") or "").strip() or channel.rstrip("/").split("/")[-1]
    except Exception:
        pass

    return channel.rstrip("/").split("/")[-1]


# Kanal listesini oku
with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
    raw_lines = [line.strip() for line in f if line.strip()]

# Mevcut playlist'i yükle
playlist_lines = load_playlist(PLAYLIST_FILE)
name_index = build_name_index(playlist_lines)

# ytdlp.online üzerinden session al
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0 Safari/537.36"
}

session_cookie = None
try:
    sess = requests.Session()
    sess.headers.update(headers)

    home_resp = sess.get("https://ytdlp.online/tr/", timeout=20)

    session_cookie = sess.cookies.get("session") or home_resp.cookies.get("session")
    if not session_cookie:
        set_cookie = home_resp.headers.get("set-cookie", "")
        match = re.search(r"session=([^;]+)", set_cookie)
        if match:
            session_cookie = match.group(1)

except Exception as e:
    print(f"Session alınamadı: {e}")
    exit(1)

if not session_cookie:
    print("Session bulunamadı, çıkılıyor.")
    exit(1)

updated = 0
skipped = 0
not_live = 0
errors = 0

for line in raw_lines:
    # Format:
    # Kanal Adı, kanal_url_veya_id
    # veya sadece kanal_url_veya_id
    if "," in line:
        name_part, channel_part = line.split(",", 1)
        given_name = name_part.strip()
        channel = channel_part.strip()
    else:
        given_name = None
        channel = line.strip()

    match_name = get_channel_name(channel, given_name)
    match_key = normalize_name(match_name)

    live_url = to_mobile_live_url(channel)
    command = f"--get-url {live_url}"
    api_url = "https://ytdlp.online/api/v1/stream?command=" + requests.utils.quote(command)

    stream_headers = {
        "accept": "text/event-stream",
        "cookie": f"session={session_cookie}",
        "referer": "https://ytdlp.online/tr/",
        "user-agent": headers["user-agent"]
    }

    try:
        stream_resp = requests.get(api_url, headers=stream_headers, timeout=30)
        text = stream_resp.text

        url_match = re.search(r'https://manifest\.googlevideo\.com/[^\s"\'<>]+', text)
        if not url_match:
            not_live += 1
            print(f"⚠️ {match_name} → canlı yayın bulunamadı, mevcut kayıt korunuyor")
            continue

        manifest_url = url_match.group(0)

        if match_key in name_index:
            url_idx = name_index[match_key]
            old_url = playlist_lines[url_idx]
            playlist_lines[url_idx] = manifest_url
            updated += 1

            if old_url != manifest_url:
                print(f"✅ {match_name} → link güncellendi")
            else:
                print(f"✅ {match_name} → link zaten güncel")
        else:
            if APPEND_IF_NOT_FOUND:
                skipped += 1
            else:
                skipped += 1
            print(f"⏭️ {match_name} → playlist.m3u içinde bulunamadı, dokunulmadı")

    except Exception as e:
        errors += 1
        print(f"❌ {match_name} → hata: {e}")

# Dosyayı kök dizine yaz
with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(playlist_lines) + "\n")

print(
    f"\n🎯 Güncellenen: {updated} | "
    f"Listede bulunamadı: {skipped} | "
    f"Canlı değil: {not_live} | "
    f"Hata: {errors} | "
    f"Dosya: {PLAYLIST_FILE}"
)
