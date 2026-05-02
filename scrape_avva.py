import json
import time
import requests
from datetime import datetime

API_URL = "https://avvasportshd1.com/api/channels"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://avvasportshd1.com/channels.html",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://avvasportshd1.com"
}

def scrape():
    print(f"🚀 [{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] API sorgulanıyor...")

    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ API hatası: {e}")
        return

    # API cevabının yapısını kontrol et
    # Genelde şu formatlardan biri olur:
    # 1) Direkt liste: [{...}, {...}]
    # 2) Obje içinde: {"channels": [{...}, {...}]}
    # 3) Obje içinde: {"data": [{...}, {...}]}

    channels = []

    if isinstance(data, list):
        channels = data
    elif isinstance(data, dict):
        # Olası anahtarları dene
        for key in ["channels", "data", "items", "list", "result"]:
            if key in data and isinstance(data[key], list):
                channels = data[key]
                break
        if not channels:
            # İlk bulunan listeyi al
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    channels = value
                    break

    if not channels:
        print("❌ API'den kanal verisi alınamadı.")
        print(f"📦 API Cevabı:\n{json.dumps(data, indent=2, ensure_ascii=False)[:2000]}")
        return

    print(f"📡 {len(channels)} kanal bulundu. İşleniyor...\n")

    # Debug: İlk kanalın yapısını göster
    print("🔍 Örnek kanal verisi:")
    print(json.dumps(channels[0], indent=2, ensure_ascii=False))
    print()

    # Kanal bilgilerini işle
    processed = []
    for ch in channels:
        # Olası alan isimleri
        name = (
            ch.get("name") or
            ch.get("channel_name") or
            ch.get("title") or
            ch.get("ch_name") or
            ch.get("label") or
            "Bilinmeyen"
        )

        url = (
            ch.get("url") or
            ch.get("stream_url") or
            ch.get("stream") or
            ch.get("link") or
            ch.get("src") or
            ch.get("source") or
            ch.get("m3u8") or
            ch.get("playlist") or
            ""
        )

        logo = (
            ch.get("logo") or
            ch.get("image") or
            ch.get("icon") or
            ch.get("thumbnail") or
            ch.get("img") or
            ""
        )

        group = (
            ch.get("group") or
            ch.get("category") or
            ch.get("genre") or
            "Avva Sports"
        )

        ch_id = (
            ch.get("id") or
            ch.get("channel_id") or
            ch.get("data-id") or
            ""
        )

        if url:
            processed.append({
                "id": ch_id,
                "name": name.strip(),
                "url": url.strip(),
                "logo": logo.strip() if logo else "",
                "group": group.strip() if isinstance(group, str) else "Avva Sports"
            })
        else:
            print(f"⚠️ '{name}' kanalında URL bulunamadı, atlanıyor.")

    if not processed:
        print("❌ Hiçbir kanalda geçerli URL bulunamadı.")
        print("\n📦 Tüm API verisi debug için kaydediliyor...")
        with open("api_debug.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("💾 api_debug.json dosyasına kaydedildi.")
        print("Bu dosyayı buraya yapıştır, sana uygun kodu yazayım.")
        return

    # M3U Playlist oluştur
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Avva Sports Playlist\n")
        f.write(f"# Son Güncelleme: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write(f"# Toplam Kanal: {len(processed)}\n\n")

        for ch in processed:
            logo_tag = f' tvg-logo="{ch["logo"]}"' if ch["logo"] else ""
            f.write(f'#EXTINF:-1 tvg-id="{ch["id"]}"{logo_tag} group-title="{ch["group"]}",{ch["name"]}\n')
            f.write(f'{ch["url"]}\n\n')

    # JSON olarak da kaydet
    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "total": len(processed),
            "channels": processed
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ Tamamlandı!")
    print(f"📺 {len(processed)} kanal playlist.m3u dosyasına yazıldı.")
    print(f"📋 channels.json dosyasına kaydedildi.")


if __name__ == "__main__":
    scrape()
