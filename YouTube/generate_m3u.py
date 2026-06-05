import os
import re
import requests

CHANNELS_FILE = "YouTube/channels.txt"
PLAYLIST_FILE = "playlist.m3u"   # Artık repo kökü
APPEND_IF_NOT_FOUND = False      # Listede yoksa ekleme, sadece mevcut linki güncelle

# Kanal listesini oku
with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
    raw_lines = [line.strip() for line in f if line.strip()]

def load_playlist(path):
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
    playlist.m3u içindeki kanal adını bulup,
    karşısındaki URL satırının index'ini çıkarır.
    Sadece URL satırı güncellenecek.
    """
    index = {}

    for i, line in enumerate(lines):
        if not line.startswith("#EXTINF"):
            continue

        _, sep, channel_name = line.partition(",")
        if not sep:
            continue

        channel_name = channel_name.strip()
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
            index[channel_name] = url_idx

    return index

def get_channel_meta(channel_id, fallback_name=None):
    """
    Eğer channels.txt içinde isim yoksa YouTube'dan kanal adını alır.
    Logo sadece gerektiğinde kullanılmak için alınır ama mevcut playlist'te değiştirilmez.
    """
    name = fallback_name
    logo = ""

    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/channel/{channel_id}&format=json"
    try:
        resp = requests.get(oembed_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if not name:
                name = data.get("title") or channel_id
            logo = data.get("thumbnail_url") or ""
    except:
        pass

    if not name:
        name = channel_id

    return name, logo

playlist_lines = load_playlist(PLAYLIST_FILE)
name_index = build_name_index(playlist_lines)

# ytdlp.online üzerinden session al
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0 Safari/537.36"
}

session = None
try:
    home_resp = requests.get("https://ytdlp.online/tr/", headers=headers, timeout=20)
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

updated = 0
skipped = 0

for line in raw_lines:
    # channels.txt:
    # Kanal Adı, kanal_url
    # veya sadece kanal_url
    if "," in line:
        name_part, channel_part = line.split(",", 1)
        lookup_name = name_part.strip()
        channel = channel_part.strip()
    else:
        lookup_name = None
        channel = line

    # Kanal ID'sini ayıkla
    channel_id = channel.rstrip("/").split("/")[-1]

    # İsim lazımsa çöz
    resolved_name, logo = get_channel_meta(channel_id, lookup_name)
    match_name = lookup_name or resolved_name

    # m3u8 manifest linkini al
    command = f"--get-url https://m.youtube.com/channel/{channel_id}/live"
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
        if not url_match:
            print(f"⚠️ {match_name} ({channel_id}) → canlı yayın bulunamadı, mevcut kayıt korunuyor")
            continue

        manifest_url = url_match.group(0)

        # Sadece mevcut listedeki kanalın URL satırını güncelle
        if match_name in name_index:
            url_idx = name_index[match_name]
            old_url = playlist_lines[url_idx]
            playlist_lines[url_idx] = manifest_url
            updated += 1

            if old_url != manifest_url:
                print(f"✅ {match_name} ({channel_id}) → link güncellendi")
            else:
                print(f"✅ {match_name} ({channel_id}) → link zaten güncel")
        else:
            if APPEND_IF_NOT_FOUND:
                # İstenirse açılabilir ama şu an kullanıcı isteğine göre kapalı
                playlist_lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="YouTube",{match_name}')
                playlist_lines.append(manifest_url)
                name_index[match_name] = len(playlist_lines) - 1
                updated += 1
                print(f"➕ {match_name} ({channel_id}) → listede yoktu, eklendi")
            else:
                skipped += 1
                print(f"⏭️ {match_name} ({channel_id}) → playlist.m3u içinde bulunamadı, dokunulmadı")

    except Exception as e:
        print(f"❌ {match_name} ({channel_id}) → hata: {e}")

# Kök dizine yaz
with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(playlist_lines) + "\n")

print(f"\n🎯 {updated} kanal güncellendi, {skipped} kanal listede olmadığı için atlandı. Dosya: {PLAYLIST_FILE}")
