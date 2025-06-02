from playwright.sync_api import sync_playwright
import re
import time

def scrape_ads(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Headless=False für sichtbaren Browser
        context = browser.new_context()
        page = context.new_page()

        try:
            # Debug: Netzwerkaktivität protokollieren
            def log_request(request):
                if "api." in request.url:
                    print(f">> API Request: {request.url}")
            
            page.on("request", log_request)

            print(f"\n=== Starte Scraping für {modell} ===")
            page.goto(url, wait_until="networkidle", timeout=60000)
            print("✓ Seite geladen")

            # Debug: Screenshot der gesamten Seite
            page.screenshot(path="debug_page.png", full_page=True)
            print("✓ Screenshot gespeichert (debug_page.png)")

            # Warte auf Anzeigen-Elemente
            page.wait_for_selector("article.aditem", timeout=15000)
            ads = page.query_selector_all("article.aditem")
            print(f"ℹ Gefundene Anzeigen: {len(ads)}")

            for index, ad in enumerate(ads[:5]):  # Nur erste 5 für Debugging
                print(f"\n--- Verarbeite Anzeige {index + 1} ---")
                
                try:
                    # Debug: HTML der einzelnen Anzeige speichern
                    ad_html = ad.inner_html()
                    with open(f"debug_ad_{index}.html", "w", encoding="utf-8") as f:
                        f.write(ad_html)
                    print(f"✓ Anzeigen-HTML gespeichert (debug_ad_{index}.html)")

                    # Titel extrahieren
                    title = ad.query_selector("a.ellipsis").inner_text().strip()
                    print(f"ℹ Titel: {title}")

                    # PREIS Debugging
                    price_element = ad.query_selector("p.aditem-main--middle--price-shipping--price")
                    
                    if not price_element:
                        print("❌ Preis-Element nicht gefunden! Alternative Selektor-Versuche:")
                        alt_selectors = [
                            ".aditem-main--middle--price",
                            ".price",
                            "[class*='price']"
                        ]
                        for selector in alt_selectors:
                            alt_element = ad.query_selector(selector)
                            print(f"  - {selector}: {'gefunden' if alt_element else 'nicht vorhanden'}")
                    else:
                        print("✓ Preis-Element gefunden")
                        price_text = price_element.inner_text()
                        print(f"ℹ Roh-Preis-Text: '{price_text}'")
                        
                        # Preisbereinigung
                        price_clean = re.sub(r"[^\d,.]", "", price_text).replace(",", ".")
                        print(f"ℹ Bereinigter Preis: '{price_clean}'")
                        
                        try:
                            price = float(price_clean) if price_clean else 0.0
                            print(f"✓ Preis erfolgreich geparst: {price}€")
                        except ValueError as e:
                            print(f"❌ Fehler bei Preis-Konvertierung: {str(e)}")
                            price = 0.0

                    # Ergebnisse sammeln
                    results.append({
                        "title": title,
                        "price": price if 'price' in locals() else 0.0,
                        "link": f"https://www.kleinanzeigen.de{ad.query_selector('a.ellipsis').get_attribute('href')}",
                        "image": ad.query_selector("img").get_attribute("src") if ad.query_selector("img") else ""
                    })

                except Exception as e:
                    print(f"❌ Fehler in Anzeige {index + 1}: {str(e)}")
                    continue

        except Exception as e:
            print(f"❌ Hauptfehler: {str(e)}")
        finally:
            context.close()
            browser.close()

    print("\n=== Scraping abgeschlossen ===")
    print(f"Ergebnisse: {results}")
    return results

# Beispielaufruf
if __name__ == "__main__":
    scrape_ads("iphone 14")
