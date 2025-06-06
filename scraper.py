import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_ads(suchbegriff, min_price=0, max_price=1500, nur_versand=False, nur_angebote=True):
    print(f"[scrape_ads] Starte Suche nach '{suchbegriff}' mit min_price={min_price}, max_price={max_price}, nur_versand={nur_versand}, nur_angebote={nur_angebote}")

    base_url = "https://www.kleinanzeigen.de/s/"
    query = suchbegriff.replace(" ", "%20")
    url = f"{base_url}{'anzeige:angebote/' if nur_angebote else ''}preis:{min_price}:{max_price}/{query}/k0"
    print(f"[scrape_ads] URL: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(3000)

        items = await page.query_selector_all(".aditem")
        print(f"[scrape_ads] {len(items)} Anzeigen gefunden.")

        anzeigen = []
        for item in items:
            try:
                title_el = await item.query_selector(".text-module-begin h2")
                title = await title_el.inner_text() if title_el else "Unbekannter Titel"

                price_el = await item.query_selector(".aditem-main--middle .aditem-main--price")
                price_text = await price_el.inner_text() if price_el else "0 €"
                price_text = price_text.replace("\n", "").replace(" ", "").replace("€", "")
                price_numbers = re.findall(r"\d+", price_text)

                if len(price_numbers) == 2:
                    price_display = f"{price_numbers[0]} € (~~{price_numbers[1]} €~~)"
                    price = int(price_numbers[0])
                elif len(price_numbers) == 1:
                    price_display = f"{price_numbers[0]} €"
                    price = int(price_numbers[0])
                else:
                    price_display = "Unbekannter Preis"
                    price = 0

                link_el = await item.query_selector("a")
                relative_link = await link_el.get_attribute("href") if link_el else None
                link = f"https://www.kleinanzeigen.de{relative_link}" if relative_link else ""

                # Beschreibung von Detailseite
                beschreibung = ""
                if link:
                    detail_page = await browser.new_page()
                    await detail_page.goto(link)
                    try:
                        await detail_page.wait_for_selector(".html5-section", timeout=5000)
                        beschreibung_el = await detail_page.query_selector(".html5-section")
                        beschreibung = await beschreibung_el.inner_text() if beschreibung_el else ""
                    except:
                        beschreibung = "Fehler beim Laden der Detailseite"
                    await detail_page.close()

                zeitpunkt = datetime.now().strftime("%d.%m.%Y %H:%M")

                anzeigen.append({
                    "titel": title.strip(),
                    "preis": price,
                    "preis_display": price_display,
                    "link": link,
                    "beschreibung": beschreibung.strip(),
                    "zeitpunkt": zeitpunkt,
                    "modell": suchbegriff,
                })

            except Exception as e:
                print(f"[scrape_ads] Fehler beim Parsen einer Anzeige: {e}")

        await browser.close()
        print(f"[scrape_ads] Fertig, {len(anzeigen)} Anzeigen zurückgegeben")
        return anzeigen

if __name__ == "__main__":
    result = asyncio.run(scrape_ads("iPhone 14 Pro"))
    for ad in result:
        print(ad)
