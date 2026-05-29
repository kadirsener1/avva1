import requests
import re
import os
import base64
from datetime import datetime

# ============================================================
# AYARLAR
# ============================================================

SOURCE_URLS = [
    "https://raw.githubusercontent.com/kadirsener1/VAVOO/refs/heads/main/ozel_listem.m3u",
    "https://raw.githubusercontent.com/kadirsener1/avva1/refs/heads/main/m3u/trspor.m3u",
    "https://raw.githubusercontent.com/kadirsener1/247/refs/heads/main/tv247.m3u",
    "https://raw.githubusercontent.com/kadirsener1/avva1/refs/heads/main/m3u/ulusal.m3u",
    "https://raw.githubusercontent.com/kadirsener1/avva1/refs/heads/main/m3u/haber.m3u",
    "https://raw.githubusercontent.com/kadirsener1/avva1/refs/heads/main/m3u/cocuk.m3u",
]

API_URL = "https://avvasportshd1.com/api/channels"
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://avvasportshd1.com/channels.html",
    "Accept": "application/json"
}

# ============================================================
# GITHUB AYARLARI
# ============================================================
GITHUB_TOKEN = os.environ.get("GH_TOKEN")          # GitHub Actions secret'tan alır
GITHUB_REPO  = "kadirsener1/avva"                   # hangi repo
GITHUB_PATH  = "playlist.m3u"                       # repodaki dosya yolu
GITHUB_BRANCH = "main"

RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/refs/heads/{GITHUB_BRANCH}/{GITHUB_PATH}"

# Geçici yerel dosya (işlem sırasında kullanılır)
LOCAL_FILE = "playlist.m3u"


# ============================================================
# GITHUB OKUMA / YAZMA
# ============================================================

