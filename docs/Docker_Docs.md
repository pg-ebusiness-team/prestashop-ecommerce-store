# Opis architektury kontenerów

Opis uzupełnia komentarze w `shop/Dockerfile` i `deploy/compose.yaml`: wyjaśnia, dlaczego konfiguracja wygląda tak, a nie inaczej.

## Dockerfile (`shop/`)

Obraz bazuje na `prestashop/prestashop:8.2.8` i dodaje:

| `COPY` | Cel w obrazie | Po co |
|---|---|---|
| `themes/custom-child-theme` | `/usr/local/share/shop-theme/` | motyw potomny |
| `modules/omnibusprice` | `/usr/local/share/shop-modules/` | moduł najniższej ceny z 30 dni (README, sekcja „Promocje i Omnibus”) |
| `init-scripts/` (`--chmod=755`) | `/tmp/init-scripts/` | skrypty startowe |
| `scripts/` (`--chmod=755`) | `/usr/local/share/shop-init/` | skrypty PHP wywoływane przez init-scripts |

- **Motyw i moduł są poza `/var/www/html`**, bo ten katalog jest wolumenem `shop_data`. Docker kopiuje zawartość obrazu do wolumenu tylko, gdy jest pusty, więc plik z obrazu w `/var/www/html` zostałby w wersji z pierwszego uruchomienia. Do wolumenu kopiuje je przy każdym starcie `00-sync-theme.sh`. Właścicielem jest `www-data`, bo PrestaShop zapisuje w motywie cache CSS/JS. Kolejne moduły własne dodajemy tak samo: `COPY` poza wolumen i `sync_dir` w `00-sync-theme.sh`.
- Same pliki nie wystarczą: aktywny motyw i zainstalowane moduły są w bazie, dlatego motyw włącza `make theme`, a moduł instaluje `make omnibus-install`.
- **Init-scripts** wykonuje skrypt startowy obrazu (`docker_run.sh`) po instalacji, przed startem Apache, w kolejności prefiksów. Uruchamia je bezpośrednio, stąd `--chmod=755`.
- **Skrypty PHP** nie mogą leżeć w `/tmp/init-scripts/`, bo `docker_run.sh` uruchomiłby je jako root bez interpretera PHP, a przy `set -e` zatrzymałoby to start.

## compose.yaml (`deploy/`)

Usługi: `shop`, `proxy` (nginx), `mail` (Mailpit), `db` (MySQL 8.0) i `tools` (importer, scraper). Wszystkie mają `platform: linux/amd64` (wymaganie). Dane są w wolumenach `shop_data`, `db_data`, `proxy_certs`; usuwa je `make reset` (`down -v`), a zastępuje kopią `make restore` ([Backup.md](Backup.md)).

### shop

Zmienne środowiskowe to dane bazy (`DB_*` z `MYSQL_*` w `.env`), automatyczna instalacja (`PS_INSTALL_AUTO`, `PS_LANGUAGE`, `PS_COUNTRY`, `PS_DOMAIN`, `ADMIN_*`, `PS_FOLDER_ADMIN`, `PS_ENABLE_SSL`), SMTP (`MAIL_SMTP_HOST`, `MAIL_SMTP_PORT`) i reguły sprzedaży (`FREE_SHIPPING_THRESHOLD`, `MAX_ORDER_WEIGHT_KG`). Uwagi:

- `PS_COUNTRY` musi być małymi literami (`pl`). Instalator szuka `localization/<kraj>.xml`; przy `PL` nie znajduje pliku i po cichu bierze `default.xml` — bez PLN i polskich stawek VAT. Działa tylko przy pierwszej instalacji (zmiana wymaga `make reset`).
- `MAIL_SMTP_HOST` musi być nazwą usługi Mailpita (`mail`). Niezgodność nie daje błędu, tylko brak wiadomości.
- Reguły sprzedaży są w `compose.yaml`, a nie w `.env`, bo są takie same dla wszystkich i zmieniają się przez PR (`.env` jest na sekrety i ustawienia komputera). Zmiana: edycja i `make up`.
- Kontener nie publikuje portów — cały ruch idzie przez `proxy`, więc sklep jest dostępny tylko po HTTPS.

**Wolumen `shop_data:/var/www/html`** trzyma wszystkie pliki sklepu: `img/`, `app/config/parameters.php`, katalog admina, moduły. `docker_run.sh` rozpoznaje zainstalowany sklep tylko po `parameters.php`. Bez wolumenu nowy kontener (`make down`/`up`, zmiana obrazu) instalował PrestaShop od nowa na istniejącej bazie i dane przepadały.

