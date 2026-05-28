"""
Verilen ilk m3u8 adresinden nihai yayın linkini çözer ve bir dosyaya yazar.
Kullanım:
    python find_stream.py <ilk_m3u8_url> [çıktı_dosyası]
Varsayılan çıktı: sonuc.m3u8
"""

import sys
import requests
from urllib.parse import urljoin

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
    output_file = sys.argv[2] if len(sys.argv) > 2 else "sonuc.m3u8"

    final_url = get_final_stream_url(url)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_url)

    print(f"Nihai yayın adresi '{output_file}' dosyasına yazıldı:")
    print(final_url)

if __name__ == "__main__":
    main()
