import json
import time
from playwright.sync_api import sync_playwright

URL = "https://avvasportshd1.com/channels.html"

def debug_scrape():
    all_requests = []
    all_responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Tüm istekleri kaydet
        def on_request(request):
            all_requests.append({
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "post_data": request.post_data
            })
            print(f"📤 İstek: {request.method} {request.url}")

        # Tüm cevapları kaydet
        def on_response(response):
            all_responses.append({
                "url": response.url,
                "status": response.status,
                "headers": dict(response.headers)
            })
            # m3u8, json, php gibi önemli cevapları işaretle
            url = response.url.lower()
            if any(x in url for x in [".m3u8", ".json", ".php", "stream", "play", "token", "get", "api", "channel", "live"]):
                print(f"⭐ ÖNEMLİ CEVAP: {response.status} {response.url}")

        page.on("request", on_request)
        page.on("response", on_response)

        # Ana sayfayı yükle
        print("🌐 Ana sayfa yükleniyor...")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        # Sayfadaki HTML'i kaydet
        html_content = page.content()
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("💾 Sayfa kaynağı page_source.html'e kaydedildi")

        # Kanal satırlarını bul
        rows = page.locator("div.ch-row")
        count = rows.count()
        print(f"\n📡 {count} kanal satırı bulundu. İlk 3 kanala tıklanıyor...\n")

        # İlk 3 kanala tıkla ve trafiği izle
        for i in range(min(3, count)):
            print(f"\n{'='*50}")
            print(f"🖱️ {i+1}. kanala tıklanıyor...")
            
            # Tıklamadan önceki istek sayısı
            before_count = len(all_requests)
            
            try:
                rows.nth(i).click()
                # Tıklama sonrası yüklenmesi için bekle
                page.wait_for_timeout(8000)
                
                # Tıklama sonrası gelen yeni istekleri göster
                new_requests = all_requests[before_count:]
                print(f"📊 Tıklama sonrası {len(new_requests)} yeni istek:")
                for req in new_requests:
                    print(f"   ➡️ {req['method']} {req['url']}")
                    if req['post_data']:
                        print(f"      📦 POST Data: {req['post_data']}")
                        
            except Exception as e:
                print(f"❌ Tıklama hatası: {e}")

        # JavaScript değişkenlerini çek
        print("\n🔍 JavaScript değişkenleri aranıyor...")
        try:
            js_vars = page.evaluate("""
                () => {
                    let results = {};
                    
                    // window objesindeki değişkenleri tara
                    for (let key in window) {
                        try {
                            let val = window[key];
                            let str = JSON.stringify(val);
                            if (str && (
                                str.includes('m3u8') || 
                                str.includes('stream') || 
                                str.includes('token') ||
                                str.includes('channel') ||
                                str.includes('.php')
                            )) {
                                results[key] = val;
                            }
                        } catch(e) {}
                    }
                    return results;
                }
            """)
            
            if js_vars:
                print(f"✅ İlgili JS değişkenleri bulundu:")
                print(json.dumps(js_vars, indent=2, ensure_ascii=False))
            else:
                print("⚠️ İlgili JS değişkeni bulunamadı")
                
        except Exception as e:
            print(f"❌ JS değişken hatası: {e}")

        # Sayfadaki inline scriptleri kaydet
        print("\n📜 Inline scriptler aranıyor...")
        try:
            scripts = page.evaluate("""
                () => {
                    let scripts = [];
                    document.querySelectorAll('script:not([src])').forEach(s => {
                        if (s.innerHTML.length > 10) {
                            scripts.push(s.innerHTML);
                        }
                    });
                    return scripts;
                }
            """)
            
            with open("scripts.txt", "w", encoding="utf-8") as f:
                for idx, script in enumerate(scripts):
                    f.write(f"\n\n{'='*50}\n")
                    f.write(f"SCRIPT #{idx+1}\n")
                    f.write(f"{'='*50}\n")
                    f.write(script)
            print(f"💾 {len(scripts)} script, scripts.txt'e kaydedildi")
            
        except Exception as e:
            print(f"❌ Script hatası: {e}")

        browser.close()

    # Tüm istekleri kaydet
    with open("all_requests.json", "w", encoding="utf-8") as f:
        json.dump(all_requests, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Toplam {len(all_requests)} istek all_requests.json'a kaydedildi")

    # Önemli istekleri filtrele ve göster
    print("\n🎯 ÖNEMLİ İSTEKLER:")
    keywords = ["m3u8", "stream", "play", "token", "api", "channel", "live", ".php", "get"]
    important = [r for r in all_requests if any(k in r["url"].lower() for k in keywords)]
    
    for req in important:
        print(f"\n{'='*50}")
        print(f"URL    : {req['url']}")
        print(f"Method : {req['method']}")
        if req['post_data']:
            print(f"POST   : {req['post_data']}")

    with open("important_requests.json", "w", encoding="utf-8") as f:
        json.dump(important, f, ensure_ascii=False, indent=2)
    print(f"\n💾 {len(important)} önemli istek important_requests.json'a kaydedildi")


if __name__ == "__main__":
    debug_scrape()
