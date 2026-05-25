import re
import json
import requests
from datetime import datetime
import os

# ==================== KOD 1 - AYNEN KORUNDU ====================

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

    link_map = {}
    for ch in channels:
        name = ch.get("name", "").strip().upper()
        url = ch.get("m3u8_url", "")
        if name and url:
            link_map[name] = url

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

        if stripped.startswith("#EXTINF"):
            comma_pos = stripped.rfind(",")
            if comma_pos != -1:
                current_channel_name = stripped[comma_pos + 1:].strip().upper()
            new_lines.append(line)

        elif "avvaupdate.com" in stripped and ".m3u8" in stripped:
            slug_match = re.search(r'avvaupdate\.com/([^/]+)/', stripped)
            old_slug = slug_match.group(1).lower() if slug_match else ""

            new_url = link_map.get(old_slug) or link_map.get(current_channel_name)

            if new_url:
                new_lines.append(new_url + "\n")
                updated += 1
                print(f"✅ Güncellendi: {current_channel_name}")
            else:
                new_lines.append(line)
                print(f"⚠️ Eşleşme yok, eski link korundu: {current_channel_name}")

        elif stripped.startswith("# Son Güncelleme:") or stripped.startswith("# Last Updated:"):
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
            new_lines.append(f"# Son Güncelleme: {now}\n")

        else:
            new_lines.append(line)

    with open(M3U_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return updated


# ==================== KOD 2 - DİREKT EKLEME (KONTROL YOK) ====================

SOURCE_URLS = [
    "https://raw.githubusercontent.com/kadirsener1/vavoos/refs/heads/main/app/output/playlist.m3u",
    "https://raw.githubusercontent.com/kadirsener1/avva1/refs/heads/main/playlist.m3u",
    "https://raw.githubusercontent.com/kadirsener1/iptv-panel/refs/heads/main/tv247.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/hit.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/ulusal.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/cocuk.m3u",
]


def m3u_parse(content):
    """M3U içeriğini kanal listesine parse eder."""
    channels = []
    current_meta = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('#EXTINF'):
            current_meta = [line]
        elif line.startswith('#'):
            if current_meta:
                current_meta.append(line)
        else:
            if current_meta:
                extinf_line = current_meta[0]
                name_match = re.search(r',(.+)$', extinf_line)
                channel_name = name_match.group(1).strip() if name_match else extinf_line.strip()
                channels.append({
                    'name': channel_name,
                    'meta': current_meta.copy(),
                    'url': line
                })
                current_meta = []
    return channels


def append_source_channels():
    """Kaynak URL'lerden tüm kanalları direkt playlist.m3u sonuna ekle - kontrol yok"""
    merged_path = M3U_FILE

    # Mevcut dosyanın sonuna ekleme yapacağız
    if not os.path.exists(merged_path):
        print(f"⚠️ {merged_path} bulunamadı, yeni oluşturuluyor...")
        with open(merged_path, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')

    total_added = 0

    for url in SOURCE_URLS:
        print(f"📥 Kaynak çekiliyor: {url}")
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            channels = m3u_parse(resp.text)
            print(f"   {len(channels)} kanal bulundu, ekleniyor...")

            # Tüm kanalları direkt dosya sonuna ekle - hiçbir kontrol yok
            with open(merged_path, 'a', encoding='utf-8') as f:
                for ch in channels:
                    for meta_line in ch['meta']:
                        f.write(meta_line + '\n')
                    f.write(ch['url'] + '\n')

            total_added += len(channels)
            print(f"   ✅ {len(channels)} kanal eklendi.")

        except Exception as e:
            print(f"   ❌ HATA: {e}")

    return total_added


# ==================== ANA FONKSİYON ====================

def main():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    print(f"🚀 [{now}] İşlem başlıyor...\n")

    # ===== ADIM 1: KOD 1 - API'den link güncelleme =====
    print("=" * 60)
    print("📡 ADIM 1: API'den link güncelleme (Kod1)")
    print("=" * 60)

    link_map = get_fresh_links()
    if link_map:
        print(f"📡 API'den {len(link_map)} kanal linki alındı.\n")
        updated = update_playlist(link_map)
        if updated:
            print(f"\n🎉 {updated} kanal linki güncellendi.\n")
        else:
            print("\n⚠️ Hiçbir link güncellenemedi.\n")
    else:
        print("⚠️ API'den link alınamadı, devam ediliyor...\n")

    # ===== ADIM 2: KOD 2 - Kaynaklardan direkt ekleme =====
    print("=" * 60)
    print("📺 ADIM 2: Kaynaklardan kanal ekleme (Kod2)")
    print("=" * 60)

    total_added = append_source_channels()
    print(f"\n🎉 Toplam {total_added} kanal direkt eklendi.")

    print("\n" + "=" * 60)
    print("✅ TÜM İŞLEMLER TAMAMLANDI!")
    print("=" * 60)


if __name__ == "__main__":
    main()
