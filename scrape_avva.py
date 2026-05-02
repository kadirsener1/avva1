import json
from datetime import datetime
from playwright.sync_api import sync_playwright

URL = "https://avvasportshd1.com/channels.html"

def scrape_channels():
    channels = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        rows = page.locator("div.ch-row")
        count = rows.count()

        print(f"Bulunan kanal satırı: {count}")

        for i in range(count):
            row = rows.nth(i)
            ch_id = row.get_attribute("data-id")

            name = ""
            name_locator = row.locator(".ch-name")
            if name_locator.count() > 0:
                name = name_locator.first.inner_text().strip()

            channels.append({
                "id": ch_id,
                "name": name
            })

        browser.close()

    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.now().isoformat(),
            "channels": channels
        }, f, ensure_ascii=False, indent=2)

    print(f"Toplam {len(channels)} kanal kaydedildi.")

if __name__ == "__main__":
    scrape_channels()
