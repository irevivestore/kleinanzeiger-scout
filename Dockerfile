FROM python:3.11-slim

# Systemabhängigkeiten für Playwright/Chromium
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 \
    libgbm1 libxcb1 libxkbcommon0 libasound2 \
    libxrandr2 libgtk-3-0 wget curl ca-certificates fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Umgebungsvariablen für Streamlit korrekt setzen
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_OPTIONS=--openssl-legacy-provider

# Arbeitsverzeichnis setzen
WORKDIR /app

# Anforderungen installieren
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Playwright: Browser installieren (Chromium)
RUN playwright install --with-deps chromium

# Projektdateien kopieren
COPY . .

# Wichtige Änderung: Config direkt ins richtige Verzeichnis kopieren
RUN mkdir -p /app/.streamlit
COPY .streamlit/config.toml /app/.streamlit/config.toml

# Startbefehl für Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
