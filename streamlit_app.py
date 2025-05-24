import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def scrape_with_playwright(modell):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    print(f"📡 URL: {url}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(5000)  # 5 Sekunden warten (wichtig!)

        html = await page.content()
        await browser.close()

        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("article.aditem")
        print(f"🔍 Anzahl gefundener Anzeigen: {len(items)}")

        for item in items[:3]:  # Nur Vorschau
            print(item.prettify()[:500])