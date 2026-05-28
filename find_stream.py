"""
Verilen ilk m3u8 adresinden nihai yayın linkini çözer ve
belirtilen formatta bir M3U playlist dosyası oluşturur.

Kullanım:
    python find_stream.py <ilk_m3u8_url> [çıktı_dosyası]

Varsayılan çıktı: playlist.m3u
"""

import sys
import requests
from urllib.parse import urljoin

# Sabit playlist başlık bilgileri
PLAYLIST_HEADER = "#EXTM3U\n"
CHANNEL_INFO = '#EXTINF:-1 tvg-logo="https://upload.wikimedia.org/wikipedia/tr/3/36/Tivibu_spor_logosu.jpg" group-title="TR Spor",Tivibu Spor\n'

def get_final_stream_url(initial_url: str) -> str:
    """
    - Yönlendirmeleri takip eder.
    - Eğer dönen içerik bir master playlist ise (#EXT-X-STREAM-INF),
      ilk alternatifin mutlak adresini döndürür.
    - Aksi takdirde son URL'yi döndürür.
    """
    session = requests.Session()
    resp = session.get(
        initial_url,
        allow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; GitHubAction)"
        },
        timeout=15
    )
    final_url = resp.url
    content_type = resp.headers.get("Content-Type", "").lower()

    if "mpegurl" in content_type or final_url.endswith(".m3u8"):
        lines = resp.text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("#EXT-X-STREAM-INF"):
                for j in range(i + 1, len(lines)):
                    candidate = lines[j].strip()
                    if candidate and not candidate.startswith("#"):
                        return urljoin(final_url, candidate)
        return final_url
    else:
        return final_url

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python find_stream.py <m3u8_url> [çıktı_dosyası]")
        sys.exit(1)

    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "playlist.m3u"

    final_url = get_final_stream_url(url)

    # M3U playlist içeriğini oluştur
    playlist_content = PLAYLIST_HEADER + CHANNEL_INFO + final_url

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(playlist_content)

    print(f"Playlist dosyası '{output_file}' oluşturuldu:")
    print(playlist_content)

if __name__ == "__main__":
    main()
