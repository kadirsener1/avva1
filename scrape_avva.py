import time
import re
from playwright.sync_api import sync_playwright

def scrape_avva():
    print("🚀 İşlem başlatıldı. Kanallar taranıyor...")
    
    found_channels = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Gerçek bir kullanıcı gibi davranmak için User-Agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # 1. Ana sayfadaki kanal listesini al
        try:
            page.goto("https://avvasportshd1.com/channels.html", wait_until="networkidle", timeout=60000)
            # Sayfadaki tüm href linklerini topla
            links = page.query_selector_all("a[href*='play.html?ch=']")
            hrefs = [link.get_attribute("href") for link in links]
            # Tekrar edenleri temizle
            hrefs = list(set(hrefs))
            print(f"📡 {len(hrefs)} adet kanal linki tespit edildi. İçerikler alınıyor...")
        except Exception as e:
            print(f"❌ Ana sayfa yüklenemedi: {e}")
            browser.close()
            return

        # 2. Her kanal sayfasını tek tek gez ve m3u8 yakala
        for href in hrefs:
            # Tam URL'yi oluştur
            target_url = f"https://avvasportshd1.com/{href}"
            ch_name = href.split("ch=")[-1].upper()
            
            print(f"🔍 Taranıyor: {ch_name}...")
            
            current_m3u8 = None

            # Ağ trafiğini dinleyen fonksiyon
            def intercept_m3u8(request):
                nonlocal current_m3u8
                if ".m3u8" in request.url and "avvaupdate" in request.url:
                    current_m3u8 = request.url

            page.on("request", intercept_m3u8)
            
            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                # m3u8'in yüklenmesi için kısa bir süre bekle (oynatıcı yüklenmeli)
                time.sleep(5) 
                
                if current_m3u8:
                    found_channels.append({"name": ch_name, "url": current_m3u8})
                    print(f"✅ Bulundu: {ch_name}")
                else:
                    print(f"⚠️ Link bulunamadı: {ch_name}")
                    
            except Exception as e:
                print(f"❌ {ch_name} taranırken hata: {e}")
            
            # Dinleyiciyi temizle
            page.remove_listener("request", intercept_m3u8)

        browser.close()

    # 3. M3U Dosyasını Kaydet
    if found_channels:
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"# Son Güncelleme: {time.ctime()}\n\n")
            for ch in found_channels:
                f.write(f'#EXTINF:-1,Avva | {ch["name"]}\n')
                f.write(f'{ch["url"]}\n\n')
        print(f"🎉 Bitti! playlist.m3u dosyasına {len(found_channels)} kanal eklendi.")
    else:
        print("😭 Hiçbir kanal linki toplanamadı.")

if __name__ == "__main__":
    scrape_avva()
