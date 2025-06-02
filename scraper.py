from playwright.sync_api import sync_playwright
import re
from datetime import datetime

def scrape_ads(modell):
    """Gibt ein Dict zurück mit: {
        'ads': [], 
        'debug': [], 
        'status': 'success'|'partial'|'failed',
        'timestamp': str
    }"""
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    result = {
        'ads': [],
        'debug': [],
        'status': 'success',
        'timestamp': datetime.now().isoformat()
    }

    def log(msg):
        """Fügt Debug-Nachricht hinzu"""
        result['debug'].append(f"{datetime.now().strftime('%H:%M:%S')} - {msg}")

    with sync_playwright() as p:
        try:
            # Browser mit erweiterten Optionen starten
            browser = p.chromium.launch(
                headless=False,  # Sichtbar für Debugging
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            # 1. Seite laden
            log(f"Starte Scraping für: {modell}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            log(f"Seite geladen: {url}")

            # 2. Auf dynamische Inhalte warten
            page.wait_for_selector("article.aditem", timeout=15000)
            ads = page.query_selector_all("article.aditem")
            log(f"Gefundene Anzeigen: {len(ads)}")

            for i, ad in enumerate(ads[:10]):  # Nur erste 10 für Debugging
                try:
                    # A. Titel extrahieren
                    title = ad.query_selector("h2").inner_text().strip()
                    log(f"\nAnzeige {i+1}: {title[:30]}...")

                    # B. Preis-Extraktion mit erweitertem Debugging
                    price = extract_price(ad, log)
                    
                    # C. Ergebnisse sammeln
                    result['ads'].append({
                        'title': title,
                        'price': price,
                        'link': "https://www.kleinanzeigen.de" + ad.query_selector("a").get_attribute("href"),
                        'image': get_image_url(ad)
                    })

                except Exception as e:
                    log(f"Fehler bei Anzeige {i+1}: {str(e)}")
                    result['status'] = 'partial'
                    continue

        except Exception as e:
            log(f"KRITISCHER FEHLER: {str(e)}")
            result['status'] = 'failed'
        finally:
            browser.close()

    log("Scraping abgeschlossen")
    return result

def extract_price(ad, log_func):
    """Hilfsfunktion für robuste Preis-Extraktion"""
    price_selectors = [
        "p.aditem-main--middle--price-shipping--price",  # Hauptselektor
        "p.aditem-main--middle--price",  # Fallback 1
        ".price",  # Fallback 2
        "[class*='price']"  # Generischer Fallback
    ]

    for selector in price_selectors:
        element = ad.query_selector(selector)
        if element:
            price_text = element.inner_text().strip()
            log_func(f"Preis gefunden mit {selector}: '{price_text}'")
            
            # Sonderfälle erkennen
            if "VB" in price_text:
                return -1  # Code für Verhandlungsbasis
            if "verschenken" in price_text.lower():
                return 0
            
            # Numerischen Wert extrahieren
            match = re.search(r"([\d.,]+)\s*€?", price_text)
            if match:
                try:
                    return float(match.group(1).replace(".", "").replace(",", "."))
                except ValueError:
                    log_func(f"Konvertierungsfehler bei: '{price_text}'")
                    continue
    
    log_func("Kein Preis ermittelbar")
    return 0

def get_image_url(ad):
    """Holt Bild-URL mit Priorisierung für Lazy-Loading"""
    img = ad.query_selector("img")
    if img:
        return img.get_attribute("data-src") or img.get_attribute("src")
    return ""
