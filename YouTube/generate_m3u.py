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

playlist_lines = ["#EXTM3U"]
success = 0

for line in raw_lines:
    # Virgülle ayrılmışsa: isim, ID/URL; değilse tüm satırı ID/URL olarak al
    if ',' in line:
        name_part, channel_part = line.split(',', 1)
        name = name_part.strip()
        channel = channel_part.strip()
    else:
        channel = line
        name = None  # sonra YouTube'dan al

    # Kanal ID'sini ayıkla
    channel_id = channel.rstrip('/').split('/')[-1]

    # Eğer isim verilmediyse YouTube'dan çek
    logo = ""
    if name is None:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/channel/{channel_id}&format=json"
        try:
            oembed_resp = requests.get(oembed_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if oembed_resp.status_code == 200:
                data = oembed_resp.json()
                name = data.get("title") or channel_id
                logo = data.get("thumbnail_url") or ""
            else:
                name = channel_id
        except:
            name = channel_id
    else:
        # İsim verilmişse logoyu yine YouTube'dan alalım (opsiyonel)
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/channel/{channel_id}&format=json"
        try:
            oembed_resp = requests.get(oembed_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if oembed_resp.status_code == 200:
                data = oembed_resp.json()
                logo = data.get("thumbnail_url") or ""
        except:
            pass

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
        if url_match:
            manifest_url = url_match.group(0)
            playlist_lines.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="YouTube",{name}')
            playlist_lines.append(manifest_url)
            success += 1
            print(f"✅ {name} ({channel_id}) → başarılı")
        else:
            print(f"⚠️ {name} ({channel_id}) → canlı yayın bulunamadı")
    except Exception as e:
        print(f"❌ {name} ({channel_id}) → hata: {e}")

# Dosyaya yaz
with open("YouTube/playlist.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(playlist_lines))

print(f"\n🎯 Toplam {len(raw_lines)} kanaldan {success} tanesi canlı, playlist.m3u oluşturuldu.")
