import re
import json
import requests
from datetime import datetime

API_URL = "https://avvasportshd1.com/api/channels"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://avvasportshd1.com/channels.html",
    "Accept": "application/json"
}

M3U_FILE = "playlist.m3u"


def get_fresh_links():
    """API'den güncel m3u8 linklerini çek"""
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        channels = response.json()
    except Exception as e:
        print(f"❌ API hatası: {e}")
        return None

    # Kanal adı -> güncel link eşleştirmesi
    # Hem tam isim hem de URL'deki slug ile eşleştir
    link_map = {}
    for ch in channels:
        name = ch.get("name", "").strip().upper()
        url = ch.get("m3u8_url", "")
        if name and url:
            link_map[name] = url

            # URL'den slug çıkar (örn: avvaupdate.com/ssport1/index.m3u8 -> ssport1)
            slug_match = re.search(r'avvaupdate\.com/([^/]+)/', url)
            if slug_match:
                link_map[slug_match.group(1).lower()] = url

    return link_map


def update_playlist(link_map):
    """Mevcut playlist.m3u dosyasındaki sadece linkleri güncelle"""
    try:
        with open(M3U_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ {M3U_FILE} dosyası bulunamadı!")
        print("Önce playlist.m3u dosyasını elle oluştur.")
        return False

    new_lines = []
    updated = 0
    current_channel_name = ""

    for i, line in enumerate(lines):
        stripped = line.strip()

        # #EXTINF satırından kanal adını al
        if stripped.startswith("#EXTINF"):
            # Son virgülden sonrası kanal adı
            comma_pos = stripped.rfind(",")
            if comma_pos != -1:
                current_channel_name = stripped[comma_pos + 1:].strip().upper()
            new_lines.append(line)

        # m3u8 link satırı - bunu güncelle
        elif "avvaupdate.com" in stripped and ".m3u8" in stripped:
            # Eski linkten slug çıkar
            slug_match = re.search(r'avvaupdate\.com/([^/]+)/', stripped)
            old_slug = slug_match.group(1).lower() if slug_match else ""

            # Önce slug ile eşleştir, bulamazsa isimle dene
            new_url = link_map.get(old_slug) or link_map.get(current_channel_name)

            if new_url:
                new_lines.append(new_url + "\n")
                updated += 1
                print(f"✅ Güncellendi: {current_channel_name}")
            else:
                # Eşleşme bulunamazsa eski linki koru
                new_lines.append(line)
                print(f"⚠️ Eşleşme yok, eski link korundu: {current_channel_name}")

        # Güncelleme tarih satırını güncelle
        elif stripped.startswith("# Son Güncelleme:") or stripped.startswith("# Last Updated:"):
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
            new_lines.append(f"# Son Güncelleme: {now}\n")

        # Diğer tüm satırlar aynen kalsın
        else:
            new_lines.append(line)

    # Dosyayı yaz
    with open(M3U_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return updated


def main():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    print(f"🚀 [{now}] Linkler güncelleniyor...\n")

    # 1. API'den güncel linkleri al
    link_map = get_fresh_links()
    if not link_map:
        return

    print(f"📡 API'den {len(link_map)} kanal linki alındı.\n")

    # 2. Mevcut playlist'teki linkleri güncelle
    updated = update_playlist(link_map)

    if updated:
        print(f"\n🎉 Tamamlandı! {updated} kanal linki güncellendi.")
    else:
        print("\n⚠️ Hiçbir link güncellenemedi.")


if __name__ == "__main__":
    main()
