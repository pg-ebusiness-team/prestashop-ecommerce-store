#!/bin/sh

# Dopasowanie zainstalowanego sklepu do zmiennych srodowiskowych przy kazdym starcie kontenera: dane bazy
# w parameters.php, katalog admina, domena i SSL (z .htaccess). Instalator zapisuje je tylko raz, wiec bez tego
# sklep odtworzony z kopii (make restore) albo po zmianie portu/domeny w .env dzialalby ze starymi wartosciami.
# Cala logika jest w /usr/local/share/shop-init/sync-env.php (w repo: shop/scripts/sync-env.php).
# Musi isc przed 05-cache-warmup.sh, ktory laduje PrestaShop i potrzebuje poprawnych danych bazy.

# Ten sam znacznik zainstalowanego sklepu sprawdza docker_run.sh
if [ ! -f /var/www/html/app/config/parameters.php ]; then
    echo "02-sync-env: sklep nie jest zainstalowany, pomijam"
    exit 0
fi

# Jako www-data, zeby parameters.php, .htaccess i cache nalezaly do uzytkownika Apache.
# Blad zatrzymuje start kontenera (docker_run.sh dziala z `set -e`): sklep z niezgodnymi danymi bazy lub domena
# i tak by nie dzialal, a kontener, ktory nie wstaje, widac w make ps. Przyczyna w logu (make logs SERVICE=shop).
if ! runuser -g www-data -u www-data -- php /usr/local/share/shop-init/sync-env.php; then
    echo "02-sync-env: BLAD: dopasowanie do zmiennych srodowiskowych nie powiodlo sie, sklep nie zostanie uruchomiony"
    exit 1
fi

exit 0
