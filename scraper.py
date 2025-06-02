from playwright.sync_api import sync_playwright
import re

def scrape_ads(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []
    debug_logs = []  # Speichert Debug-Nachrichten für die App

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. Seite laden
            debug_logs.append(f"🔄 Lade Seite: {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 2. Warte auf Anzeigen
            debug_logs.append("🔍 Suche nach Anzeigen...")
            page.wait_for_selector("article.aditem", timeout=15000)
            ads = page.query_selector_all("article.aditem")
            debug_logs.append(f"✅ {len(ads)} Anzeigen gefunden")

            for ad in ads[:10]:  # Begrenzung für Performance
                try:
                    # A. Titel extrahieren
                    title = ad.query_selector("a.ellipsis").inner_text().strip()
                    debug_logs.append(f"\n📌 Verarbeite: '{title}'")

                    # B. Preis-Extraktion mit Debugging
                    price_element = ad.query_selector("p.aditem-main--middle--price-shipping--price")
                    if not price_element:
                        debug_logs.append("⚠️ Preis-Element nicht gefunden! Versuche Alternativen...")
                        price_element = ad.query_selector(".price, [class*='price']")

                    if price_element:
                        price_text = price_element.inner_text().strip()
                        debug_logs.append(f"ℹ️ Roh-Preis: '{price_text}'")
                        
                        # Preisbereinigung
                        price_clean = re.sub(r"[^\d,.]", "", price_text).replace(",", ".")
                        price = float(price_clean) if price_clean else 0.0
                        debug_logs.append(f"✅ Preis geparst: {price}€")
                    else:
                        price = 0.0
                        debug_logs.append("❌ Kein Preis ermittelbar")

                    # C. Ergebnisse sammeln
                    results.append({
                        "title": title,
                        "price": price,
                        "link": f"https://www.kleinanzeigen.de{ad.query_selector('a.ellipsis').get_attribute('href')}",
                        "image": ad.query_selector("img").get_attribute("src") or ""
                    })

                except Exception as e:
                    error_msg = f"❌ Fehler bei Anzeige: {str(e)}"
                    debug_logs.append(error_msg)
                    continue

        except Exception as e:
            debug_logs.append(f"💥 KRITISCHER FEHLER: {str(e)}")
        finally:
            browser.close()

    # Rückgabe für die App (Ergebnisse + Logs)
    return {
        "ads": results,
        "debug_logs": debug_logs,
        "success": len(results) > 0
    }
