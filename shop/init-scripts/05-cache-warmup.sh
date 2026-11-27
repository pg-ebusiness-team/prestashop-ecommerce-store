#!/bin/sh

# Rozgrzanie cache Symfony (bin/console cache:warmup) przy kazdym starcie, ok. 1 s.
# Warmer PrestaShop (src/PrestaShopBundle/Cache/CacheWarmer.php) tworzy w var/cache/prod/ katalogi
# purifier, tcpdf, cachefs, push i sandbox. Instalator ich nie tworzy, a bez nich:
#  - zapis produktu z opisem HTML (import przez API) konczy sie HTTP 500 (brak purifier),
#  - generowanie PDF faktury moze sie nie udac (brak tcpdf).
# Dotad tworzyl je przypadkiem cache:clear w `make theme` uruchamianym przed importem.

# Ten sam znacznik zainstalowanego sklepu sprawdza docker_run.sh
if [ ! -f /var/www/html/app/config/parameters.php ]; then
    echo "05-cache-warmup: sklep nie jest zainstalowany, pomijam"
    exit 0
fi

# Jako www-data, zeby pliki cache nalezaly do uzytkownika Apache
if runuser -g www-data -u www-data -- php /var/www/html/bin/console cache:warmup --env=prod > /dev/null; then
    echo "05-cache-warmup: cache rozgrzany"
else
    echo "05-cache-warmup: BLAD: cache:warmup nie powiodl sie, import produktow moze zwracac HTTP 500"
fi

exit 0
