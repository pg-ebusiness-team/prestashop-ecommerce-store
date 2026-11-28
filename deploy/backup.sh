#!/usr/bin/env bash
# Kopia zapasowa działającego sklepu (WYMAGANIA.md, D4: „zrzut bazy, zdjęcia, pliki konfiguracyjne”).
# Uruchamiany na hoście z katalogu repo: make backup. Odtwarzanie: deploy/restore.sh (make restore).
#
# Wynik: backups/backup-<data>.tar (chmod 600: zawiera dane klientów i hasła, w repo wykluczony w .gitignore):
#   db.sql.gz          - zrzut bazy (mysqldump --single-transaction: spójny bez zatrzymywania sklepu)
#   shop_data.tar.gz   - wolumen shop_data (/var/www/html): zdjęcia img/, parameters.php, moduły, katalog admina;
#                        bez zawartości var/cache i var/logs (odtwarzalne)
#   proxy_certs.tar.gz - certyfikat HTTPS (po odtworzeniu przeglądarka nie pyta ponownie o wyjątek)
#   mappings/          - scraper/importer/*_mapping.json (bez nich ponowny import wgrywa zdjęcia drugi raz)
#   env                - kopia .env, tylko informacyjnie: restore dopasowuje sklep do bieżącego .env
#   manifest.txt       - data, commit, wersja PrestaShop, liczby rekordów, sumy SHA-256 części
# Części są już skompresowane, więc archiwum zewnętrzne to zwykły tar.
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE=(docker compose -f deploy/compose.yaml --env-file .env)
BACKUP_DIR=backups

log() { echo "backup: $*"; }
fail() { echo "backup: BLAD: $*" >&2; exit 1; }

start=$(date +%s)
[ -f .env ] || fail "brak .env - uruchom najpierw make up"

# Kopia tylko z działającego sklepu: zrzut i pliki są pobierane z kontenerów
for service in db shop proxy; do
    state=$("${COMPOSE[@]}" ps "$service" --format '{{.State}}' 2>/dev/null || true)
    [ "$state" = running ] || fail "usluga $service nie dziala (stan: '${state:-brak}') - uruchom make up"
done

name="backup-$(date +%Y%m%d-%H%M%S)"
# Pliki tylko dla właściciela: kopia zawiera .env, hasło bazy w parameters.php i dane klientów
umask 077
mkdir -p "$BACKUP_DIR"
work="$BACKUP_DIR/.$name.tmp"
mkdir "$work"
# Przy błędzie nie zostawiamy niepełnej kopii
trap 'rm -rf "$work" "$BACKUP_DIR/$name.tar.part"' EXIT

# 1. Baza. Bez --databases: zrzut nie zawiera CREATE DATABASE/USE, więc wgra się do bazy o dowolnej nazwie
#    (MYSQL_DATABASE z bieżącego .env). --no-tablespaces: użytkownik sklepu nie ma uprawnienia PROCESS.
log "zrzut bazy..."
"${COMPOSE[@]}" exec -T db sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" exec mysqldump -u"$MYSQL_USER" \
    --single-transaction --quick --triggers --no-tablespaces --default-character-set=utf8mb4 "$MYSQL_DATABASE"' \
    | gzip > "$work/db.sql.gz"
# mysqldump kończy poprawny zrzut tą linią - bez niej zrzut jest ucięty
gzip -dc "$work/db.sql.gz" | tail -n 1 | grep -q '^-- Dump completed' || fail "zrzut bazy jest niepelny"

# 2. Pliki sklepu. tar jako root w kontenerze: czyta wszystkie pliki i zapisuje właścicieli (www-data).
#    Katalogi var/cache i var/logs zostają (puste), ich zawartość odtworzy sklep.
log "pliki sklepu (wolumen shop_data)..."
"${COMPOSE[@]}" exec -T shop tar -C /var/www/html --exclude='./var/cache/*' --exclude='./var/logs/*' -czf - . \
    > "$work/shop_data.tar.gz"

# 3. Certyfikat HTTPS
log "certyfikat (wolumen proxy_certs)..."
"${COMPOSE[@]}" exec -T proxy tar -C /etc/nginx/certs -czf - . > "$work/proxy_certs.tar.gz"

# 4. Mapowania importera i kopia .env
mkdir "$work/mappings"
cp scraper/importer/*_mapping.json "$work/mappings/" 2>/dev/null || log "UWAGA: brak mapowan importera (sklep bez importu?)"
cp .env "$work/env"

# 5. Manifest: z czego i kiedy powstała kopia, co w niej jest
sql() {
    "${COMPOSE[@]}" exec -T db sh -c 'MYSQL_PWD="$MYSQL_PASSWORD" mysql -N -u"$MYSQL_USER" "$MYSQL_DATABASE"' <<< "$1"
}
commit=$(git rev-parse --short HEAD 2>/dev/null || echo brak)
[ -n "$(git status --porcelain 2>/dev/null)" ] && commit="$commit (z niezacommitowanymi zmianami)"
{
    echo "data: $(date -Iseconds)"
    echo "commit: $commit"
    echo "prestashop: $(sql "SELECT value FROM ps_configuration WHERE name = 'PS_VERSION_DB'")"
    echo "produkty: $(sql 'SELECT COUNT(*) FROM ps_product')"
    echo "kategorie: $(sql 'SELECT COUNT(*) FROM ps_category')"
    echo "klienci: $(sql 'SELECT COUNT(*) FROM ps_customer')"
    echo "zamowienia: $(sql 'SELECT COUNT(*) FROM ps_orders')"
    echo "zdjecia_produktow: $(sql 'SELECT COUNT(*) FROM ps_image')"
    echo ""
    echo "sha256:"
    (cd "$work" && find . -type f ! -name manifest.txt | sort | xargs sha256sum)
} > "$work/manifest.txt"

# 6. Jedno archiwum; najpierw .part, żeby przerwany zapis nie wyglądał na gotową kopię
tar -C "$work" -cf "$BACKUP_DIR/$name.tar.part" .
mv "$BACKUP_DIR/$name.tar.part" "$BACKUP_DIR/$name.tar"

elapsed=$(( $(date +%s) - start ))
log "gotowe w $(( elapsed / 60 )) min $(( elapsed % 60 )) s: $BACKUP_DIR/$name.tar ($(du -h "$BACKUP_DIR/$name.tar" | cut -f1))"
sed -n '1,8p' "$work/manifest.txt" | sed 's/^/  /'
log "odtworzenie: make restore BACKUP=$BACKUP_DIR/$name.tar"
