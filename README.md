# Kleinanzeigen Scout – Fly.io Edition

Einfacher Kleinanzeigen.de-Scraper mit Flask-Frontend, bereit für Fly.io Deployment.

## Start lokal
```bash
pip install -r requirements.txt
playwright install chromium
python app.py
```

## Deployment auf Fly.io
```bash
fly launch
fly deploy
```