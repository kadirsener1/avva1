import requests
import re
import os
from datetime import datetime

# ============================================================
# AYARLAR
# ============================================================

# Kaynak M3U URL'leri (2. aşama için)
SOURCE_URLS = [
    "https://raw.githubusercontent.com/kadirsener1/vavoos/refs/heads/main/app/output/playlist.m3u",
    "https://raw.githubusercontent.com/kadirsener1/avva1/refs/heads/main/playlist.m3u",
    "https://raw.githubusercontent.com/kadirsener1/iptv-panel/refs/heads/main/tv247.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/hit.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/ulusal.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/cocuk.m3u",
]

# Avva API ayarları (1. aşama için)
API_URL = "https://avvasportshd1.com/api/channels"

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://avvasportshd1.com/channels.html",
    "Accept": "application/json"
}

# Çıkış dosyası
M3U_FILE = "playlist.m3u"


# ============================================================
# AŞAMA 1: AVVA API'DEN TÜM KANALLARI ÖNCE EKLE
# ============================================================

def get_fresh_links():
    """API'den güncel kanal listesini çek"""
    try:
        response = requests.get(API_URL, headers=API_HEADERS, timeout=30)
        response.raise_for_status()
        channels = response.json()
    except Exception as e:
        print(f"❌ API hatası: {e}")
        return None
    return channels


def stage1_avva_add():
    """Aşama 1: Avva API'den gelen tüm kanalları kategori ve logo ile ekle"""
    print("=" * 60)
    print("📡 AŞAMA 1: Avva API Kanallarını Ekleme")
    print("=" * 60)

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    print(f"🚀 [{now}] Avva kanalları çekiliyor...\n")

    channels = get_fresh_links()
    if not channels:
        print("⚠️ Avva API'den kanal alınamadı, bu aşama atlanıyor.\n")
        with open(M3U_FILE, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
        return 0

    print(f"📡 API'den {len(channels)} kanal alındı.\n")

    added = 0
    with open(M3U_FILE, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for ch in channels:
            name = ch.get("name", "").strip()
            url = ch.get("m3u8_url", "").strip()

            if not name or not url:
                continue

            # API'den kategori ve logo bilgilerini al
            category = ch.get("category", "").strip()
            logo = ch.get("logo", "").strip()

            # Alternatif alan adları kontrol et
            if not category:
                category = ch.get("group", "").strip()
            if not category:
                category = ch.get("group_title", "").strip()
            if not category:
                category = "Avva Sports"

            if not logo:
                logo = ch.get("image", "").strip()
            if not logo:
                logo = ch.get("thumbnail", "").strip()
            if not logo:
                logo = ch.get("icon", "").strip()

            # URL düzenlemeleri
            processed_url = url.replace("o=1&e", "o=1%26e")
            processed_url = processed_url.replace("&", "%26")

            # Worker prefix ekle
            prefix = "https://avva.magnitude.workers.dev/?url="
            processed_url = prefix + processed_url

            # EXTINF satırını kategori ve logo ile oluştur
            extinf = f'#EXTINF:-1'
            extinf += f' tvg-logo="{logo}"' if logo else ''
            extinf += f' group-title="{category}"'
            extinf += f',{name}'

            f.write(extinf + '\n')
            f.write(processed_url + '\n')
            added += 1
            print(f"  ✅ Eklendi: {name} | Kategori: {category} | Logo: {"Var" if logo else "Yok"}")

    if added:
        print(f"\n🎉 Aşama 1 tamamlandı! {added} avva kanalı eklendi.\n")
    else:
        print("\n⚠️ Hiçbir avva kanalı eklenemedi.\n")

    return added


# ============================================================
# AŞAMA 2: M3U KAYNAKLARINDAN TÜM KANALLARI EKLE
# ============================================================

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


def stage2_add_all_sources():
    """Aşama 2: Tüm M3U kaynaklarından tüm kanalları sona ekle"""
    print("=" * 60)
    print("📋 AŞAMA 2: M3U Kaynaklarından Tüm Kanalları Ekleme")
    print("=" * 60)

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
                print(f"  ✅ {len(channels)} kanal eklendi.")
            except Exception as e:
                print(f"  ❌ HATA: {e}")

    print(f"\n✅ Aşama 2 tamamlandı. Toplam {total_added} kanal eklendi.\n")
    return total_added


# ============================================================
# ANA FONKSİYON
# ============================================================

def main():
    print("🔄 Playlist Oluşturma Başlıyor...")
    print(f"📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    # Aşama 1: Önce Avva API kanallarını ekle
    count1 = stage1_avva_add()

    # Aşama 2: Sonra M3U kaynaklarından tüm kanalları ekle
    count2 = stage2_add_all_sources()

    print("=" * 60)
    total = (count1 or 0) + (count2 or 0)
    print(f"🏁 Tüm işlemler tamamlandı! Toplam {total} kanal playlist'e eklendi.")
    print("=" * 60)


if __name__ == '__main__':
    main()
