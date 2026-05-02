import re
import json
from datetime import datetime
from playwright.sync_api import sync_playwright

# Kanal isim mapping (istediğin kadar genişletebilirsin)
CHANNEL_MAPPING = {
    "ssport1": "S Sport 1 HD",
    "ssport2": "S Sport 2 HD",
    "bein1": "beIN Sports 1 HD",
    "bein2": "beIN Sports 2 HD",
    "bein3": "beIN Sports 3 HD",
    "bein4": "beIN Sports 4 HD",
    "smartsp1": "Smart Spor 1 HD",
    "smartsp2": "Smart Spor 2 HD",
    "trtspor": "TRT Spor",
    "a_spor": "A Spor HD",
    "spor32": "Spor 32",
    "mhrs": "MHR Spor",
    # istediğin kadar ekle...
}

def get_channel_name(url):
    match = re.search(r'avvaupdate\.com/([^/]+)/', url)
    if match:
        key = match.group(1).lower()
        return CHANNEL_MAPPING.get(key, key.upper().replace("_", " "))
    return "Bilinmeyen Kanal"


def scrape_avva():
    print(f"[{datetime.now()}] Scraping başlıyor...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Cloudflare ve anti-bot koruması için
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        page.goto("https://avvasportshd1.com/channels.html", wait_until="networkidle", timeout=45000)
        
        # Sayfadaki tüm m3u8 linklerini yakala
        content = page.content()
        browser.close()

    # Regex ile tüm m3u8 linklerini bul
    m3u8_links = re.findall(r'https?://[^"\']+\.m3u8[^"\']*', content)
    m3u8_links = list(dict.fromkeys(m3u8_links))  # duplicate temizle

    channels = []
    for link in m3u8_links:
        name = get_channel_name(link)
        channels.append({
            "name": name,
            "url": link,
            "updated_at": datetime.now().isoformat()
        })

    # JSON kaydet
    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

    # M3U Playlist oluştur
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"#Playlist Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for ch in channels:
            f.write(f'#EXTINF:-1 tvg-id="" group-title="Avva Sports",{ch["name"]}\n')
            f.write(f'{ch["url"]}\n\n')

    print(f"✅ Başarıyla {len(channels)} kanal bulundu ve kaydedildi.")
    return channels


if __name__ == "__main__":
    scrape_avva()
