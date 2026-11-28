#!/usr/bin/env bash
# Odtworzenie sklepu z kopii z deploy/backup.sh (WYMAGANIA.md, D4: „odtwarzają z niej sklep”, na czystym środowisku ≤10 min).
# Uruchamiany na hoście z katalogu repo: make restore [BACKUP=backups/backup-<data>.tar] (domyślnie najnowsza kopia).
#
# Bieżące dane sklepu (baza, wolumeny shop_data i proxy_certs, mapowania importera) są USUWANE i zastępowane kopią.
# Środowisko opisuje bieżący .env, a nie kopia: dane bazy, domenę, SSL i katalog admina dopasowuje przy starcie
# shop/init-scripts/02-sync-env.sh, a klucz Webservice API - make webservice. Konta (np. hasło admina) są z kopii.
# Bez pytania o potwierdzenie: CONFIRM=tak.
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE=(docker compose -f deploy/compose.yaml --env-file .env)
BACKUP_DIR=backups

log() { echo "restore: $*"; }
fail() { echo "restore: BLAD: $*" >&2; exit 1; }

start=$(date +%s)
[ -f .env ] || fail "brak .env - na czystym klonie tworzy go make (make restore), recznie: cp .env.example .env"

backup="${1:-}"
if [ -z "$backup" ]; then
    backup=$(ls -1 "$BACKUP_DIR"/backup-*.tar 2>/dev/null | sort | tail -n 1 || true)
    [ -n "$backup" ] || fail "brak kopii w $BACKUP_DIR/ - podaj plik: make restore BACKUP=<plik.tar>"
fi
[ -f "$backup" ] || fail "nie ma pliku $backup"

# 1. Rozpakowanie i sprawdzenie sum z manifestu, zanim cokolwiek zostanie usunięte
umask 077
mkdir -p "$BACKUP_DIR"
work=$(mktemp -d "$BACKUP_DIR/.restore.XXXXXX")
trap 'rm -rf "$work"' EXIT
log "sprawdzam kopie $backup..."
tar -C "$work" -xf "$backup"
for part in manifest.txt db.sql.gz shop_data.tar.gz proxy_certs.tar.gz; do
    [ -f "$work/$part" ] || fail "kopia nie zawiera $part"
done
(cd "$work" && sed -n '/^sha256:$/,$p' manifest.txt | tail -n +2 | sha256sum --quiet -c -) \
    || fail "sumy SHA-256 sie nie zgadzaja - kopia uszkodzona"

sed -n '1,8p' "$work/manifest.txt" | sed 's/^/  /'

# Zmienne, którymi kopia różni się od bieżącego .env - same nazwy, bez wartości
if [ -f "$work/env" ]; then
    diff_vars=$(diff <(grep -E '^[A-Z_]+=' "$work/env" | sort) <(grep -E '^[A-Z_]+=' .env | sort) \
        | grep -E '^[<>]' | sed -E 's/^[<>] ([A-Z_]+)=.*/\1/' | sort -u | tr '\n' ' ' || true)
    if [ -n "$diff_vars" ]; then
        log "biezacy .env rozni sie od .env z kopii: $diff_vars"
        log "sklep zostanie dopasowany do biezacego .env (konta, np. haslo admina, zostaja z kopii)"
    fi
fi

# 2. Potwierdzenie - dalej dane są usuwane
if [ "${CONFIRM:-}" != tak ]; then
    echo "restore: UWAGA: biezaca baza, pliki sklepu, certyfikat i mapowania importu zostana USUNIETE."
    read -r -p "restore: wpisz 'tak', aby kontynuowac: " answer
    [ "$answer" = tak ] || fail "przerwano, nic nie zostalo zmienione"
fi

