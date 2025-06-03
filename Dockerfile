FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 \
    libgbm1 libxcb1 libxkbcommon0 libasound2 \
    libxrandr2 libgtk-3-0 wget curl ca-certificates fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && playwright install chromium

COPY . .

CMD ["python", "app.py"]
