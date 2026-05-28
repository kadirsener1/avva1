import requests
import os
from datetime import datetime

STREAM_URL = "https://streams.uzunmuhalefet.com/stream/e47153e0-42fe-4980-8570-e840d1cc1cf4.m3u8"
OUTPUT_FILE = "tivibu.m3u8"

def get_m3u8_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://streams.uzunmuhalefet.com/',
        'Origin': 'https://streams.uzunmuhalefet.com'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text
        else:
            print(f"❌ HTTP Hata: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return None

def extract_links(content, base_url):
    lines = content.strip().split('\n')
    links = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            if line.startswith('http'):
                links.append(line)
            else:
                base = '/'.join(base_url.split('/')[:-1])
                links.append(f"{base}/{line}")
    return links

def save_m3u8(stream_url, output_file):
    print(f"🔄 Stream çekiliyor: {stream_url}")
    content = get_m3u8_content(stream_url)

    if content is None:
        print("❌ İçerik alınamadı!")
        return False

    links = extract_links(content, stream_url)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Ana playlist içeriği
    m3u8_output = "#EXTM3U\n"
    m3u8_output += f"# Guncelleme: {timestamp}\n"
    m3u8_output += f"# Kaynak: {stream_url}\n\n"
    m3u8_output += "#EXTINF:-1 tvg-id=\"uzunmuhalefet\" "
    m3u8_output += "tvg-name=\"Uzun Muhalefet\" "
    m3u8_output += "tvg-logo=\"\" "
    m3u8_output += "group-title=\"Canli Yayin\","
    m3u8_output += "Uzun Muhalefet\n"
    m3u8_output += f"{stream_url}\n"

    # Alt linkler varsa ekle
    if links:
        m3u8_output += "\n# === Alt Stream Linkleri ===\n"
        for i, link in enumerate(links, 1):
            m3u8_output += f"# [{i}] {link}\n"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(m3u8_output)

    print(f"✅ Dosya güncellendi: {output_file}")
    print(f"📅 Zaman: {timestamp}")
    print(f"🔗 Bulunan link sayısı: {len(links)}")

    if links:
        print("\n📋 Bulunan Linkler:")
        for i, link in enumerate(links, 1):
            print(f"  [{i}] {link}")

    return True

def main():
    print("=" * 60)
    print("🎬 M3U8 Updater - GitHub Actions")
    print("=" * 60)
    success = save_m3u8(STREAM_URL, OUTPUT_FILE)
    if success:
        print("\n✅ İşlem başarılı!")
    else:
        print("\n❌ İşlem başarısız!")
        exit(1)

if __name__ == "__main__":
    main()
