import requests
import re
import os
import json
from datetime import datetime

# ============================================================
# AYARLAR
# ============================================================

# Kaynak M3U URL'leri (1. aşama için)
SOURCE_URLS = [
    "https://raw.githubusercontent.com/kadirsener1/VAVOO/refs/heads/main/ozel_listem.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/trspor.m3u",
    "https://raw.githubusercontent.com/kadirsener1/247/refs/heads/main/tv247.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/ulusal.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/haber.m3u",
    "https://raw.githubusercontent.com/kadirsener1/tivim/refs/heads/main/m3u/cocuk.m3u",
]

# Avva API ayarları (2. aşama için)
API_URL = "https://avvasportshd1.com/api/channels"

API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://avvasportshd1.com/channels.html",
    "Accept": "application/json"
}

# Çıkış dosyası
M3U_FILE = "playlist.m3u"


# ============================================================
# AŞAMA 1: M3U KAYNAKLARINI BİRLEŞTİR / LİNK GÜNCELLE
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


def is_avva_channel(channel):
    """Kanalın Avva kanalı olup olmadığını kontrol eder"""
    return "avvaupdate.com" in channel.get('url', '') or "avva" in channel.get('url', '').lower()


def stage1_merge_sources():
    """Aşama 1: M3U kaynaklarını birleştir veya mevcut dosyadaki linkleri güncelle + yeni kanalları ekle"""
    print("=" * 60)
    print("📋 AŞAMA 1: M3U Kaynakları Birleştirme / Link Güncelleme")
    print("=" * 60)

    if os.path.exists(M3U_FILE):
        # ----------------------------------------------------------------
        # MEVCUT playlist.m3u VAR
        # Kural:
        #   - Mevcut sıralama KESINLIKLE korunur (avva dahil hiçbir şey)
        #   - Kaynaklarda isim eşleşen kanalların SADECE linki güncellenir
        #   - Yeni kanallar listenin SONUNA eklenir
        #   - Meta/isim/grup hiçbir şeye dokunulmaz
        # ----------------------------------------------------------------
        print(f"Mevcut {M3U_FILE} bulundu. Sadece linkler güncelleniyor...")
        with open(M3U_FILE, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        existing_channels = m3u_parse(existing_content)
        print(f"Mevcut {len(existing_channels)} kanal yüklendi.")

        # Mevcut kanal isimlerini set olarak tut (hızlı arama için)
        existing_names = set(ch['name'] for ch in existing_channels)

        # Kaynaklardan kanal adı -> link sözlüğü oluştur + yeni kanalları topla
        source_links = {}        # isim -> url  (link güncelleme için)
        source_meta = {}         # isim -> meta (sadece yeni kanallar için)
        new_channels_from_sources = []
        new_names_added = set()

        for url in SOURCE_URLS:
            print(f"Kaynak çekiliyor: {url}")
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                channels = m3u_parse(resp.text)
                for ch in channels:
                    # Link güncelleme sözlüğüne ekle
                    # Aynı isim birden fazla kaynakta varsa SON kaynak kazanır
                    source_links[ch['name']] = ch['url']
                    source_meta[ch['name']] = ch['meta']

                    # Yeni kanal mı kontrol et
                    if ch['name'] not in existing_names and ch['name'] not in new_names_added:
                        new_channels_from_sources.append(ch)
                        new_names_added.add(ch['name'])

                print(f"  {len(channels)} kanal tarandı.")
            except Exception as e:
                print(f"  HATA: {e}")

        # ----------------------------------------------------------------
        # Mevcut kanalların SADECE linklerini güncelle
        # Sıralama, meta, isim — hiçbir şeye dokunma
        # ----------------------------------------------------------------
        updated_count = 0
        for ch in existing_channels:
            if ch['name'] in source_links:
                new_url = source_links[ch['name']]
                if ch['url'] != new_url:
                    print(f"  🔗 Link güncellendi: {ch['name']}")
                    print(f"     Eski: {ch['url']}")
                    print(f"     Yeni: {new_url}")
                    ch['url'] = new_url
                    updated_count += 1

        # ----------------------------------------------------------------
        # Yeni kanalları SONUNA ekle (avva olanlar dahil)
        # NOT: Yeni kanallar için sıralama uygulanmaz,
        #      ilk oluşturma aşamasında zaten avva başta oluşuyor.
        # ----------------------------------------------------------------
        if new_channels_from_sources:
            existing_channels.extend(new_channels_from_sources)
            print(f"🆕 {len(new_channels_from_sources)} yeni kanal listenin sonuna eklendi:")
            for ch in new_channels_from_sources:
                print(f"   + {ch['name']}")

        # ----------------------------------------------------------------
        # Güncellenmiş dosyayı yaz — sıra mevcut haliyle korunur
        # ----------------------------------------------------------------
        with open(M3U_FILE, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for ch in existing_channels:
                for meta_line in ch['meta']:
                    f.write(meta_line + '\n')
                f.write(ch['url'] + '\n')

        print(f"✅ Aşama 1 tamamlandı. {updated_count} kanalın linki güncellendi, "
              f"{len(new_channels_from_sources)} yeni kanal eklendi. "
              f"Toplam {len(existing_channels)} kanal kaydedildi.\n")

    else:
        # ----------------------------------------------------------------
        # playlist.m3u YOK: İlk oluşturma
        # Avva kanalları BAŞA alınır, sonra diğerleri
        # ----------------------------------------------------------------
        print(f"{M3U_FILE} bulunamadı. Kaynaklar birleştiriliyor...")
        all_channels = []
        seen_channels = {}

        for url in SOURCE_URLS:
            print(f"Kaynak çekiliyor: {url}")
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                channels = m3u_parse(resp.text)
                print(f"  {len(channels)} kanal bulundu.")
                for ch in channels:
                    name = ch['name']
                    if name not in seen_channels:
                        all_channels.append(ch)
                        seen_channels[name] = len(all_channels) - 1
                    else:
                        # Tekrar eden kanalda sadece linki güncelle
                        idx = seen_channels[name]
                        all_channels[idx]['url'] = ch['url']
            except Exception as e:
                print(f"  HATA: {e}")

        # *** İLK OLUŞTURMADA Avva kanalları başa al ***
        avva_channels = [ch for ch in all_channels if is_avva_channel(ch)]
        non_avva_channels = [ch for ch in all_channels if not is_avva_channel(ch)]
        sorted_channels = avva_channels + non_avva_channels

        if avva_channels:
            print(f"📡 {len(avva_channels)} Avva kanalı listenin başına yerleştirildi.")

        # Dosyayı yaz
        with open(M3U_FILE, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for ch in sorted_channels:
                for meta_line in ch['meta']:
                    f.write(meta_line + '\n')
                f.write(ch['url'] + '\n')

        print(f"✅ Aşama 1 tamamlandı. Toplam {len(sorted_channels)} kanal birleştirildi, "
              f"tekrar edenler ayıklandı.\n")


# ============================================================
# AŞAMA 2: AVVA API'DEN LİNK GÜNCELLEME
# ============================================================

def get_fresh_links():
    """API'den güncel m3u8 linklerini çek"""
    try:
        response = requests.get(API_URL, headers=API_HEADERS, timeout=30)
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

            # URL'den slug çıkar (örn: avvaupdate.com/ssport1/index.m3u8 -> ssport1)
            slug_match = re.search(r'avvaupdate\.com/([^/]+)/', url)
            if slug_match:
                link_map[slug_match.group(1).lower()] = url

    return link_map


def update_playlist_avva(link_map):
    """Mevcut playlist.m3u dosyasındaki avva linklerini güncelle"""
    try:
        with open(M3U_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ {M3U_FILE} dosyası bulunamadı!")
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
            new_lines.append(line)

        # m3u8 link satırı - avva linkini güncelle
        elif "avvaupdate.com" in stripped and ".m3u8" in stripped:
            # Eski linkten slug çıkar
            slug_match = re.search(r'avvaupdate\.com/([^/]+)/', stripped)
            old_slug = slug_match.group(1).lower() if slug_match else ""

            # Önce slug ile eşleştir, bulamazsa isimle dene
            new_url = link_map.get(old_slug) or link_map.get(current_channel_name)

            if new_url:
                # 1. Karakter düzenlemeleri (URL encode)
                new_url = new_url.replace("o=1&e", "o=1%26e")
                new_url = new_url.replace("&", "%26")

                # 2. Worker prefix ekle
                prefix = "https://avva.magnitude.workers.dev/?url="
                new_url = prefix + new_url

                new_lines.append(new_url + "\n")
                updated += 1
                print(f"  ✅ Güncellendi: {current_channel_name}")
            else:
                new_lines.append(line)
                print(f"  ⚠️ Eşleşme yok, eski link korundu: {current_channel_name}")

        # Güncelleme tarih satırını güncelle
        elif stripped.startswith("# Son Güncelleme:") or stripped.startswith("# Last Updated:"):
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
            new_lines.append(f"# Son Güncelleme: {now}\n")

        # Diğer satırlar aynen kalsın
        else:
            new_lines.append(line)

    # Dosyayı yaz
    with open(M3U_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return updated


def stage2_avva_update():
    """Aşama 2: Avva API'den link güncelleme"""
    print("=" * 60)
    print("📡 AŞAMA 2: Avva API Link Güncelleme")
    print("=" * 60)

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    print(f"🚀 [{now}] Avva linkleri güncelleniyor...\n")

    # API'den güncel linkleri al
    link_map = get_fresh_links()
    if not link_map:
        print("⚠️ Avva API'den link alınamadı, bu aşama atlanıyor.\n")
        return

    print(f"📡 API'den {len(link_map)} kanal linki alındı.\n")

    # Mevcut playlist'teki avva linklerini güncelle
    updated = update_playlist_avva(link_map)

    if updated:
        print(f"\n🎉 Aşama 2 tamamlandı! {updated} avva kanal linki güncellendi.\n")
    else:
        print("\n⚠️ Hiçbir avva linki güncellenemedi.\n")


# ============================================================
# ANA FONKSİYON
# ============================================================

def main():
    print("🔄 Playlist Güncelleme Başlıyor...")
    print(f"📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    # Aşama 1: M3U kaynaklarını birleştir / güncelle
    stage1_merge_sources()

    # Aşama 2: Avva API'den linkleri güncelle
    stage2_avva_update()

    print("=" * 60)
    print("🏁 Tüm işlemler tamamlandı!")
    print("=" * 60)


if __name__ == '__main__':
    main()
