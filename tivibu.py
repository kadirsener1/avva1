import requests
import datetime
import re

# Ana yayın adresi
STREAM_URL = "http://50.7.144.122:1935/live/tivibuspor.stream/playlist.m3u8"
# Sunucunun ana adresi (Token alabileceği yer)
BASE_SERVER = "http://50.7.144.122:1935/live/"

def get_live_link():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Referer": "http://tivibu.com.tr/",
        "Origin": "http://50.7.144.122"
    }

    session = requests.Session()
    
    try:
        # 1. Adım: Önce sunucuya bir 'merhaba' diyoruz (Cookie veya Session için)
        session.get(BASE_SERVER, headers=headers, timeout=10)
        
        # 2. Adım: Direkt linki sorgula
        response = session.get(STREAM_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Eğer doğrudan çalışıyorsa
            return STREAM_URL
        
        # 3. Adım: Eğer 403 verirse, sunucunun döndüğü hatanın içindeki hash'i yakalamaya çalış
        # Bazı sunucular 'Missing Hash' diyerek beklenen formatı gösterir
        print(f"Sunucu yanıtı: {response.status_code}. Alternatif aranıyor...")
        
        # Yaygın kullanılan Tivibu hash parametreleri (Deneme yanılma)
        test_params = ["?hash=", "?token=", "?auth=", "?st="]
        for param in test_params:
            test_url = STREAM_URL + param + "demo" # Bazı sunucular demo hash ile yol gösterir
            r = session.get(test_url, headers=headers, timeout=5)
            if r.status_code == 200:
                return test_url

    except Exception as e:
        print(f"Hata oluştu: {e}")
    
    return None

def main():
    link = get_live_link()
    
    if link:
        print(f"✅ ÇALIŞAN LİNK: {link}")
        with open("tivibuspor.m3u", "w") as f:
            f.write(f"#EXTM3U\n#EXTINF:-1,TiviBuspor\n{link}")
    else:
        # Eğer sunucu tamamen kapalıysa yedek bir IPTV panelinden çekmeyi dener
        print("❌ Ana sunucu kapalı. Yedek aranıyor...")
        # Buraya yedek bir IP (örneğin 185.x.x.x gibi) eklenebilir.
        with open("tivibuspor.m3u", "w") as f:
            f.write("#EXTM3U\n#EXTINF:-1,TiviBuspor (KAPALI)\nhttp://0.0.0.0/offline.m3u8")

if __name__ == "__main__":
    main()
