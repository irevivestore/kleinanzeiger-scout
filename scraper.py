from playwright.sync_api import sync_playwright
import re
import time

def scrape_ads(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # auf False setzen für Debug-Fenster
        context = browser.new_context()
        page = context.new_page()

        try:
            # Debug: API-Anfragen loggen
            def log_request(request):
                if "api." in request.url:
                    print(f">> API Request: {request.url}")
            page.on("request", log_request)

            print(f"\n=== Starte Scraping für {modell} ===")
            page.goto(url, wait_until="networkidle", timeout=60000)
            print("✓ Seite geladen")

            # Screenshot zur Kontrolle
            page.screenshot(path="debug_page.png", full_page=True)
            print("✓ Screenshot gespeichert (debug_page.png)")

            # Warte auf Anzeigen
            page.wait_for_selector("article.aditem", timeout=15000)
            ads = page.query_selector_all("article.aditem")
            print(f"ℹ Gefundene Anzeigen: {len(ads)}")

            for index, ad in enumerate(ads[:5]):  # Nur die ersten 5 Anzeigen
                print(f"\n--- Verarbeite Anzeige {index + 1} ---")

                try:
                    # Speichere HTML der Anzeige
                    ad_html = ad.inner_html()
                    with open(f"debug_ad_{index}.html", "w", encoding="utf-8") as f:
                        f.write(ad_html)
                    print(f"✓ HTML gespeichert: debug_ad_{index}.html")

                    # Titel extrahieren
                    title_elem = ad.query_selector("a.ellipsis")
                    title = title_elem.inner_text().strip() if title_elem else "Kein Titel"
                    print(f"ℹ Titel: {title}")

                    # Preis extrahieren
                    price_elem = ad.query_selector("p.aditem-main--middle--price-shipping--price")
                    if not price_elem:
                        print("❌ Preis nicht gefunden – versuche Fallbacks")
                        alt_selectors = [
                            ".aditem-main--middle--price",
                            ".price",
                            "[class*='price']"
                        ]
                        for sel in alt_selectors:
                            try_alt = ad.query_selector(sel)
                            if try_alt:
                                price_elem = try_alt
                                break
                    if price_elem:
                        raw_price = price_elem.inner_text().strip()
                        print(f"ℹ Rohpreis: '{raw_price}'")
                        price_clean = re.sub(r"[^\d,.]", "", raw_price).replace(",", ".")
                        try:
                            price = float(price_clean)
                            print(f"✓ Preis extrahiert: {price}€")
                        except ValueError:
                            price = 0.0
                            print("❌ Fehler beim Umwandeln")
                    else:
                        price = 0.0
                        print("❌ Kein Preis extrahiert")

                    # Bild
                    img_elem = ad.query_selector("img")
                    img_url = img_elem.get_attribute("src") if img_elem else ""

                    # Link
                    href = title_elem.get_attribute("href") if title_elem else ""
                    link = f"https://www.kleinanzeigen.de{href}" if href else ""

                    results.append({
                        "title": title,
                        "price": price,
                        "image": img_url,
                        "link": link
                    })

                except Exception as e:
                    print(f"❌ Fehler in Anzeige {index + 1}: {e}")
                    continue

        except Exception as e:
            print(f"❌ Hauptfehler: {e}")
        finally:
            context.close()
            browser.close()

    print("\n=== Scraping abgeschlossen ===")
    print(f"Ergebnisse: {results}")
    return results

# Lokaler Test
if __name__ == "__main__":
    scrape_ads("iphone 14 pro")
