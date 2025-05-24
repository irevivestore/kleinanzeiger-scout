import requests
from bs4 import BeautifulSoup

def fetch_kleinanzeigen(model_keyword):
    # Modell als URL-Keyword aufbereiten
    keyword = model_keyword.replace(" ", "-").lower()
    url = f"https://www.kleinanzeigen.de/s-{keyword}/k0"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Fehler beim Abrufen: Status Code {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select("article.aditem")

    ergebnisse = []

    for item in items:
        try:
            titel_tag = item.select_one("a.ellipsis")
            titel = titel_tag.get_text(strip=True)
            link = "https://www.kleinanzeigen.de" + titel_tag["href"]

            preis_tag = item.select_one("p.aditem-main--middle--price-shipping--price")
            preis = preis_tag.get_text(strip=True) if preis_tag else "Kein Preis angegeben"

            beschreibung_tag = item.select_one("div.aditem-main--middle > p")
            beschreibung = beschreibung_tag.get_text(strip=True) if beschreibung_tag else "Keine Beschreibung"

            bild_tag = item.select_one("img")
            bild_url = bild_tag["src"] if bild_tag and "src" in bild_tag.attrs else None

            ergebnisse.append({
                "titel": titel,
                "preis": preis,
                "beschreibung": beschreibung,
                "link": link,
                "thumbnail": bild_url
            })
        except Exception as e:
            print(f"Fehler beim Verarbeiten eines Elements: {e}")
            continue

    return ergebnisse

# Beispielnutzung
if __name__ == "__main__":
    modell = "iPhone 14 Pro"
    anzeigen = fetch_kleinanzeigen(modell)

    if not anzeigen:
        print("❌ Keine Anzeigen gefunden.")
    else:
        for i, a in enumerate(anzeigen, 1):
            print(f"{i}. {a['titel']}")
            print(f"   Preis: {a['preis']}")
            print(f"   Beschreibung: {a['beschreibung']}")
            print(f"   Link: {a['link']}")
            print(f"   Thumbnail: {a['thumbnail']}\n")