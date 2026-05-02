import json
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

def scrape_avva():
    print(f"[{datetime.now()}] Scraping başlatılıyor (Network Sniffer Modu)...")
    
    found_links = set() # Tekrar eden linkleri engellemek için

    with sync_playwright() as p:
        # Tarayıcıyı başlat
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # AĞ TRAFİĞİNİ DİNLE: m3u8 içeren her isteği yakala
        def handle_request(request):
            url = request.url
            if ".m3u8" in url and "avvaupdate.com" in url:
                found_links.add(url)
                print(f"Bulunan Link: {url}")

        page.on("request", handle_request)

        try:
            # Ana sayfaya git
            page.goto("https://avvasportshd1.com/channels.html", wait_until="networkidle", timeout=60000)
            
            # Bazı siteler tıklama olmadan linkleri yüklemez, sayfada biraz bekle
            page.wait_for_timeout(10000) 
            
            # Eğer hala link yoksa, sayfadaki butonları simüle etmek gerekebilir
            # Ancak genellikle networkidle yeterlidir.
            
        except Exception as e:
            print(f"Hata oluştu: {e}")
        finally:
            browser.close()

    if not found_links:
        print("❌ Hiç m3u8 linki bulunamadı. Site korumayı artırmış olabilir.")
        return

    # Kanalları işle ve kaydet
    channels = []
    for link in found_links:
        # Linkten kanal adını tahmin et (Örn: ssport1)
        name_match = re.search(r'com/([^/?]+)', link)
        channel_id = name_match.group(1) if name_match else "Bilinmeyen"
        
        channels.append({
            "name": channel_id.upper(),
            "url": link
        })

    # M3U Dosyası Oluştur
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(f'#EXTINF:-1,Avva | {ch["name"]}\n')
            f.write(f'{ch["url"]}\n')

    print(f"✅ Bitti! {len(channels)} kanal playlist.m3u dosyasına yazıldı.")

if __name__ == "__main__":
    scrape_avva()
