import json
import requests
from datetime import datetime

API_URL = "https://avvasportshd1.com/api/channels"
BASE_URL = "https://avvasportshd1.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://avvasportshd1.com/channels.html",
    "Accept": "application/json"
}

def scrape():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    print(f"🚀 [{now}] API sorgulanıyor...")

    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        channels = response.json()
    except Exception as e:
        print(f"❌ API hatası: {e}")
        return

    if not channels:
        print("❌ API boş döndü.")
        return

    print(f"📡 {len(channels)} kanal bulundu.\n")

    # M3U Playlist oluştur
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Avva Sports HD Playlist\n")
        f.write(f"# Son Güncelleme: {now}\n")
        f.write(f"# Toplam Kanal: {len(channels)}\n\n")

        for ch in channels:
            ch_id = ch.get("id", "")
            name = ch.get("name", "Bilinmeyen")
            m3u8 = ch.get("m3u8_url", "")
            logo = ch.get("logo_url", "")

            if not m3u8:
                print(f"⚠️ {name} - m3u8 linki yok, atlandı.")
                continue

            # Logo URL'sini tam yap
            if logo and not logo.startswith("http"):
                logo = BASE_URL + logo

            f.write(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}" group-title="Avva Sports",{name}\n')
            f.write(f'{m3u8}\n\n')

            print(f"✅ {name}")

    # JSON olarak da kaydet
    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": now,
            "total": len(channels),
            "channels": channels
        }, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 Tamamlandı! {len(channels)} kanal playlist.m3u dosyasına yazıldı.")

if __name__ == "__main__":
    scrape()
