#!/bin/sh

# Ten sam znacznik zainstalowanego sklepu sprawdza docker_run.sh
if [ ! -f /var/www/html/app/config/parameters.php ]; then
    echo "10-configure-mail: sklep nie jest zainstalowany, pomijam"
    exit 0
fi

# Adres serwera SMTP podaje compose.yaml: MAIL_SMTP_HOST (nazwa uslugi z Mailpitem)
# i MAIL_SMTP_PORT. Zrodlem prawdy jest compose.yaml, wiec tu nie ma wartosci domyslnych.
if [ -z "$MAIL_SMTP_HOST" ] || [ -z "$MAIL_SMTP_PORT" ]; then
    echo "10-configure-mail: BLAD: brak MAIL_SMTP_HOST lub MAIL_SMTP_PORT, pomijam"
    exit 0
fi

# Konsola jako www-data (tak jak instalator w obrazie), zeby nie utworzyc
# w var/cache plikow nalezacych do roota, do ktorych Apache nie moglby pisac.
set_config() {
    runuser -g www-data -u www-data -- php /var/www/html/bin/console prestashop:config set "$1" --value="$2" \
        || echo "10-configure-mail: BLAD: nie udalo sie ustawic $1"
}

echo "10-configure-mail: ustawiam SMTP ${MAIL_SMTP_HOST}:${MAIL_SMTP_PORT}"
set_config PS_MAIL_METHOD 2
set_config PS_MAIL_SERVER "$MAIL_SMTP_HOST"
set_config PS_MAIL_SMTP_PORT "$MAIL_SMTP_PORT"
set_config PS_MAIL_SMTP_ENCRYPTION off

exit 0
