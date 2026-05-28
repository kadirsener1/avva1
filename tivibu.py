import requests
import datetime

# Yeni verdiğin kaynak linki
SOURCE_URL = "https://streams.uzunmuhalefet.com/stream/e47153e0-42fe-4980-8570-e840d1cc1cf4.m3u8"
M3U_FILE = "tivibuspor.m3u"

def check_and_get_link():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://uzunmuhalefet.com/",
        "Origin": "https://uzunmuhalefet.com"
    }

    try:
        # Linkin hala aktif olup olmadığını kontrol et
        response = requests.get(SOURCE_URL, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print("✅ Yayın Aktif!")
            return SOURCE_URL
        else:
            print(f"❌ Yayın Hatası: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Bağlantı Hatası: {e}")
        return None

def main():
    working_link = check_and_get_link()
    
    # M3U Dosyasını Oluştur
    with open(M3U_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#EXTINF:-1 tvg-id=\"TivibuSpor\" tvg-logo=\"https://upload.wikimedia.org/wikipedia/tr/d/d2/Tivibu_Spor_logo.png\", Tivibu Spor\n")
        if working_link:
            f.write(working_link)
        else:
            # Eğer link bozulursa, ileride buraya otomatik yeni link bulma fonksiyonu eklenebilir
            f.write("https://raw.githubusercontent.com/KULLANICI_ADIN/REPOS_ADIN/main/error.m3u8")

    print(f"🚀 {M3U_FILE} başarıyla güncellendi.")

if __name__ == "__main__":
    main()
