#!/bin/sh

# Konfiguracja sprzedazy (platnosci, przewoznicy, ograniczenia dostawy) przy kazdym starcie kontenera.
# Cala logika jest w /usr/local/share/shop-init/configure-sales.php (w repo: shop/scripts/configure-sales.php).
# PHP nie lezy w /tmp/init-scripts/, bo docker_run.sh uruchamia kazdy plik z tego katalogu.

# Ten sam znacznik zainstalowanego sklepu sprawdza docker_run.sh
if [ ! -f /var/www/html/app/config/parameters.php ]; then
    echo "20-configure-sales: sklep nie jest zainstalowany, pomijam"
    exit 0
fi

# Jako www-data (tak jak instalator w obrazie), zeby nie utworzyc w var/cache plikow nalezacych do roota.
# Blad konfiguracji zatrzymuje start kontenera: docker_run.sh dziala z `set -e`, wiec kod != 0 konczy go
# przed uruchomieniem Apache. Sklep z ustawieniami z instalatora (czek, domyslni przewoznicy) nie spelnialby
# wymagan, a taki blad bylby latwy do przeoczenia. Przyczyna jest w logu (make logs SERVICE=shop).
if ! runuser -g www-data -u www-data -- php /usr/local/share/shop-init/configure-sales.php; then
    echo "20-configure-sales: BLAD: konfiguracja sprzedazy nie powiodla sie, sklep nie zostanie uruchomiony"
    exit 1
fi

exit 0