# 3. Usunięcie bieżących kontenerów i wolumenów (jak make reset)
log "usuwam biezace kontenery i wolumeny..."
"${COMPOSE[@]}" down -v --remove-orphans
rm -f scraper/importer/*_mapping.json

# 4. Baza: świeży MySQL zakłada bazę i użytkownika z bieżącego .env. Przy pierwszym starcie MySQL uruchamia się
#    najpierw tymczasowo bez sieci, więc czekamy na połączenie po TCP, tak jak potem połączy się sklep.
log "uruchamiam baze..."
"${COMPOSE[@]}" up -d db
db_sql() {
    "${COMPOSE[@]}" exec -T db sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" exec mysql -h127.0.0.1 -u"$MYSQL_USER" "$MYSQL_DATABASE" "$@"' sh "$@"
}
for _ in $(seq 1 90); do
    db_sql -e 'SELECT 1' >/dev/null 2>&1 && break
    sleep 2
done
db_sql -e 'SELECT 1' >/dev/null 2>&1 || fail "baza nie odpowiada po 3 min - sprawdz: make logs SERVICE=db"

log "wgrywam zrzut bazy..."
gzip -dc "$work/db.sql.gz" | db_sql

# 5. Pliki sklepu do pustego wolumenu shop_data. Docker przy pierwszym montażu kopiuje do niego pliki z obrazu
#    (m.in. admin/ i install/), dlatego najpierw je usuwamy - inaczej obok katalogu admina z kopii zostałby
#    drugi panel i katalog instalatora. tar jako root zachowuje właścicieli (www-data).
log "wgrywam pliki sklepu (wolumen shop_data)..."
"${COMPOSE[@]}" run --rm -T --no-deps --entrypoint sh shop \
    -c 'find /var/www/html -mindepth 1 -delete && tar -xzpf - -C /var/www/html' < "$work/shop_data.tar.gz"

log "wgrywam certyfikat (wolumen proxy_certs)..."
"${COMPOSE[@]}" run --rm -T --no-deps --entrypoint sh proxy \
    -c 'tar -xzf - -C /etc/nginx/certs' < "$work/proxy_certs.tar.gz"

# 6. Mapowania importera z kopii pasują do ID w odtworzonej bazie
if ls "$work"/mappings/*_mapping.json >/dev/null 2>&1; then
    cp "$work"/mappings/*_mapping.json scraper/importer/
fi

# 7. Start sklepu jak make up. docker_run.sh widzi parameters.php, więc nie instaluje PrestaShop od nowa,
#    a 02-sync-env.sh dopasowuje dane bazy, domenę i katalog admina do bieżącego .env.
log "uruchamiam sklep..."
"${COMPOSE[@]}" up -d --build --wait --wait-timeout 900

# 8. Klucz Webservice API z bieżącego .env (w kopii jest klucz ze środowiska, w którym ją zrobiono)
make --no-print-directory webservice

# 9. Porównanie liczby rekordów z manifestem
check_count() {
    local label=$1 query=$2 expected actual
    expected=$(sed -n "s/^$label: //p" "$work/manifest.txt")
    actual=$(db_sql -N -e "$query")
    if [ "$expected" = "$actual" ]; then
        log "OK   $label: $actual"
    else
        fail "$label: w bazie $actual, w kopii $expected"
    fi
}
check_count produkty 'SELECT COUNT(*) FROM ps_product'
check_count kategorie 'SELECT COUNT(*) FROM ps_category'
check_count klienci 'SELECT COUNT(*) FROM ps_customer'
check_count zamowienia 'SELECT COUNT(*) FROM ps_orders'
check_count zdjecia_produktow 'SELECT COUNT(*) FROM ps_image'

elapsed=$(( $(date +%s) - start ))
# Adres z .env bez wczytywania całego pliku w shellu (PS_TAX_RULES_GROUP_MAP to JSON)
env_value() { sed -n "s/^$1=//p" .env | tail -n 1; }
echo ""
log "gotowe w $(( elapsed / 60 )) min $(( elapsed % 60 )) s. Sklep: https://$(env_value SERVER_NAME):$(env_value HTTPS_PORT)"
