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
        return None, None

    # Kanal adı -> güncel link eşleştirmesi
    link_map = {}
    # Kanal adı -> tüm bilgiler (kategori, logo, id)
    info_map = {}

    for ch in channels:
        name = ch.get("name", "").strip()
        name_upper = name.upper()
        url = ch.get("m3u8_url", "")

        # Kategori bilgisi
        category = (ch.get("category", "") or ch.get("group", "") or
                    ch.get("group_title", "") or "").strip()
        if not category:
            category = "Avva Sports"

        # Logo bilgisi
        logo = (ch.get("logo", "") or ch.get("image", "") or
                ch.get("thumbnail", "") or ch.get("icon", "") or "").strip()

        # ID bilgisi
        tvg_id = (ch.get("id", "") or ch.get("tvg_id", "") or
                  ch.get("channel_id", "") or "").strip()
        if not tvg_id:
            tvg_id = name

        if name_upper and url:
            link_map[name_upper] = url
            info_map[name_upper] = {
                "name": name,
                "category": category,
                "logo": logo,
                "tvg_id": tvg_id
            }

            # URL'den slug çıkar
            slug_match = re.search(r'avvaupdate\.com/([^/]+)/', url)
            if slug_match:
                slug = slug_match.group(1).lower()
                link_map[slug] = url
                info_map[slug] = info_map[name_upper]

    return link_map, info_map


def update_playlist(link_map, info_map):
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
            comma_pos = stripped.rfind(",")
            if comma_pos != -1:
                current_channel_name = stripped[comma_pos + 1:].strip().upper()

            # EXTINF satırında kategori/logo/id yoksa API'den ekle
            has_group = "group-title=" in stripped
            has_logo = "tvg-logo=" in stripped
            has_id = "tvg-id=" in stripped

            # Slug ile veya isimle info bul
            info = info_map.get(current_channel_name)
            if not info:
                # Bir sonraki satırdan slug dene
                if i + 1 < len(lines):
                    next_stripped = lines[i + 1].strip()
                    slug_match = re.search(r'avvaupdate\.com/([^/]+)/', next_stripped)
                    if slug_match:
                        info = info_map.get(slug_match.group(1).lower())

            if info and (not has_group or not has_logo or not has_id):
                # EXTINF satırını yeniden oluştur
                # Mevcut parametreleri koru, eksikleri ekle
                extinf_params = stripped[:comma_pos] if comma_pos != -1 else stripped
                channel_display = stripped[comma_pos + 1:].strip() if comma_pos != -1 else ""

                if not has_id and info.get("tvg_id"):
                    extinf_params = extinf_params.rstrip() + f' tvg-id="{info["tvg_id"]}"'
                if not has_logo and info.get("logo"):
                    extinf_params = extinf_params.rstrip() + f' tvg-logo="{info["logo"]}"'
                if not has_group and info.get("category"):
                    extinf_params = extinf_params.rstrip() + f' group-title="{info["category"]}"'

                new_lines.append(f"{extinf_params},{channel_display}\n")
            else:
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
    """Aşama 1: Avva API link güncelleme + kategori/logo/id ekleme"""
    print("=" * 60)
    print("📡 AŞAMA 1: Avva API Link Güncelleme")
    print("=" * 60)

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    print(f"🚀 [{now}] Linkler güncelleniyor...\n")

    # 1. API'den güncel linkleri ve bilgileri al
    link_map, info_map = get_fresh_links()
    if not link_map:
        print("⚠️ Avva API'den link alınamadı, bu aşama atlanıyor.\n")
        return

    print(f"📡 API'den {len(link_map)} kanal linki alındı.\n")

    # 2. Mevcut playlist'teki linkleri güncelle
    updated = update_playlist(link_map, info_map)

    if updated:
        print(f"\n🎉 Aşama 1 tamamlandı! {updated} kanal linki güncellendi.\n")
    else:
        print("\n⚠️ Hiçbir link güncellenemedi.\n")


# ============================================================
# AŞAMA 2: M3U KAYNAKLARINI DİREKT EKLE (KONTROL YOK)
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

    # Aşama 1: Avva API link güncelleme (1. kod + kategori/logo/id)
    stage1_avva_update()

    # Aşama 2: M3U kaynaklarından tüm kanalları direkt ekle
    count2 = stage2_append_sources()

    print("=" * 60)
    print(f"🏁 Tüm işlemler tamamlandı!")
    print("=" * 60)


if __name__ == '__main__':
    main()
