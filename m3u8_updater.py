import requests
import re
from datetime import datetime

STREAM_URL = "https://streams.uzunmuhalefet.com/stream/e47153e0-42fe-4980-8570-e840d1cc1cf4.m3u8"
OUTPUT_FILE = "tivibu.m3u8"

def get_content(url):
    """URL içeriğini çeker"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://streams.uzunmuhalefet.com/',
        'Origin': 'https://streams.uzunmuhalefet.com',
        'Accept': '*/*',
        'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"📡 Status: {response.status_code}")
        if response.status_code == 200:
            return response.text
        return None
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None


def find_stream_links(content):
    """
    İçerikten stream linklerini bulur
    Örnek format: http://50.7.144.122:1935/live/tivibuspor.stream/playlist.m3u8?hash=xxx
    """
    patterns = [
        # IP:Port formatındaki linkler (hash ile)
        r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+/[^\s\"\'\<\>]+\.m3u8\?hash=[a-zA-Z0-9]+',
        
        # IP:Port formatındaki linkler (hash'siz)
        r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+/[^\s\"\'\<\>]+\.m3u8[^\s\"\'\<\>]*',
        
        # Genel m3u8 linkleri (hash ile)
        r'https?://[^\s\"\'\<\>]+\.m3u8\?hash=[a-zA-Z0-9]+',
        
        # Genel m3u8 linkleri
        r'https?://[^\s\"\'\<\>]+\.m3u8[^\s\"\'\<\>]*',
        
        # ts dosyaları
        r'https?://[^\s\"\'\<\>]+\.ts\?[^\s\"\'\<\>]*',
        
        # live/stream içeren linkler
        r'https?://[^\s\"\'\<\>]*live[^\s\"\'\<\>]*stream[^\s\"\'\<\>]*',
        
        # playlist içeren linkler
        r'https?://[^\s\"\'\<\>]*playlist[^\s\"\'\<\>]*'
    ]
    
    found_links = []
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            # Temizle
            clean_link = match.strip().rstrip(',').rstrip('"').rstrip("'")
            if clean_link and clean_link not in found_links:
                # Kaynak URL'yi hariç tut
                if 'streams.uzunmuhalefet.com' not in clean_link:
                    found_links.append(clean_link)
    
    return found_links


def parse_m3u8_content(content, base_url):
    """M3U8 içeriğini parse eder ve alt linkleri çıkarır"""
    lines = content.strip().split('\n')
    links = []
    base = '/'.join(base_url.split('/')[:-1])
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            if line.startswith('http'):
                links.append(line)
            elif line.endswith('.m3u8') or line.endswith('.ts') or '?' in line:
                full_url = f"{base}/{line}"
                links.append(full_url)
    
    return links


def recursive_search(url, depth=0, max_depth=3, found_links=None):
    """Alt m3u8 dosyalarını da kontrol eder"""
    if found_links is None:
        found_links = []
    
    if depth > max_depth:
        return found_links
    
    print(f"{'  ' * depth}🔍 Kontrol ediliyor: {url[:80]}...")
    content = get_content(url)
    
    if content is None:
        return found_links
    
    # İçerikten link ara
    links = find_stream_links(content)
    for link in links:
        if link not in found_links:
            found_links.append(link)
            print(f"{'  ' * depth}✅ Bulundu: {link}")
    
    # M3U8 içindeki alt linkleri de kontrol et
    sub_links = parse_m3u8_content(content, url)
    for sub_link in sub_links:
        if sub_link.endswith('.m3u8') and sub_link not in found_links:
            # Alt m3u8'i de kontrol et
            recursive_search(sub_link, depth + 1, max_depth, found_links)
        elif sub_link not in found_links:
            found_links.append(sub_link)
    
    return found_links


def save_m3u8(stream_url, output_file):
    """Bulunan linkleri tivibu.m3u8 olarak kaydeder"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print("=" * 60)
    print("🎬 M3U8 Link Çıkarıcı")
    print(f"📅 Tarih: {timestamp}")
    print("=" * 60)
    
    # Linkleri bul
    found_links = recursive_search(stream_url)
    
    # Hash içeren linkleri önce sırala
    hash_links = [l for l in found_links if 'hash=' in l]
    other_links = [l for l in found_links if 'hash=' not in l]
    sorted_links = hash_links + other_links
    
    # M3U8 dosyası oluştur
    m3u8_content = "#EXTM3U\n"
    m3u8_content += f"# Guncelleme: {timestamp}\n"
    m3u8_content += f"# Kaynak: {stream_url}\n"
    m3u8_content += f"# Bulunan link sayisi: {len(sorted_links)}\n\n"
    
    if sorted_links:
        for i, link in enumerate(sorted_links, 1):
            # Kanal adını linkten çıkar
            channel_name = "Stream"
            if 'tivibu' in link.lower():
                channel_name = "Tivibu Spor"
            elif 'bein' in link.lower():
                channel_name = "beIN Sports"
            elif 'sport' in link.lower():
                channel_name = "Sports"
            
            m3u8_content += f"#EXTINF:-1 tvg-id=\"stream{i}\" "
            m3u8_content += f"tvg-name=\"{channel_name} {i}\" "
            m3u8_content += f"group-title=\"Canli\",{channel_name} {i}\n"
            m3u8_content += f"{link}\n\n"
        
        print(f"\n📋 Toplam {len(sorted_links)} link bulundu!")
    else:
        # Link bulunamadıysa kaynak linki ekle
        print("\n⚠️ Özel link bulunamadı, kaynak link ekleniyor...")
        m3u8_content += "#EXTINF:-1 tvg-name=\"Uzun Muhalefet\" group-title=\"Canli\",Uzun Muhalefet\n"
        m3u8_content += f"{stream_url}\n"
    
    # Dosyaya kaydet
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(m3u8_content)
    
    print(f"\n✅ Kaydedildi: {output_file}")
    
    # İçeriği göster
    print("\n📄 Dosya İçeriği:")
    print("-" * 40)
    print(m3u8_content)
    
    return len(sorted_links) > 0


def main():
    success = save_m3u8(STREAM_URL, OUTPUT_FILE)
    if success:
        print("\n✅ İşlem başarılı!")
    else:
        print("\n⚠️ Özel link bulunamadı, varsayılan link kullanıldı.")


if __name__ == "__main__":
    main()
