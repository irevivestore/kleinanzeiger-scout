from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time

def scrape_ads(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Hauptseite mit JS-Unterstützung aufrufen
        page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Explizit auf dynamisch geladene Elemente warten
        page.wait_for_selector("article.aditem", state="attached", timeout=15000)
        
        # Scrollen um Lazy-Loading zu triggern
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("article.aditem")[:8]  # Begrenzung für Performance
        
        for card in cards:
            try:
                title = card.select_one("h2").get_text(strip=True) if card.select_one("h2") else "Kein Titel"
                relative_link = card.select_one("a")["href"] if card.select_one("a") else ""
                link = f"https://www.kleinanzeigen.de{relative_link}" if relative_link else ""
                img = card.select_one("img")["src"] if card.select_one("img") else ""
                
                if not link:
                    continue
                
                # Neue Seite im gleichen Context erstellen
                with context.expect_page() as new_page_info:
                    page.evaluate(f"window.open('{link}')")
                detail_page = new_page_info.value
                
                # Auf Detailseite warten
                detail_page.wait_for_load_state("networkidle", timeout=30000)
                
                # Dynamische Preis-Extraktion
                try:
                    price_element = detail_page.wait_for_selector(
                        'h2[itemprop="price"], 
                        state="attached",
                        timeout=5000
                    )
                    price_text = price_element.inner_text()
                    price_clean = re.sub(r"[^\d,.]", "", price_text).replace(",", ".")
                    price = float(price_clean) if price_clean else 0.0
                except Exception as e:
                    print(f"Preis nicht gefunden für {title}: {e}")
                    price = 0.0
                finally:
                    detail_page.close()
                
                results.append({
                    "title": title,
                    "price": price,
                    "link": link,
                    "image": img
                })
                
            except Exception as e:
                print(f"Fehler bei {title}: {e}")
                continue
        
        context.close()
        browser.close()
    
    return results