**Healthcheck** (`curl -f http://localhost/` co 10 s, `start_period: 15m`) pyta Apache z wnętrza kontenera. Apache startuje dopiero po instalacji i init-scriptach, więc odpowiedź oznacza gotowy sklep. Przekierowanie 302 na HTTPS to sukces; przy niedostępnej bazie PrestaShop zwraca 500. Dzięki temu `make up` (`--wait`) kończy się po instalacji, a `make init` (`check-shop`) nie startuje wcześniej. Proxy, HTTPS ani danych nie sprawdza. W etapie 2 Swarm użyje go do restartów i aktualizacji.

#### Synchronizacja motywu i modułu (init-scripts)

`00-sync-theme.sh` przy każdym starcie podmienia w wolumenie `themes/custom-child-theme` i `modules/omnibusprice` na wersje z obrazu. Kopiuje obok i zamienia nazwy, żeby Apache nie trafił na niepełny katalog. Podmiana jest całościowa: pliki usunięte z repo znikają, ręczne zmiany w kontenerze są nadpisywane. Ustawień z panelu (baza, `img/`) to nie dotyczy. Brak katalogu w obrazie zatrzymuje start (`00-sync-theme: BLAD`).

#### Dopasowanie do zmiennych środowiskowych (init-scripts)

Instalator zapisuje część ustawień tylko raz, potem sklep nie czyta ich ze zmiennych:

| Ustawienie | Gdzie zapisane | Zmienna |
|---|---|---|
| dane bazy | `app/config/parameters.php` | `DB_*` (`MYSQL_*`) |
| domena i SSL | baza (`ps_shop_url`, `PS_SHOP_DOMAIN*`, `PS_SSL_ENABLED*`) i `.htaccess` (reguły zdjęć z warunkiem na domenę) | `PS_DOMAIN` (`SERVER_NAME:HTTPS_PORT`), `PS_ENABLE_SSL` |
| katalog panelu | nazwa katalogu (`docker_run.sh` zmienia ją tylko przy instalacji) | `PS_FOLDER_ADMIN` (`ADMIN_FOLDER`) |

`02-sync-env.sh` uruchamia przy każdym starcie (jako `www-data`) `shop/scripts/sync-env.php`, który:

1. poprawia dane bazy w `parameters.php` bez ładowania PrestaShop (ze złymi danymi by nie wystartował): zapis do pliku obok, zamiana nazwy, usunięcie cache Symfony; w logu tylko nazwy pól,
2. zmienia nazwę katalogu panelu (rozpoznaje go po `index.php` z `_PS_ADMIN_DIR_`; gdy kandydatów nie jest dokładnie jeden, tylko ostrzega),
3. ustawia domenę i SSL klasami PrestaShop, a `.htaccess` generuje od nowa, gdy brak w nim `#Domain: <domena>`; potem czyści cache.

Przy zgodnych wartościach nic nie zapisuje (`02-sync-env: sklep zgodny ze zmiennymi srodowiskowymi`). Zmiany są potrzebne po `make restore` z kopii z innym `.env` i po zmianie portu, domeny lub hasła bazy w `.env` — wystarczy `make up`. Wyjątek: `MYSQL_PASSWORD` na istniejącym wolumenie `db_data` trzeba też zmienić w MySQL (`ALTER USER`), bo obraz MySQL zakłada użytkownika tylko raz. Błąd zatrzymuje start (`02-sync-env: BLAD`). Mechanizm spełnia też D1 etapu 2 (domena i SSL ze zmiennych, nie ze zrzutu bazy).

#### Rozgrzanie cache (init-scripts)

`05-cache-warmup.sh` wykonuje `bin/console cache:warmup --env=prod` (ok. 1 s), który tworzy w `var/cache/prod/` m.in. `purifier` i `tcpdf`. Instalator ich nie zakłada, a bez nich zapis produktu z opisem HTML przez API daje HTTP 500, a faktura PDF może się nie wygenerować. Musi być po `02-sync-env` (potrzebuje poprawnych danych bazy). Błąd jest tylko zgłaszany (`BLAD`), bo sklep działa bez tych katalogów.

#### Konfiguracja poczty (init-scripts)

Obraz nie ma zmiennych SMTP, a ustawienia poczty są w bazie, więc `10-configure-mail.sh` ustawia je przez `bin/console prestashop:config set`: `PS_MAIL_METHOD=2` (SMTP), `PS_MAIL_SERVER`, `PS_MAIL_SMTP_PORT`, szyfrowanie `off` (Mailpit bez TLS i logowania). Jest w init-scripts, a nie w `make init`, bo to konfiguracja środowiska. Pomija niezainstalowany sklep, działa jako `www-data` (pliki cache roota blokowałyby Apache) i zawsze kończy się kodem 0 — błąd poczty nie powinien wyłączać sklepu, jest tylko zgłaszany (`BLAD`).

#### Konfiguracja sprzedaży (init-scripts)

