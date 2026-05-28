import requests
import time
import os
from datetime import datetime

def get_m3u8_content(url):
    """
    M3U8 URL'sinden içeriği çeker
    """
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


def extract_stream_url(m3u8_content, base_url):
    """
    M3U8 içeriğinden gerçek stream URL'sini çıkarır
    """
    lines = m3u8_content.strip().split('\n')
    stream_urls = []
    
    for line in lines:
        line = line.strip()
        # .m3u8 veya .ts uzantılı linkleri bul
        if line and not line.startswith('#'):
            if line.startswith('http'):
                stream_urls.append(line)
            else:
                # Relative URL'yi absolute URL'ye çevir
                base = '/'.join(base_url.split('/')[:-1])
                full_url = f"{base}/{line}"
                stream_urls.append(full_url)
    
    return stream_urls


def save_tivibu_m3u8(stream_url, output_file="tivibu.m3u8"):
    """
    Stream URL'sini tivibu.m3u8 formatında kaydeder
    """
    
    # Önce ana m3u8'i çek
    print(f"🔄 Stream kontrol ediliyor...")
    content = get_m3u8_content(stream_url)
    
    if content is None:
        print("❌ Stream'e erişilemedi!")
        return False
    
    # İçerideki URL'leri çıkar
    extracted_urls = extract_stream_url(content, stream_url)
    
    # Tivibu formatında m3u8 oluştur
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    m3u8_content = f"""#EXTM3U
#EXT-X-VERSION:3
# Son güncelleme: {timestamp}
# Kaynak: {stream_url}

#EXTINF:-1 tvg-id="uzunmuhalefet" tvg-name="Uzun Muhalefet" tvg-logo="" group-title="Canlı Yayın",Uzun Muhalefet
{stream_url}
"""
    
    # Eğer alt stream'ler varsa onları da ekle
    if extracted_urls:
        m3u8_content += "\n# Alt Stream URL'leri:\n"
        for i, url in enumerate(extracted_urls, 1):
            m3u8_content += f"# Stream {i}: {url}\n"
    
    # Dosyaya kaydet
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(m3u8_content)
    
    print(f"✅ Kaydedildi: {output_file}")
    print(f"📅 Zaman: {timestamp}")
    
    return True


def auto_update(stream_url, output_file="tivibu.m3u8", interval=60):
    """
    Belirli aralıklarla otomatik güncelleme yapar
    """
    
    print("=" * 60)
    print("🔄 M3U8 Otomatik Güncelleyici")
    print(f"📁 Dosya: {output_file}")
    print(f"⏱️  Güncelleme aralığı: {interval} saniye")
    print("⏹️  Durdurmak için: Ctrl+C")
    print("=" * 60)
    
    update_count = 0
    
    while True:
        try:
            update_count += 1
            print(f"\n[Güncelleme #{update_count}]")
            
            success = save_tivibu_m3u8(stream_url, output_file)
            
            if success:
                print(f"⏳ Sonraki güncelleme: {interval} saniye sonra...")
            else:
                print(f"⚠️  Başarısız, {interval} saniye sonra tekrar denenecek...")
            
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Program durduruldu.")
            break


def main():
    # Stream URL'si
    STREAM_URL = "https://streams.uzunmuhalefet.com/stream/e47153e0-42fe-4980-8570-e840d1cc1cf4.m3u8"
    OUTPUT_FILE = "tivibu.m3u8"
    UPDATE_INTERVAL = 60  # saniye (1 dakika)
    
    print("\n🎬 M3U8 Link Çekici")
    print("-" * 40)
    print("1. Tek seferlik kaydet")
    print("2. Otomatik güncelle")
    print("-" * 40)
    
    choice = input("Seçiminiz (1/2): ").strip()
    
    if choice == "1":
        save_tivibu_m3u8(STREAM_URL, OUTPUT_FILE)
    elif choice == "2":
        interval = input(f"Güncelleme aralığı (saniye, varsayılan {UPDATE_INTERVAL}): ").strip()
        if interval.isdigit():
            UPDATE_INTERVAL = int(interval)
        auto_update(STREAM_URL, OUTPUT_FILE, UPDATE_INTERVAL)
    else:
        print("Geçersiz seçim!")


if __name__ == "__main__":
    main()
