import time
import uuid
from datetime import datetime
from playwright.sync_api import sync_playwright


def scrape_ads(modell, min_price=0, max_price=1500, nur_versand=False, nur_angebote=True, debug=False, config=None, log=None):
    if config is None:
        config = {
            "verkaufspreis": 600,
            "wunsch_marge": 100,
            "reparaturkosten": {}
        }

    if log is None:
        def log(x): pass  # Fallback-Logfunktion, falls keine übergeben wurde

    base_url = "https://www.kleinanzeigen.de/s-anzeige:angebote"
    if not nur_angebote:
        base_url = "https://www.kleinanzeigen.de/s-anzeige"  # schließt Gesuche mit ein

    suchbegriff = modell.replace(" ", "-")
    url = f"{base_url}/{suchbegriff}/k0"
    url += f"?price={min_price}:{max_price}"
    if nur_versand:
        url += "&shipping=1"

    log(f"[🔍] Starte Suche unter: {url}")

    new_ads = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)

        # Alle Anzeigen auf der Ergebnisseite sammeln
        eintraege = page.locator("li.aditem")

        count = eintraege.count()
        log(f"[📄] {count} Anzeigen gefunden.")

        for i in range(count):
            try:
                entry = eintraege.nth(i)
                title = entry.locator("a.ellipsis").inner_text().strip()
                price_text = entry.locator(".aditem-main--middle .aditem-main--middle--price").inner_text()
                price = int(price_text.replace("€", "").replace(".", "").replace(",", "").strip())

                link = entry.locator("a.ellipsis").get_attribute("href")
                if not link.startswith("https"):
                    link = "https://www.kleinanzeigen.de" + link

                image = entry.locator("img").get_attribute("src") or ""

                versand = "versand möglich" in entry.inner_text().lower()

                # Detailseite laden
                detail_page = context.new_page()
                detail_page.goto(link, timeout=60000)
                detail_page.wait_for_timeout(3000)

                beschreibung = detail_page.locator("div[data-testid='description']").inner_text(timeout=3000)
                detail_page.close()

                rep_summe = 0
                for defekt, kosten in config["reparaturkosten"].items():
                    if defekt.lower() in beschreibung.lower():
                        rep_summe += kosten

                max_ek = config["verkaufspreis"] - config["wunsch_marge"] - rep_summe

                log(f"📦 {title} | {price} € | Versand: {versand} | Max EK: {max_ek} €")

                new_ads.append({
                    "id": str(uuid.uuid5(uuid.NAMESPACE_URL, link)),
                    "modell": modell,
                    "title": title,
                    "price": price,
                    "link": link,
                    "image": image,
                    "versand": versand,
                    "beschreibung": beschreibung,
                    "reparaturkosten": rep_summe,
                    "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "updated_at": datetime.now().strftime("%d.%m.%Y %H:%M")
                })

                if debug:
                    time.sleep(1)

            except Exception as e:
                log(f"[⚠️] Fehler bei Anzeige {i+1}: {e}")

        browser.close()

    return new_ads
