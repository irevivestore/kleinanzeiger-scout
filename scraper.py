# scraper.py
import re
import time
import uuid
import json
from datetime import datetime
from urllib.parse import quote, urljoin
from playwright.sync_api import sync_playwright
import db  # Dein Datenbankmodul

def build_kleinanzeigen_url(
    modell: str,
    min_price: int = 0,
    max_price: int = 1500,
    nur_versand: bool = False,
    nur_angebote: bool = True
) -> str:
    base_url = "https://www.kleinanzeigen.de"

    # Kategorie immer handy-telekom
    kategorie = "handy-telekom"

    # s oder s-anzeige:angebote
    if nur_angebote:
        search_type = "s-anzeige:angebote"
    else:
        search_type = "s"

    # Preisfilter
    preis_filter = f"preis:{min_price}:{max_price}"

    # Modell (URL-encoded, Bindestriche statt Leerzeichen)
    modell_encoded = quote(modell.lower().replace(" ", "-"))

    # Filter, immer "only_device" und ggf. Versandfilter
    filter_parts = ["handy_telekom.device_equipment_s:only_device"]
    if nur_versand:
        filter_parts.append("handy_telekom.versand_s:ja")

    filter_string = "+".join(filter_parts)

    # k0c173 steht für weitere Filter/Kategorien (laut deinem Beispiel)
    filter_section = f"k0c173+{filter_string}"

    url = f"{base_url}/{search_type}-{kategorie}/{preis_filter}/{modell_encoded}/{filter_section}"
    return url


def scrape_kleinanzeigen(
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

    url = build_kleinanzeigen_url(modell, min_price, max_price, nur_versand, nur_angebote)
    log(f"[🔍] Starte Suche unter: {url}")

    bestehende_ids = db.get_all_ad_ids_for_model(modell, include_archived=True)
    log(f"[ℹ️] Bereits {len(bestehende_ids)} Anzeigen (inkl. archiviert) in DB.")

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
            try:
                page.wait_for_selector("article.aditem", timeout=5000)
                eintraege = page.locator("article.aditem")
                log("[✅] Fallback-Selektor verwendet: article.aditem")
            except:
                log("[❌] Kein Anzeigenselektor gefunden.")
                browser.close()
                return []

        count = min(eintraege.count(), 5)
        log(f"[📄] {count} Anzeigen gefunden.")

        for i in range(count):
            try:
                entry = eintraege.nth(i)
                ad_id = entry.get_attribute("data-adid") or str(uuid.uuid5(uuid.NAMESPACE_URL, entry.get_attribute("data-custom-href") or ""))

                if ad_id in bestehende_ids:
                    log(f"[⏭️] Anzeige {ad_id} bereits in DB, übersprungen.")
                    continue

                custom_href = entry.get_attribute("data-custom-href")
                if not custom_href or not custom_href.startswith("/s-anzeige/"):
                    href = entry.locator("a").first.get_attribute("href")
                    if href and href.startswith("/s-anzeige/"):
                        custom_href = href

                if not custom_href or not custom_href.startswith("/s-anzeige/"):
                    log(f"[⚠️] Anzeige {i+1} übersprungen: Kein gültiger Link.")
                    continue

                full_link = urljoin("https://www.kleinanzeigen.de", custom_href)

                title_el = entry.locator("h2 a")
                title = title_el.inner_text().strip() if title_el else "Unbekannter Titel"

                preis_el = entry.locator(".aditem-main--middle--price-shipping--price")
                preis_text = preis_el.inner_text().strip() if preis_el else ""
                preis_text = preis_text.replace("€", "").replace(".", "").replace(",", "").strip()
                try:
                    price = int(re.findall(r"\d+", preis_text)[0])
                except (IndexError, ValueError):
                    price = 0

                detail_page = context.new_page()
                detail_page.goto(full_link, timeout=60000)
                detail_page.wait_for_timeout(2000)  # Warten auf Bild-Ladezeit

                images = []
                try:
                    detail_page.wait_for_selector("div.galleryimage-element img", timeout=5000)
                    img_elements = detail_page.locator("div.galleryimage-element img")
                    count_images = img_elements.count()

                    for j in range(count_images):
                        img_src = img_elements.nth(j).get_attribute("src")
                        if img_src and img_src not in images:
                            images.append(img_src)
                    log(f"[🖼️] {len(images)} Bilder erfolgreich geladen.")
                except Exception as e:
                    log(f"[⚠️] Fehler beim Sammeln der Bilder: {e}")

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

                ad_data = {
                    "id": ad_id,
                    "modell": modell,
                    "title": title,
                    "price": price,
                    "link": full_link,
                    "image": images[0] if images else "",
                    "bilder_liste": images,
                    "versand": nur_versand,
                    "beschreibung": beschreibung,
                    "reparaturkosten": rep_summe,
                    "bewertung": bewertung,
                    "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "updated_at": datetime.now().strftime("%d.%m.%Y %H:%M")
                }

                db.save_advert(ad_data)
                anzeigen.append(ad_data)

                if debug:
                    time.sleep(1)

            except Exception as e:
                log(f"[❌] Fehler bei Anzeige {i+1}: {e}")
                continue

        browser.close()

    return anzeigen
