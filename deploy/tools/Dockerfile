# Kontener narzędziowy do inicjalizacji danych (make init, make import): importer i scraper w Pythonie
# bez instalowania Pythona na hoście. Kod nie jest kopiowany do obrazu - compose.yaml montuje repo w /app,
# więc obraz trzeba przebudować tylko po zmianie scraper/requirements.txt.
FROM python:3.12-slim

# curl i unzip: pobieranie i rozpakowanie archiwum zdjęć z Releases (deploy/init/photos.sh)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl unzip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Bez __pycache__ w zamontowanym repo
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
