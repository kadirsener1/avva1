import re
import json
import os
import requests
from datetime import datetime

# ============================================================
# AYARLAR
# ============================================================

# Avva API ayarları (1. aşama)
API_URL = "https://avvasportshd1.com/api/channels"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://avvasportshd1.com/channels.html",
    "Accept": "application/json"
}

M3U_FILE = "playlist.m3u"

# Kaynak M3U URL'leri (2. aşama)
SOURCE_URLS = [
    "https://raw.githubusercontent.com/kadirsener1/vavoos/refs/heads/main/app/output/playlist.m3u",
    "https://raw.githubusercontent.com/kadirsener1/avva1/refs/heads/main/playlist.m3u",
    "https://raw.githubusercontent.com/kadirsener1/iptv-panel/refs/heads/main/tv247.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/hit.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/ulusal.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/cocuk.m3u",
]


# ============================================================
# AŞAMA 1: AVVA API LİNK GÜNCELLEME (1. KOD - AYNEN KORUNDU)
# ============================================================

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
                # 1. Önce karakter düzenlemelerini (URL encode) yapıyoruz
                new_url = new_url.replace("o=1&e", "o=1%26e")
                new_url = new_url.replace("&", "%26")

                # 2. Düzenlenmiş linkin başına belirtilen worker adresini ekliyoruz
                prefix = "https://avva.magnitude.workers.dev/?url="
                new_url = prefix + new_url

                new_lines.append(new_url + "\n")
                updated += 1
                print(f"✅ Güncellendi ve Öneklendi: {current_channel_name}")
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


def stage1_avva_update():
    """Aşama 1: Avva API link güncelleme - 1. kod aynen"""
    print("=" * 60)
    print("📡 AŞAMA 1: Avva API Link Güncelleme")
    print("=" * 60)

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    print(f"🚀 [{now}] Linkler güncelleniyor...\n")

    # 1. API'den güncel linkleri al
    link_map = get_fresh_links()
    if not link_map:
        print("⚠️ Avva API'den link alınamadı, bu aşama atlanıyor.\n")
        return

    print(f"📡 API'den {len(link_map)} kanal linki alındı.\n")

    # 2. Mevcut playlist'teki linkleri güncelle
    updated = update_playlist(link_map)

    if updated:
        print(f"\n🎉 Aşama 1 tamamlandı! {updated} kanal linki güncellendi.\n")
    else:
        print("\n⚠️ Hiçbir link güncellenemedi.\n")


# ============================================================
# AŞAMA 2: M3U KAYNAKLARINI DİREKT EKLE (KONTROL YOK)
# ============================================================

def m3u_parse(content):
    """M3U içeriğini kanal listesine parse eder. Her kanal: isim, metadata (tüm # satırları), link"""
    channels = []
    current_meta = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('#EXTINF'):
            # Yeni kanal başlangıcı
            current_meta = [line]
        elif line.startswith('#'):
            # Mevcut kanalın metadata satırı (EXTVLCOPT dahil)
            if current_meta:
                current_meta.append(line)
        else:
            # Yayın linki satırı
            if current_meta:
                # Kanal adını EXTINF satırından al (virgülden sonraki kısım)
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


def stage2_append_sources():
    """Aşama 2: M3U kaynaklarından tüm kanalları kontrol etmeden direkt sona ekle"""
    print("=" * 60)
    print("📋 AŞAMA 2: M3U Kaynaklarından Tüm Kanalları Ekleme")
    print("=" * 60)

    # Dosya yoksa başlat
    if not os.path.exists(M3U_FILE):
        with open(M3U_FILE, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
        print(f"{M3U_FILE} oluşturuldu.\n")

    total_added = 0

    with open(M3U_FILE, 'a', encoding='utf-8') as f:
        for url in SOURCE_URLS:
            print(f"Kaynak çekiliyor: {url}")
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                channels = m3u_parse(resp.text)
                for ch in channels:
                    for meta_line in ch['meta']:
                        f.write(meta_line + '\n')
                    f.write(ch['url'] + '\n')
                total_added += len(channels)
                print(f"  ✅ {len(channels)} kanal direkt eklendi.")
            except Exception as e:
                print(f"  ❌ HATA: {e}")

    print(f"\n✅ Aşama 2 tamamlandı. Toplam {total_added} kanal kontrol edilmeden eklendi.\n")
    return total_added


# ============================================================
# ANA FONKSİYON
# ============================================================

def main():
    print("🔄 Playlist Güncelleme & Birleştirme Başlıyor...")
    print(f"📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    # Aşama 1: Avva API link güncelleme (1. kod aynen çalışır)
    stage1_avva_update()

    # Aşama 2: M3U kaynaklarından tüm kanalları direkt ekle (kontrol yok)
    count2 = stage2_append_sources()

    print("=" * 60)
    print(f"🏁 Tüm işlemler tamamlandı!")
    print("=" * 60)


if __name__ == '__main__':
    main()
