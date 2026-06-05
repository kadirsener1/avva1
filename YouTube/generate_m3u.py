import os
import re
import html
import unicodedata
import requests

CHANNELS_FILE = os.getenv("CHANNELS_FILE", "YouTube/channels.txt")
PLAYLIST_FILE = os.getenv("PLAYLIST_FILE", "playlist.m3u")

# Hedef playlist kaynağı olarak avva repo kullanılır
PLAYLIST_SOURCE_URLS = [
    os.getenv("PLAYLIST_SOURCE_URL", "https://raw.githubusercontent.com/kadirsener1/avva/main/playlist.m3u"),
    "https://raw.githubusercontent.com/kadirsener1/avva/refs/heads/main/playlist.m3u",
]

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0 Safari/537.36"
}


def tr_ascii(text: str) -> str:
    table = str.maketrans({
        "ç": "c", "Ç": "c",
        "ğ": "g", "Ğ": "g",
        "ı": "i", "İ": "i",
        "ö": "o", "Ö": "o",
        "ş": "s", "Ş": "s",
        "ü": "u", "Ü": "u",
    })
    return text.translate(table)


def compact_key(text: str) -> str:
    if not text:
        return ""

    text = html.unescape(text).strip().casefold()
    text = tr_ascii(text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def alias_keys(text: str) -> set:
    base = compact_key(text)
    keys = set()

    if not base:
        return keys

    keys.add(base)

    stripped = base
    for token in ["youtube", "ytube", "live", "canli"]:
        stripped = stripped.replace(token, "")

    if stripped and len(stripped) >= 3:
        keys.add(stripped)

    stripped2 = re.sub(r"(youtube|ytube|live|canli)+$", "", base)
    if stripped2 and len(stripped2) >= 3:
        keys.add(stripped2)

    return keys


def extract_attr(extinf_line: str, attr_name: str) -> str:
    match = re.search(rf'{re.escape(attr_name)}="([^"]*)"', extinf_line, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def load_target_playlist():
    # Önce yerelde hedef repo içindeki playlist varsa onu kullan
    if os.path.exists(PLAYLIST_FILE):
        with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]

        if not lines or not lines[0].startswith("#EXTM3U"):
            lines.insert(0, "#EXTM3U")

        print(f"📂 Yerel hedef playlist kullanıldı: {PLAYLIST_FILE}")
        return lines

    # Yerelde yoksa raw URL'den al
    for url in PLAYLIST_SOURCE_URLS:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            if resp.status_code == 200 and resp.text.strip():
                lines = [line.rstrip("\n") for line in resp.text.splitlines()]
                if not lines or not lines[0].startswith("#EXTM3U"):
                    lines.insert(0, "#EXTM3U")
                print(f"📥 Playlist kaynağı yüklendi: {url}")
                return lines
        except Exception as e:
            print(f"⚠️ Raw playlist alınamadı: {url} -> {e}")

    print("⚠️ Hedef playlist bulunamadı, yeni liste başlatılıyor.")
    return ["#EXTM3U"]


def build_playlist_entries(lines):
    entries = []
    key_index = {}

    for i, line in enumerate(lines):
        if not line.startswith("#EXTINF"):
            continue

        parts = line.split(",", 1)
        display_name = parts[1].strip() if len(parts) == 2 else ""

        tvg_name = extract_attr(line, "tvg-name")
        tvg_id = extract_attr(line, "tvg-id")

        url_idx = None
        for j in range(i + 1, len(lines)):
            candidate = lines[j].strip()
            if not candidate:
                continue
            if candidate.startswith("#"):
                continue
            url_idx = j
            break

        if url_idx is None:
            continue

        names = [display_name, tvg_name, tvg_id]
        keys = set()
        for name in names:
            keys.update(alias_keys(name))

        entry = {
            "extinf_idx": i,
            "url_idx": url_idx,
            "display_name": display_name,
            "tvg_name": tvg_name,
            "tvg_id": tvg_id,
            "keys": keys,
        }

        entry_idx = len(entries)
        entries.append(entry)

        for key in keys:
            key_index.setdefault(key, []).append(entry_idx)

    print(f"📋 Playlist içinden {len(entries)} kanal indexlendi.")
    return entries, key_index


def parse_channel_line(line: str):
    if "," in line:
        name_part, channel_part = line.split(",", 1)
        return name_part.strip(), channel_part.strip()
    return None, line.strip()


def to_youtube_url(channel: str) -> str:
    channel = channel.strip()

    if channel.startswith("http://") or channel.startswith("https://"):
        return channel.rstrip("/")

    if channel.startswith("@"):
        return f"https://www.youtube.com/{channel}"

    return f"https://www.youtube.com/channel/{channel}"


def to_mobile_live_url(channel: str) -> str:
    url = to_youtube_url(channel)
    url = re.sub(r"^https?://(www\.)?youtube\.com", "https://m.youtube.com", url)
    url = re.sub(r"^https?://youtu\.be", "https://m.youtube.com", url)

    if not url.endswith("/live"):
        url += "/live"

    return url


def get_channel_title(channel: str) -> str:
    youtube_url = to_youtube_url(channel)
    oembed_url = (
        "https://www.youtube.com/oembed?url="
        + requests.utils.quote(youtube_url, safe=":/?=&@")
        + "&format=json"
    )

    try:
        resp = requests.get(
            oembed_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return (data.get("title") or "").strip()
    except Exception:
        pass

    return ""


def get_ytdlp_session():
    try:
        sess = requests.Session()
        sess.headers.update(HEADERS)

        home_resp = sess.get("https://ytdlp.online/tr/", timeout=20)

        session_cookie = sess.cookies.get("session") or home_resp.cookies.get("session")
        if session_cookie:
            return session_cookie

        set_cookie = home_resp.headers.get("set-cookie", "")
        match = re.search(r"session=([^;]+)", set_cookie)
        if match:
            return match.group(1)

    except Exception as e:
        print(f"Session alınamadı: {e}")

    return None


def find_playlist_entry(candidate_names, entries, key_index):
    tried_keys = set()
    direct_hits = set()

    for name in candidate_names:
        for key in alias_keys(name):
            tried_keys.add(key)
            if key in key_index:
                ids = key_index[key]
                if len(ids) == 1:
                    return ids[0], "exact"
                direct_hits.update(ids)

    if len(direct_hits) == 1:
        return next(iter(direct_hits)), "exact-multi"

    fuzzy_hits = set()

    for idx, entry in enumerate(entries):
        for tkey in tried_keys:
            if not tkey or len(tkey) < 4:
                continue
            for ekey in entry["keys"]:
                if not ekey:
                    continue
                if tkey in ekey or ekey in tkey:
                    fuzzy_hits.add(idx)
                    break
            if idx in fuzzy_hits:
                break

    if len(fuzzy_hits) == 1:
        return next(iter(fuzzy_hits)), "fuzzy"

    return None, None


def get_manifest_url(channel: str, session_cookie: str):
    live_url = to_mobile_live_url(channel)
    command = f"--get-url {live_url}"
    api_url = "https://ytdlp.online/api/v1/stream?command=" + requests.utils.quote(command, safe="")

    stream_headers = {
        "accept": "text/event-stream",
        "cookie": f"session={session_cookie}",
        "referer": "https://ytdlp.online/tr/",
        "user-agent": HEADERS["user-agent"]
    }

    resp = requests.get(api_url, headers=stream_headers, timeout=30)
    text = resp.text

    match = re.search(r'https://manifest\.googlevideo\.com/[^\s"\'<>\\]+', text)
    return match.group(0) if match else None


with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
    raw_lines = [line.strip() for line in f if line.strip()]

playlist_lines = load_target_playlist()
entries, key_index = build_playlist_entries(playlist_lines)

session_cookie = get_ytdlp_session()
if not session_cookie:
    print("Session bulunamadı, çıkılıyor.")
    raise SystemExit(1)

updated = 0
skipped = 0
not_live = 0
errors = 0

for raw_line in raw_lines:
    given_name, channel = parse_channel_line(raw_line)

    candidate_names = []
    if given_name:
        candidate_names.append(given_name)

    yt_title = get_channel_title(channel)
    if yt_title and compact_key(yt_title) not in {compact_key(x) for x in candidate_names}:
        candidate_names.append(yt_title)

    fallback_name = channel.rstrip("/").split("/")[-1]
    if fallback_name and compact_key(fallback_name) not in {compact_key(x) for x in candidate_names}:
        candidate_names.append(fallback_name)

    entry_idx, match_type = find_playlist_entry(candidate_names, entries, key_index)

    if entry_idx is None:
        skipped += 1
        shown = " / ".join(candidate_names) if candidate_names else channel
        print(f"⏭️ {shown} → playlist içinde bulunamadı, dokunulmadı")
        continue

    entry = entries[entry_idx]
    playlist_name = entry["display_name"] or entry["tvg_name"] or entry["tvg_id"] or "(isimsiz)"

    try:
        manifest_url = get_manifest_url(channel, session_cookie)

        if not manifest_url:
            not_live += 1
            print(f"⚠️ {playlist_name} → canlı yayın bulunamadı, mevcut kayıt korunuyor")
            continue

        url_idx = entry["url_idx"]
        old_url = playlist_lines[url_idx]
        playlist_lines[url_idx] = manifest_url

        updated += 1
        if old_url != manifest_url:
            print(f"✅ {playlist_name} → link güncellendi ({match_type})")
        else:
            print(f"✅ {playlist_name} → link zaten güncel ({match_type})")

    except Exception as e:
        errors += 1
        print(f"❌ {playlist_name} → hata: {e}")

output_dir = os.path.dirname(os.path.abspath(PLAYLIST_FILE))
os.makedirs(output_dir, exist_ok=True)

with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(playlist_lines) + "\n")

print(
    f"\n🎯 Güncellenen: {updated} | "
    f"Listede bulunamadı: {skipped} | "
    f"Canlı değil: {not_live} | "
    f"Hata: {errors} | "
    f"Dosya: {PLAYLIST_FILE}"
)