def github_read():
    """GitHub'dan mevcut playlist.m3u içeriğini ve SHA'sını çek."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        resp = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH}, timeout=15)
        if resp.status_code == 404:
            print("  GitHub'da dosya yok, sıfırdan oluşturulacak.")
            return None, None
        resp.raise_for_status()
        data = resp.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        sha = data["sha"]
        print(f"  GitHub'dan {len(content)} karakter okundu. SHA: {sha[:8]}...")
        return content, sha
    except Exception as e:
        print(f"  GitHub okuma hatası: {e}")
        return None, None


def github_write(content, sha=None):
    """Güncellenmiş içeriği GitHub'a yaz (commit)."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    body = {
        "message": f"🔄 Playlist güncellendi [{now}]",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": GITHUB_BRANCH
    }
    if sha:
        body["sha"] = sha  # Güncelleme için SHA zorunlu

    try:
        resp = requests.put(url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        print(f"  ✅ GitHub'a başarıyla yazıldı!")
        return True
    except Exception as e:
        print(f"  ❌ GitHub yazma hatası: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Detay: {e.response.text}")
        return False


# ============================================================
# M3U PARSE
# ============================================================

def m3u_parse(content):
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


def channels_to_m3u(channels):
    """Kanal listesini M3U string'e çevir."""
    lines = ['#EXTM3U']
    for ch in channels:
        for meta_line in ch['meta']:
            lines.append(meta_line)
        lines.append(ch['url'])
    return '\n'.join(lines) + '\n'


def is_avva_channel(channel):
    return "avvaupdate.com" in channel.get('url', '') or \
           "avva" in channel.get('url', '').lower()


# ============================================================
# AŞAMA 1: M3U KAYNAKLARINI BİRLEŞTİR / LİNK GÜNCELLE
# ============================================================

def stage1_merge_sources():
    print("=" * 60)
    print("📋 AŞAMA 1: M3U Kaynakları Birleştirme / Link Güncelleme")
    print("=" * 60)

    # GitHub'dan mevcut dosyayı oku
    existing_content, sha = github_read()

    if existing_content:
        # ----------------------------------------------------------------
        # MEVCUT DOSYA VAR → Sadece linkleri güncelle + yeni kanalları ekle
        # ----------------------------------------------------------------
        print(f"Mevcut playlist bulundu. Linkler güncelleniyor...")
        existing_channels = m3u_parse(existing_content)
        print(f"Mevcut {len(existing_channels)} kanal yüklendi.")

        existing_names = set(ch['name'] for ch in existing_channels)
        source_links = {}
        source_meta = {}
        new_channels_from_sources = []
        new_names_added = set()

        for url in SOURCE_URLS:
            print(f"Kaynak çekiliyor: {url}")
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                channels = m3u_parse(resp.text)
                for ch in channels:
                    source_links[ch['name']] = ch['url']
                    source_meta[ch['name']] = ch['meta']
                    if ch['name'] not in existing_names and \
                       ch['name'] not in new_names_added:
                        new_channels_from_sources.append(ch)
                        new_names_added.add(ch['name'])
                print(f"  {len(channels)} kanal tarandı.")
            except Exception as e:
                print(f"  HATA: {e}")

        # Linkleri güncelle
        updated_count = 0
        for ch in existing_channels:
            if ch['name'] in source_links:
                new_url = source_links[ch['name']]
                if ch['url'] != new_url:
                    print(f"  🔗 Link güncellendi: {ch['name']}")
                    ch['url'] = new_url
                    updated_count += 1

        # Yeni kanalları sona ekle
        if new_channels_from_sources:
            existing_channels.extend(new_channels_from_sources)
            print(f"🆕 {len(new_channels_from_sources)} yeni kanal eklendi.")

        new_content = channels_to_m3u(existing_channels)
        print(f"✅ Aşama 1 hazır. {updated_count} link güncellendi, "
              f"toplam {len(existing_channels)} kanal.")

    else:
        # ----------------------------------------------------------------
        # DOSYA YOK → Sıfırdan oluştur (Avva başta)
        # ----------------------------------------------------------------
        print("Playlist bulunamadı. Sıfırdan oluşturuluyor...")
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
                        all_channels[seen_channels[name]]['url'] = ch['url']
            except Exception as e:
                print(f"  HATA: {e}")

        avva_channels     = [ch for ch in all_channels if is_avva_channel(ch)]
        non_avva_channels = [ch for ch in all_channels if not is_avva_channel(ch)]
        sorted_channels   = avva_channels + non_avva_channels

        if avva_channels:
            print(f"📡 {len(avva_channels)} Avva kanalı başa alındı.")

        new_content = channels_to_m3u(sorted_channels)
        sha = None  # Yeni dosya, SHA yok
        print(f"✅ Aşama 1 hazır. Toplam {len(sorted_channels)} kanal.")

    # GitHub'a yaz
    print("\n📤 GitHub'a yazılıyor...")
    github_write(new_content, sha)
    print()

    # Aşama 2 için yerel kopyayı güncelle
    with open(LOCAL_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return sha  # Aşama 2'de tekrar yazarken lazım


# ============================================================
# AŞAMA 2: AVVA API'DEN LİNK GÜNCELLEME
# ============================================================

def get_fresh_links():
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
        url  = ch.get("m3u8_url", "")
        if name and url:
            link_map[name] = url
            slug_match = re.search(r'avvaupdate\.com/([^/]+)/', url)
            if slug_match:
                link_map[slug_match.group(1).lower()] = url
    return link_map


def stage2_avva_update():
    print("=" * 60)
    print("📡 AŞAMA 2: Avva API Link Güncelleme")
    print("=" * 60)

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    print(f"🚀 [{now}] Avva linkleri güncelleniyor...\n")

    link_map = get_fresh_links()
    if not link_map:
        print("⚠️ API'den link alınamadı, bu aşama atlanıyor.\n")
        return

    print(f"📡 API'den {len(link_map)} kanal linki alındı.\n")

    # Yerel dosyayı oku (Aşama 1'de yazılmıştı)
    try:
        with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ Yerel dosya bulunamadı!")
        return

    new_lines = []
    updated = 0
    current_channel_name = ""

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("#EXTINF"):
            comma_pos = stripped.rfind(",")
            if comma_pos != -1:
                current_channel_name = stripped[comma_pos + 1:].strip().upper()
            new_lines.append(line)

        elif "avvaupdate.com" in stripped and ".m3u8" in stripped:
            slug_match = re.search(r'avvaupdate\.com/([^/]+)/', stripped)
            old_slug   = slug_match.group(1).lower() if slug_match else ""
            new_url    = link_map.get(old_slug) or link_map.get(current_channel_name)

            if new_url:
                new_url = new_url.replace("o=1&e", "o=1%26e")
                new_url = new_url.replace("&", "%26")
                prefix  = "https://avva.magnitude.workers.dev/?url="
                new_url = prefix + new_url
                new_lines.append(new_url + "\n")
                updated += 1
                print(f"  ✅ Güncellendi: {current_channel_name}")
            else:
                new_lines.append(line)
                print(f"  ⚠️ Eşleşme yok: {current_channel_name}")

        elif stripped.startswith("# Son Güncelleme:"):
            now2 = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
            new_lines.append(f"# Son Güncelleme: {now2}\n")
        else:
            new_lines.append(line)

    if updated == 0:
        print("⚠️ Hiçbir avva linki güncellenemedi.\n")
        return

    final_content = "".join(new_lines)

    # Güncellenmiş içeriği GitHub'a yaz
    # Yeni SHA almak için tekrar oku
    print("\n📤 Avva güncellemeleri GitHub'a yazılıyor...")
    _, current_sha = github_read()
    github_write(final_content, current_sha)

    print(f"\n🎉 Aşama 2 tamamlandı! {updated} avva linki güncellendi.\n")


# ============================================================
# ANA FONKSİYON
# ============================================================

def main():
    if not GITHUB_TOKEN:
        print("❌ HATA: GH_TOKEN environment variable bulunamadı!")
        print("   GitHub Actions > Settings > Secrets > GH_TOKEN ekleyin.")
        exit(1)

    print("🔄 Playlist Güncelleme Başlıyor...")
    print(f"📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"📁 Hedef: https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{GITHUB_PATH}")
    print()

    stage1_merge_sources()
    stage2_avva_update()

    print("=" * 60)
    print("🏁 Tüm işlemler tamamlandı!")
    print("=" * 60)


if __name__ == '__main__':
    main()