`20-configure-sales.sh` uruchamia `shop/scripts/configure-sales.php`, który klasami PrestaShop ustawia kraje, płatności, przewoźników, darmową dostawę i limit wagi (opis: README, sekcja „Płatności i dostawa”; uzasadnienie: [ADR 0003](adr/0003-konfiguracja-sprzedazy.md)). W odróżnieniu od poczty błąd **zatrzymuje start** (`20-configure-sales: BLAD`), bo sklep z ustawieniami instalatora nie spełnia wymagań. Skrypt nadpisuje zmiany z panelu i jest idempotentny (przewoźników rozpoznaje po `id_reference` zapisanym w konfiguracji).

### proxy

nginx (`deploy/nginx`, obraz `nginx:alpine`) kończy HTTPS, przekierowuje HTTP na HTTPS i przekazuje ruch do `shop`. Publikuje `HTTP_PORT:80` i `HTTPS_PORT:443`, certyfikat trzyma w wolumenie `proxy_certs`. `depends_on: shop` jest potrzebne, bo nginx rozwiązuje nazwę `shop` przy starcie (inaczej `host not found in upstream`); nie czeka na gotowość sklepu.

**Konfiguracja** (`deploy/nginx/templates/default.conf.template`) przechodzi przez `envsubst` obrazu nginx, który podmienia tylko istniejące zmienne środowiskowe (`SERVER_NAME`, `HTTPS_PORT`), a zmienne nginx (`$request_uri`) zostawia.

- port 80: `return 301 https://${SERVER_NAME}:${HTTPS_PORT}$request_uri` — cel nie zależy od nagłówka `Host`, więc nie ma open redirectu,
- port 443: TLS i `proxy_pass` do `shop:80` z `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto` (po nim PrestaShop wie, że jest HTTPS) i `X-Forwarded-Port`,
- `proxy_redirect http://$http_host/ https://$http_host/`: Apache (`mod_dir`) przekierowuje katalogi bez `/` (np. `/<ADMIN_FOLDER>`) na adres ze schematem `http`, bo nie czyta `X-Forwarded-Proto`. Bez tego przeglądarka trafiałaby HTTP-em na port TLS (błąd 400).

**Certyfikat** generuje `deploy/nginx/docker-entrypoint.d/05-generate-cert.sh`, gdy w wolumenie nie ma `tls.crt` i `tls.key`: RSA 2048, 10 lat, SAN z `SERVER_NAME`, `localhost` i `127.0.0.1`, klucz bez hasła (nginx nie odblokuje go przy starcie). Nie trafia do repo. Po zmianie `SERVER_NAME` stary certyfikat zostaje; nowy: `make down`, `docker volume rm deploy_proxy_certs`, `make up`.

### mail

Mailpit (`axllent/mailpit:v1.32.0`, przypięta wersja dla powtarzalności) przechwytuje e-maile sklepu. Publikowany jest tylko interfejs WWW (`MAILPIT_PORT:8025`, HTTP — wymóg HTTPS dotyczy sklepu); SMTP (1025) działa w sieci Dockera pod nazwą usługi `mail`. Bez wolumenu — wiadomości znikają z kontenerem.

### db

`mysql:8.0` z `utf8mb4` / `utf8mb4_unicode_ci` (polskie znaki), dane w `db_data`. Zmienne `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` z `.env`; użytkownik ma dostęp tylko do bazy sklepu.

### tools

Kontener z Pythonem do importera i scrapera, żeby nie instalować Pythona na hoście. Nie startuje przy `make up` (`profiles: [tools]`); makefile uruchamia go jednorazowo (`make init`, `import*`, `photos`, `cleanup-demo`):

```make
TOOLS = $(COMPOSE) run --rm --no-deps --build --user $(shell id -u):$(shell id -g) tools
```

- `--rm` usuwa kontener po poleceniu, `--no-deps` nie uruchamia innych usług (sklep ma już działać, stąd brak `depends_on`),
- `--build` przebudowuje obraz po zmianie `scraper/requirements.txt` (bez zmian — z cache),
- `--user` sprawia, że pliki zapisane w repo (zdjęcia, `*_mapping.json`) należą do użytkownika hosta.

Obraz: `deploy/tools/Dockerfile` (`python:3.12-slim`, `requirements.txt`, `curl`, `unzip`). Kontekst to `scraper/`, bo całe repo obejmowałoby wyniki i zdjęcia. Kod nie jest kopiowany, tylko montowany (`..:/app`), więc zmiany działają bez przebudowy.

Zmienne: `SHOP_URL=https://proxy` (adres sklepu w sieci Dockera; `localhost` to sam kontener), `PS_SHOP_HOST` (domena w nagłówku `Host` — pod innym adresem PrestaShop odpowiada 302 na swoją domenę), `PYTHONWARNINGS` (wycisza ostrzeżenie o samopodpisanym certyfikacie). Resztę (`PS_API_KEY`, `PS_TAX_RULES_GROUP_MAP`, `PS_VERIFY_SSL`) importer czyta sam z `/app/.env`, nie nadpisując zmiennych z `environment`.
