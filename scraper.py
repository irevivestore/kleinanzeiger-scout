import re
import time
import uuid
from datetime import datetime
from urllib.parse import quote, urljoin
from playwright.sync_api import sync_playwright, TimeoutError

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
    if log is None:
        def log(x): print(x)
    
    if config is None:
        config = {
            "verkaufspreis": 600,
            "wunsch_marge": 100,
            "reparaturkosten": {}
        }

    base_url = "https://www.kleinanzeigen.de"
    kategorie = "handy-telekom" if nur_versand else ""
    
    # URL construction
    pfadteile = ["s-anzeige:angebote" if nur_angebote else "s"]
    if kategorie:
        pfadteile.append(f"-{kategorie}")
    pfadteile.extend([
        f"preis:{min_price}:{max_price}",
        quote(modell),
        "k0"
    ])
    
    url = f"{base_url}/{'/'.join(pfadteile)}"
    if nur_versand:
        url += "c173+handy_telekom.versand_s:ja"
    
    log(f"[🔍] Starte Suche unter: {url}")
    log(f"[⚙️] Konfiguration: {config}")

    anzeigen = []
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True debug,
                args=["--enable-logging", "--v=1"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            
            # Enable request logging
            def on_request(request):
                log(f"→ {request.method} {request.url}")
            
            page.on("request", on_request)
            
            # Main page loading
            page.goto(url, timeout=90000)
            page.wait_for_load_state("networkidle")
            
            if debug:
                page.screenshot(path="debug_main_page.png")
                log("[📸] Screenshot der Hauptseite gespeichert")
            
            # Wait for ads
            page.wait_for_selector("article.aditem", timeout=15000)
            eintraege = page.locator("article.aditem")
            count = eintraege.count()
            log(f"[📄] {count} Anzeigen gefunden")
            
            if count == 0:
                log("[⚠️] Keine Anzeigen gefunden - HTML-Inhalt:")
                log(page.content()[:500] + "...")
                return []
            
            # Process ads
            for i in range(min(count, 50)):  # Limit to 50 for debugging
                try:
                    log(f"\n--- Anzeige {i+1}/{count} ---")
                    entry = eintraege.nth(i)
                    
                    # Extract basic info
                    ad_id = entry.get_attribute("data-adid") or str(uuid.uuid4())
                    custom_href = entry.get_attribute("data-custom-href") or entry.locator("a").get_attribute("href")
                    
                    if not custom_href or not custom_href.startswith("/s-anzeige/"):
                        log(f"[⚠️] Ungültiger Link: {custom_href}")
                        continue
                    
                    full_link = urljoin(base_url, custom_href)
                    log(f"[🔗] Link: {full_link}")
                    
                    # Extract title and price
                    title = entry.locator("h2").inner_text().strip()
                    price_text = entry.locator(".aditem-main--middle--price-shipping--price").inner_text()
                    price = int(re.sub(r"[^\d]", "", price_text or "0"))
                    
                    log(f"[💰] {title} - {price}€")
                    
                    # Get description
                    detail_page = context.new_page()
                    try:
                        detail_page.goto(full_link, timeout=30000)
                        detail_page.wait_for_selector("div[data-testid='description']", timeout=10000)
                        
                        beschreibung = detail_page.locator("div[data-testid='description']").inner_text()
                        log(f"[📝] Beschreibungslänge: {len(beschreibung)} Zeichen")
                    except Exception as e:
                        log(f"[⚠️] Detailseitenfehler: {str(e)}")
                        beschreibung = ""
                    finally:
                        detail_page.close()
                    
                    # Calculate repair costs
                    rep_summe = 0
                    for defekt, kosten in config["reparaturkosten"].items():
                        if defekt.lower() in beschreibung.lower():
                            rep_summe += kosten
                    
                    # Evaluate deal
                    max_ek = config["verkaufspreis"] - config["wunsch_marge"] - rep_summe
                    bewertung = (
                        "grün" if price <= max_ek else
                        "blau" if price <= max_ek + (config["wunsch_marge"] * 0.1) else
                        "rot"
                    )
                    
                    log(f"[✅] Bewertung: {bewertung} (Max EK: {max_ek}€)")
                    
                    anzeigen.append({
                        "id": ad_id,
                        "modell": modell,
                        "title": title,
                        "price": price,
                        "link": full_link,
                        "image": entry.locator("img").get_attribute("src"),
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
                    log(f"[❌] Fehler bei Anzeige {i+1}: {str(e)}")
                    continue
            
            return anzeigen
        
        except Exception as e:
            log(f"[🔥] Kritischer Fehler: {str(e)}")
            return []
        
        finally:
            if 'browser' in locals():
                browser.close()
