import re
import time
import uuid
from datetime import datetime
from urllib.parse import quote, urljoin
from playwright.sync_api import sync_playwright


def scrape_ads(
    modell,
    min_price=0,
    max_price=1500,
    nur_versand=False,
    nur_angebote=True,
    debug=False,
    config=None,
    log=None
):
    if config is None:
        config = {
            "verkaufspreis": 600,
            "wunsch_marge": 100,
            "reparaturkosten": {}
        }

    if log is None:
        def log(x): pass  # Fallback-Logger

    base_url = "https://www.kleinanzeigen.de"
    kategorie = "handy-telekom" if nur_versand else ""

    pfadteile = ["s"]
    if kategorie:
        pfadteile.append(f"-{kategorie}")
    if nur_angebote:
        pfadteile.append("anzeige:angebote")
    pfadteile.append(f"preis:{min_price}:{max_price}")
    pfadteile.append(quote(modell))
    pfadteile.append("k0")

    url = f"{base_url}/{'/'.join(pfadteile)}"
    if nur_versand:
        url += "c173+handy_telekom.versand_s:ja"

    log(f"[🔍] Starte Suche unter: {url}")

    anzeigen = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)

        eintraege = page.locator("article.aditem")
        count = eintraege.count()
        log(f"[📄] {count} Anzeigen gefunden.")

        for i in range(count):
            try:
                entry = eintraege.nth(i)

                ad_id = entry.get_attribute("data-adid")
                custom_href = entry.get_attribute("data-custom-href")
                if not custom_href or not custom_href.startswith("/s-anzeige/"):
                    continue

                full_link = urljoin(base_url, custom_href)

                title_el = entry.locator("h2.text-module-begin a")
                title = title_el.inner_text().strip() if title_el else "Unbekannter Titel"

                preis_el = entry.locator(".aditem-main--middle--price-shipping--price")
                preis_text = preis_el.inner_text().strip() if preis_el else ""
                preis_text = preis_text.replace("€", "").replace(".", "").replace(",", "").strip()
                try:
                    price = int(re.findall(r"\d+", preis_text)[0])
                except (IndexError, ValueError):
                    price = 0

                image_el = entry.locator("img")
                image_url = image_el.get_attribute("src") if image_el else ""

                # Detailseite öffnen, um Beschreibung zu laden
                detail_page = context.new_page()
                detail_page.goto(full_link, timeout=60000)
                detail_page.wait_for_timeout(3000)

                try:
                    beschreibung = detail_page.locator("div[data-testid='description']").inner_text(timeout=3000)
                except:
                    beschreibung = ""
                detail_page.close()

                rep_summe = 0
                for defekt, kosten in config["reparaturkosten"].items():
                    if defekt.lower() in beschreibung.lower():
                        rep_summe += kosten

                max_ek = config["verkaufspreis"] - config["wunsch_marge"] - rep_summe

                if price <= max_ek:
                    bewertung = "grün"
                elif price <= max_ek + config["wunsch_marge"] * 0.1:
                    bewertung = "blau"
                else:
                    bewertung = "rot"

                log(f"📦 {title} | {price} € | Max EK: {max_ek} € | Bewertung: {bewertung}")

                anzeigen.append({
                    "id": ad_id or str(uuid.uuid5(uuid.NAMESPACE_URL, full_link)),
                    "modell": modell,
                    "title": title,
                    "price": price,
                    "link": full_link,
                    "image": image_url,
                    "versand": nur_versand,
                    "beschreibung": beschreibung,
                    "reparaturkosten": rep_summe,
                    "bewertung": bewertung,
                    "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "updated_at": datetime.now().strftime("%d.%m.%Y %H:%M")
                })

                if debug:
                    time.sleep(1)

            except Exception as e:
                log(f"[⚠️] Fehler bei Anzeige {i+1}: {e}")
                continue

        browser.close()

    return anzeigen
