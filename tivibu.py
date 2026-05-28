import requests
import datetime
import os

BASE_URL = "http://50.7.144.122:1935/live/tivibuspor.stream/playlist.m3u8"
OUTPUT_FILE = "tivibuspor_live.txt"
M3U_FILE = "tivibuspor.m3u"

def is_working(url):
    try:
        headers = {
            "User-Agent": "IPTV Smarters/1.0 (Linux; Android 10)",
            "Referer": "http://50.7.144.122/",
            "Origin": "http://50.7.144.122"
        }
        r = requests.get(url, headers=headers, timeout=12, stream=True)
        return r.status_code == 200 and len(r.content) > 500
    except:
        return False

def try_link(url):
    if is_working(url):
        print(f"✅ ÇALIŞIYOR: {url}")
        return url
    return None

def main():
    print(f"\n🔄 Tivibuspor Link Güncelleyici - {datetime.datetime.now()}")
    
    urls_to_try = [
        BASE_URL,
        BASE_URL + "?hash=8a1926764081c85cf38943c0c0d1f9d6",
        BASE_URL + "?token=free",
        BASE_URL + "?key=live",
    ]
    
    working_url = None
    
    for url in urls_to_try:
        result = try_link(url)
        if result:
            working_url = result
            break

    if not working_url:
        print("❌ Şu anda çalışan link bulunamadı.")
        working_url = "Şu anda çalışan link bulunamadı."
    
    # Dosyaları kaydet
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(working_url)
    
    with open(M3U_FILE, "w", encoding="utf-8") as f:
        f.write(f"#EXTM3U\n#EXTINF:-1,TiviBuspor\n{working_url}")
    
    print(f"💾 Güncel link kaydedildi → {M3U_FILE}")

if __name__ == "__main__":
    main()
