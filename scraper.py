from playwright.sync_api import sync_playwright

def get_prices_only(modell):
    """Extrahiert NUR Preise von Kleinanzeigen"""
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    prices = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Sichtbar für Debugging
        page = browser.new_page()
        
        try:
            # 1. Seite laden
            page.goto(url, timeout=60000)
            print("Seite geladen - suche Preise...")

            # 2. Explizit auf Preiselemente warten
            page.wait_for_selector("p.aditem-main--middle--price-shipping--price", timeout=10000)
            
            # 3. Alle Preise sammeln
            price_elements = page.query_selector_all("p.aditem-main--middle--price-shipping--price")
            print(f"Gefundene Preiselemente: {len(price_elements)}")

            for element in price_elements:
                price_text = element.inner_text().strip()
                print(f"Roh-Preis: '{price_text}'")  # Debug-Ausgabe
                
                # Einfache Bereinigung (nur Zahlen und Komma)
                clean_price = ''.join(c for c in price_text if c.isdigit() or c in ',.')
                prices.append(clean_price)

        except Exception as e:
            print(f"FEHLER: {str(e)}")
        finally:
            browser.close()

    return prices

# Testaufruf
if __name__ == "__main__":
    preise = get_prices_only("iphone 14")
    print("\nErgebnis:")
    for i, preis in enumerate(preise, 1):
        print(f"Anzeige {i}: {preis or 'Kein Preis'}")

    if not preise:
        print("⚠️ Keine Preise gefunden! Bitte manuell prüfen:")
        print("- Browser öffnet sich? (Captcha?)")
        print("- Stimmt der Selektor 'p.aditem-main--middle--price-shipping--price'?")
