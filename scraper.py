# scraper.py

from playwright.sync_api import sync_playwright
import re
from datetime import datetime

def scrape_ads(modell, min_price=None, max_price=None, nur_versand=False):
    keyword = modell.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_selector("article.aditem", timeout