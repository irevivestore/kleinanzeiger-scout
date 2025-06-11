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
    debug=True,
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
        def log(x): print(x)

    base_url = "https://www.kleinanzeigen.de"
    kategorie = "handy-telekom" if nur_versand else ""

    pfadteile = []
    if nur_angebote:
        pfadteile.append("s-anzeige:angebote")
    else:
        pfadteile.append("s")

    if kategorie:
        pfadteile.append(f"-{kategorie}")
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

        try:
            page.wait_for_selector("article[data-testid='ad-list-item']", timeout=5000)
            eintraege = page.locator("article[data-testid='ad-list-item']")
        except:
            log("[ℹ️] Neuer Selektor funktioniert nicht, versuche Fallback 'article.aditem'")
            try:
                page.wait_for_selector("article.aditem", timeout=5000)
                eintraege = page.locator("article.aditem")
                log("[✅] Fallback-Selektor verwendet: article.aditem")
            except:
                log("[❌] Kein bekannter Anzeigenselektor gefunden.")
                html_debug = page.inner_html("body")
                with open("debug_kleinanzeigen.html", "w", encoding="utf-8") as f:
                    f.write(html_debug)
                log("[📝] HTML gespeichert in debug_kleinanzeigen.html")
                browser.close()
                return []

        count = eintraege.count()
        log(f"[📄] {count} Anzeigen gefunden.")

        # Für Tests: Nur die ersten 5 Anzeigen verarbeiten
        count = min(count, 5)

        for i in range(count):
            try:
                entry = eintraege.nth(i)
                ad_id = entry.get_attribute("data-adid")

                custom_href = entry.get_attribute("data-custom-href")
                if not custom_href or not custom_href.startswith("/s-anzeige/"):
                    href = entry.locator("a").first.get_attribute("href")
                    if href and href.startswith("/s-anzeige/"):
                        custom_href = href

                if not custom_href or not custom_href.startswith("/s-anzeige/"):
                    log(f"[⚠️] Anzeige {i+1} übersprungen: Kein gültiger Link.")
                    continue

                full_link = urljoin(base_url, custom_href)

                title_el = entry.locator("h2 a")
                title = title_el.inner_text().strip() if title_el else "Unbekannter Titel"

                preis_el = entry.locator(".aditem-main--middle--price-shipping--price")
                preis_text = preis_el.inner_text().strip() if preis_el else ""
                preis_text = preis_text.replace("€", "").replace(".", "").replace(",", "").strip()
                try:
                    price = int(re.findall(r"\d+", preis_text)[0])
                except (IndexError, ValueError):
                    log(f"[⚠️] Preis konnte nicht gelesen werden bei Anzeige {i+1}: '{preis_text}'")
                    price = 0

                image_el = entry.locator("img")
                image_url = image_el.get_attribute("src") if image_el else ""

                # Detailseite öffnen
                detail_page = context.new_page()
                detail_page.goto(full_link, timeout=60000)
                detail_page.wait_for_timeout(3000)

                beschreibung = ""
                selectors = [
                    "div[data-testid='ad-detail-description']",
                    "p[itemprop='description']",
                    "section[data-testid='description']",
                    "div[itemprop='description']"
                ]

                for sel in selectors:
                    try:
                        detail_page.wait_for_selector(sel, timeout=3000)
                        beschreibung_el = detail_page.locator(sel)
                        if beschreibung_el.count() > 0:
                            beschreibung = beschreibung_el.first.inner_text().strip()
                            if beschreibung:
                                break
                    except:
                        continue

                if not beschreibung:
                    try:
                        body_text = detail_page.locator("body").inner_text()
                        match = re.search(r"(Beschreibung|Details|Zustand):\s*(.+)", body_text, re.IGNORECASE)
                        if match:
                            beschreibung = match.group(2).strip()
                    except:
                        pass

                detail_page.close()

                log(f"[📝] Beschreibung: {beschreibung[:100]}...")

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

                log(f"[📦] {title} | {price} € | Max EK: {max_ek} € | Bewertung: {bewertung}")

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
                log(f"[❌] Fehler bei Anzeige {i+1}: {e}")
                continue

        browser.close()

    return anzeigen
