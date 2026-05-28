"""
Mevcut M3U playlist dosyasını okur, belirtilen kaynaktan
Tivibu Spor yayın adresini çeker ve playlist içindeki
ilgili girişi günceller veya yoksa ekler.
Diğer kanallara dokunulmaz.

Kullanım:
    python update_playlist.py <kaynak_m3u8> [playlist_dosyası]
Varsayılan playlist: playlist.m3u
"""

import sys
import requests
import os
from urllib.parse import urljoin

# Kanal bilgisi sabiti
CHANNEL_EXTINF = '#EXTINF:-1 tvg-logo="https://upload.wikimedia.org/wikipedia/tr/3/36/Tivibu_spor_logosu.jpg" group-title="TR Spor",Tivibu Spor'
CHANNEL_NAME = "Tivibu Spor"  # Eşleşme için kullanılacak isim

def get_final_stream_url(initial_url: str) -> str:
    """
    Kaynak m3u8 adresinden nihai yayın bağlantısını çözer.
    """
    session = requests.Session()
    resp = session.get(
        initial_url,
        allow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; GitHubAction)"},
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
    return final_url

def read_playlist(path: str):
    """Playlist dosyasını satır listesi olarak okur, yoksa boş liste döner."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()
    return []

def write_playlist(path: str, lines: list):
    """Playlist'i dosyaya yazar."""
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def update_playlist(existing_lines: list, new_url: str) -> list:
    """
    Mevcut satırlarda Tivibu Spor girişini arar, URL'sini günceller.
    Bulamazsa sona ekler. Başlık (#EXTM3U) kontrolü yapılır.
    """
    # Satırları temizle: her satırın sonundaki newline karakterini koru
    lines = [line if line.endswith('\n') else line + '\n' for line in existing_lines]

    # Başlık kontrolü: ilk satır #EXTM3U değilse ekle
    if not lines or not lines[0].startswith("#EXTM3U"):
        lines.insert(0, "#EXTM3U\n")

    # Tivibu Spor girişini ara
    extinf_index = -1
    for i, line in enumerate(lines):
        if line.startswith("#EXTINF:") and line.rstrip().endswith(f",{CHANNEL_NAME}"):
            extinf_index = i
            break

    if extinf_index != -1:
        # Bu #EXTINF satırından sonraki URL satırını bul ve değiştir
        url_index = None
        for j in range(extinf_index + 1, len(lines)):
            stripped = lines[j].strip()
            if stripped and not stripped.startswith("#"):
                url_index = j
                break
        if url_index is not None:
            lines[url_index] = new_url + '\n'
        else:
            # Eğer URL satırı yoksa hemen altına ekle
            lines.insert(extinf_index + 1, new_url + '\n')
    else:
        # Giriş bulunamadı, sona ekle (mevcut boş satır varsa koru)
        # Sondaki boş satırları temizlemeden ekleyelim
        if lines and not lines[-1].endswith('\n'):
            lines[-1] += '\n'
        lines.append(CHANNEL_EXTINF + '\n')
        lines.append(new_url + '\n')

    return lines

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python update_playlist.py <kaynak_m3u8> [playlist_dosyası]")
        sys.exit(1)

    source_url = sys.argv[1]
    playlist_file = sys.argv[2] if len(sys.argv) > 2 else "playlist.m3u"

    # Yeni yayın adresini al
    new_stream_url = get_final_stream_url(source_url)
    print(f"Yeni yayın adresi: {new_stream_url}")

    # Mevcut playlist'i oku
    existing = read_playlist(playlist_file)

    # Playlist'i güncelle
    updated_lines = update_playlist(existing, new_stream_url)

    # Dosyaya yaz
    write_playlist(playlist_file, updated_lines)
    print(f"'{playlist_file}' güncellendi.")

if __name__ == "__main__":
    main()
