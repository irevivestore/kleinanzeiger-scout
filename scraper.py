import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import re

async def scrape_kleinanzeigen(verkaufspreis: int, wunsch_marge: int, reparaturkosten: int, debug: bool = False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "https://www.kleinanzeigen.de/s-handys-telefone/iphone-14-pro/k0"
        await page.goto(url)

        await page.wait_for_selector("article.aditem")

        eintraege = await page.locator("article.aditem").all()
        print(f"📦 {len(eintraege)} Anzeigen gefunden")

        for index, eintrag in enumerate(eintraege):
            try:
                print(f"\n--- Anzeige {index + 1}/{len(eintraege)} ---")

                # Zwei mögliche Links – wir wählen den sichtbaren und klickbaren Link
                links = await eintrag.locator("a.ellipsis").all()
                if not links:
                    raise Exception("Kein passender Link gefunden")

                link_element = links[0]
                relative_url = await link_element.get_attribute("href")
                if not relative_url:
                    raise Exception("Kein href gefunden")
                link = f"https://www.kleinanzeigen.de{relative_url}"
                print(f"[🔗] Link: {link}")

                # Titel extrahieren
                titel = await link_element.inner_text()
                titel = titel.strip()
                print(f"[📝] Titel: {titel}")

                # Preis aus Text extrahieren
                preis_element = await eintrag.locator(".aditem-main--middle .aditem-main--middle--price").first
                preis_text = await preis_element.inner_text()
                preis_match = re.search(r"\d+", preis_text.replace(".", ""))
                preis = int(preis_match.group()) if preis_match else 0
                print(f"[💰] Preis: {preis}€")

                # Bewertung (grün, gelb, rot)
                max_einkaufspreis = verkaufspreis - wunsch_marge - reparaturkosten
                if preis <= max_einkaufspreis:
                    farbe = "grün"
                elif preis <= max_einkaufspreis + 50:
                    farbe = "gelb"
                else:
                    farbe = "rot"

                print(f"[✅] Bewertung: {farbe} (Max EK: {max_einkaufspreis}€)")

                if debug:
                    # Detailseite besuchen
                    detail = await browser.new_page()
                    await detail.goto(link)
                    try:
                        await detail.wait_for_selector("div[data-testid='description']", timeout=10_000)
                        beschreibung = await detail.locator("div[data-testid='description']").inner_text()
                        beschreibung = beschreibung.strip()
                        print(f"[📄] Beschreibung: {beschreibung[:150]}{'...' if len(beschreibung) > 150 else ''}")
                    except Exception:
                        print(f"[⚠️] Detailseitenfehler: Beschreibung konnte nicht geladen werden.")
                    await detail.close()

            except Exception as e:
                print(f"[❌] Fehler bei Anzeige {index + 1}: {e}")

        await browser.close()


# Beispielhafte Verwendung
if __name__ == "__main__":
    asyncio.run(scrape_kleinanzeigen(
        verkaufspreis=550,
        wunsch_marge=100,
        reparaturkosten=70,
        debug=True
    ))