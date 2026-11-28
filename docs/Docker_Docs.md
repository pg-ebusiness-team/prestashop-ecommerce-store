# Opis architektury kontenerów

Stan architektury będzie rozwijany w czasie, a niniejszy plik aktualizowany.

## Dockerfile

**Dockerfile** bazuje na obrazie kontenera Prestashop w wersji zgodnej z wymaganiami i kopiuje do niego motyw potomny:

```dockerfile
COPY --chown=www-data:www-data themes/custom-child-theme /usr/local/share/shop-theme/custom-child-theme
```

Motyw trafia poza `/var/www/html`, bo cały ten katalog jest wolumenem `shop_data` (sekcja o kontenerze `shop`). Docker kopiuje zawartość obrazu do nazwanego wolumenu tylko raz, gdy wolumen jest pusty. Plik skopiowany prosto do `/var/www/html/themes/` byłby więc w sklepie tylko w wersji z pierwszego uruchomienia, a kolejne zmiany motywu nie byłyby widoczne. Do katalogu `themes/` w wolumenie kopiuje go przy każdym starcie kontenera init-script `00-sync-theme.sh` (opis niżej).

Właścicielem musi być `www-data` (użytkownik Apache), bo PrestaShop zapisuje w katalogu motywu cache CSS/JS. Kolejne moduły własne dodajemy analogicznie: kopia z obrazu poza wolumen i synchronizacja w init-scripcie.

Sam motyw w plikach nie wystarczy. Aktywuje go `make theme` (`bin/console prestashop:theme:enable`), ponieważ aktywny motyw jest zapisany w bazie danych.

Drugi `COPY` dodaje skrypty uruchamiane przy każdym starcie kontenera:

```dockerfile
COPY --chmod=755 init-scripts/ /tmp/init-scripts/
```

Skrypt startowy obrazu (`docker_run.sh`) wykonuje po kolei wszystkie pliki z `/tmp/init-scripts/` po zakończeniu instalacji, tuż przed uruchomieniem serwera WWW. Obraz uruchamia te pliki bezpośrednio, dlatego `--chmod=755` nadaje bit wykonywalny niezależnie od uprawnień pliku w repozytorium. Obecnie jest tam pięć skryptów: synchronizacja motywu (`00-sync-theme.sh`), dopasowanie do zmiennych środowiskowych (`02-sync-env.sh`), rozgrzanie cache (`05-cache-warmup.sh`), konfiguracja poczty (`10-configure-mail.sh`) i konfiguracja sprzedaży (`20-configure-sales.sh`), opisane w sekcji o kontenerze `shop`. Prefiks liczbowy ustala kolejność uruchamiania.

Trzeci `COPY` dodaje skrypty PHP wywoływane przez init-scripts:

```dockerfile
COPY --chmod=755 scripts/ /usr/local/share/shop-init/
```

Nie mogą leżeć w `/tmp/init-scripts/`, bo `docker_run.sh` uruchomiłby je bezpośrednio — jako root i bez interpretera PHP, co przy `set -e` zatrzymałoby start kontenera. `--chmod=755` dotyczy też samego katalogu, który bez bitu `x` nie byłby dostępny.

## Plik compose.yaml

Plik zawiera kontener sklepu, reverse proxy (nginx), serwer poczty testowej (Mailpit), bazę danych oraz kontener narzędziowy `tools` do inicjalizacji danych. Sklep, baza i certyfikat proxy przechowują dane w nazwanych wolumenach (`shop_data`, `db_data`, `proxy_certs`). Usuwa je dopiero `make reset` (`docker compose down -v`) albo `make restore`, który zastępuje je kopią zapasową ([Backup.md](Backup.md)).

### Kontener shop

Zbudowanie kontenera z obrazu w katalogu **../shop**, a następnie nazwanie go:

```yaml
build: ../shop
image: shop:dev
```

Wymuszenie platformy w celu spełnienia narzuconych wymagań:

```yaml
platform: linux/amd64
```

Zmienne środowiskowe:
- DB_SERVER - miejsce instancji mysql
- DB_NAME - nazwa bazy danych
- DB_USER - nazwa użytkownika w bazie danych
- DB_PASSWD - hasło użytkownika w bazie danych
- PS_INSTALL_AUTO - flaga inicjalizująca automatyczną instalację prestashop po uruchomieniu kontenera
- PS_LANGUAGE - bazowy język w Prestashop
- PS_COUNTRY - bazowy kraj w Prestashop. Musi być zapisany **małymi literami** (`pl`): instalator wczytuje pakiet lokalizacyjny z pliku `localization/<kraj>.xml`, a przy `PL` nie znajduje `PL.xml` (system plików rozróżnia wielkość liter) i po cichu bierze `default.xml` — sklep nie ma wtedy waluty PLN ani polskich stawek VAT. Wartość jest stosowana tylko przy pierwszej instalacji, więc jej zmiana wymaga `make reset`.
- PS_DOMAIN - adres sklepu
- ADMIN_MAIL - mail użytkownika admin, używany w panelu admina
- ADMIN_PASSWD - hasło użytkownika admin
- PS_FOLDER_ADMIN - miejsce panelu admina. Adres: PS_DOMAIN/PS_FOLDER_ADMIN
- PS_ENABLE_SSL - włącza HTTPS w sklepie. Wartość jest zapisywana w bazie przy pierwszej instalacji.
- MAIL_SMTP_HOST - nazwa serwera SMTP, czyli nazwa usługi z Mailpitem (`mail`) w sieci Dockera. Musi być zgodna z nazwą usługi w pliku `compose.yaml`.
- MAIL_SMTP_PORT - port serwera SMTP (Mailpit domyślnie nasłuchuje na 1025).
- FREE_SHIPPING_THRESHOLD - kwota w zł brutto, od której (włącznie) dostawa jest darmowa (wymaganie: 2000).
- MAX_ORDER_WEIGHT_KG - maksymalna waga zamówienia w kg; cięższe zamówienie nie ma dostępnego przewoźnika (wymaganie: 50).

FREE_SHIPPING_THRESHOLD i MAX_ORDER_WEIGHT_KG to reguły sklepu z wymagań, takie same dla wszystkich, dlatego są wpisane bezpośrednio w `compose.yaml` (zmiana przechodzi przez PR), a nie w `.env`, który służy sekretom i ustawieniom zależnym od komputera. Zmiana: edycja wartości i `make up`, bez przebudowy bazy.

Kontener nie publikuje portów na hoście. Cały ruch przechodzi przez kontener `proxy`, co gwarantuje, że sklep jest dostępny wyłącznie przez HTTPS.

#### Wolumen z plikami sklepu

```yaml
volumes:
  - shop_data:/var/www/html
```

W wolumenie są wszystkie pliki sklepu, w tym zdjęcia produktów (`img/`), plik `app/config/parameters.php` z konfiguracją instalacji, katalog panelu admina i moduły. Bez wolumenu pliki te żyły w warstwie kontenera i znikały przy każdym jego odtworzeniu (`make down` i `make up`, `make up` po zmianie obrazu). `docker_run.sh` rozpoznaje zainstalowany sklep wyłącznie po `app/config/parameters.php`, więc nowy kontener instalował PrestaShop od nowa na istniejącej bazie, a import i zamówienia przepadały.

Kopię całego wolumenu (bez zawartości `var/cache` i `var/logs`) robi `make backup`, a odtwarza `make restore` ([Backup.md](Backup.md)).

Motyw i skrypty z obrazu leżą poza wolumenem (`/usr/local/share/`, `/tmp/init-scripts/`), więc ich zmiany docierają do sklepu po `make up` (motyw przez `00-sync-theme.sh`).

#### Healthcheck

```yaml
healthcheck:
  test: ["CMD", "curl", "-fsS", "-o", "/dev/null", "http://localhost/"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 15m
```

Co 10 s zapytanie z wnętrza kontenera do Apache, z pominięciem proxy. `docker_run.sh` uruchamia Apache dopiero po instalacji i init-scriptach, więc odpowiedź oznacza, że sklep jest gotowy. Po HTTP sklep odpowiada przekierowaniem na HTTPS (302), które `curl -f` uznaje za sukces. Do tego przekierowania PrestaShop musi wczytać konfigurację z bazy, więc przy niedostępnej bazie odpowiedź to 500 i healthcheck nie przechodzi. Strona nie jest przy tym renderowana, a zapytanie trwa kilka milisekund.

`start_period: 15m` to okres ochronny na pierwszą instalację: nieudane próby w tym czasie się nie liczą, a pierwsza udana od razu daje status *healthy*. Później 3 nieudane próby z rzędu dają status *unhealthy*.

Healthcheck nie sprawdza proxy, HTTPS ani danych. Służy do tego, żeby `make up` (`docker compose up --wait`) kończył się dopiero po instalacji, a `make init` (`check-shop`) nie startował wcześniej. W etapie 2 Docker Swarm użyje go do restartu usługi i aktualizacji bez przerwy.

#### Synchronizacja motywu (init-scripts)

`shop/init-scripts/00-sync-theme.sh` przy każdym starcie podmienia katalog `themes/custom-child-theme` w wolumenie na wersję z obrazu (`/usr/local/share/shop-theme/`). Kopiuje go obok i zamienia nazwy, żeby Apache nie trafił na niepełny motyw. Katalog jest podmieniany w całości, więc pliki usunięte z repo znikają też ze sklepu. Ręczne zmiany plików motywu w kontenerze są przy restarcie nadpisywane, bo źródłem prawdy jest repo. Ustawienia z panelu są w bazie i w `img/`, więc ich to nie dotyczy.

#### Dopasowanie do zmiennych środowiskowych (init-scripts)

Instalator zapisuje część ustawień środowiska tylko raz, przy pierwszej instalacji, i potem sklep nie czyta ich już ze zmiennych:

| Ustawienie | Gdzie je zapisał instalator | Zmienna (z `.env`) |
|---|---|---|
| dane bazy | `app/config/parameters.php` w wolumenie | `DB_SERVER`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWD` (`MYSQL_*`) |
| domena i SSL | baza: `ps_shop_url`, `PS_SHOP_DOMAIN`, `PS_SHOP_DOMAIN_SSL`, `PS_SSL_ENABLED`, `PS_SSL_ENABLED_EVERYWHERE`; plik `.htaccess` (reguły zdjęć mają warunek `RewriteCond %{HTTP_HOST} ^<domena>$`) | `PS_DOMAIN` (`SERVER_NAME:HTTPS_PORT`), `PS_ENABLE_SSL` |
| katalog panelu admina | nazwa katalogu (`docker_run.sh` zmienia `admin` na `PS_FOLDER_ADMIN` tylko przy instalacji) | `PS_FOLDER_ADMIN` (`ADMIN_FOLDER`) |

`shop/init-scripts/02-sync-env.sh` uruchamia przy każdym starcie jako `www-data` plik `shop/scripts/sync-env.php` (w obrazie `/usr/local/share/shop-init/sync-env.php`), który doprowadza te miejsca do wartości zmiennych:
1. dane bazy w `parameters.php`, bez ładowania PrestaShop, bo ten ze złymi danymi bazy by nie wystartował. Zapis w formacie instalatora do pliku obok i zamiana nazwy, potem usunięcie cache Symfony, w którym jest skompilowana kopia parametrów. W logu są tylko nazwy zmienionych pól, bez wartości,
2. nazwa katalogu admina. Panel jest rozpoznawany po `index.php` z `_PS_ADMIN_DIR_`. Gdy nie ma dokładnie jednego kandydata, skrypt tylko ostrzega, bo sklep dla klientów działa bez panelu,
3. domena i SSL przez klasy PrestaShop (`ShopUrl`, `Configuration::updateGlobalValue`). `.htaccess` jest generowany od nowa (`Tools::generateHtaccess()`), gdy nie ma w nim `#Domain: <domena>`. Po zmianach czyszczony jest cache Smarty i Symfony.

Skrypt jest przed `05-cache-warmup.sh`, bo ten już ładuje PrestaShop i potrzebuje poprawnych danych bazy. Cache usunięty przez `02-sync-env` od razu odbudowuje `05-cache-warmup`.

Przy zgodnych wartościach, czyli przy zwykłym restarcie, skrypt niczego nie zapisuje i wypisuje `02-sync-env: sklep zgodny ze zmiennymi srodowiskowymi`. Zmiany są potrzebne w dwóch sytuacjach:
- po `make restore`, gdy baza i pliki pochodzą z kopii zrobionej z innym `.env` ([Backup.md](Backup.md)),
- po zmianie portu, domeny lub hasła bazy w `.env`. Wystarczy `make up`, bez `make reset`. Wyjątkiem jest `MYSQL_PASSWORD`: obraz MySQL zakłada użytkownika tylko przy tworzeniu wolumenu `db_data`, więc na istniejącej bazie trzeba też zmienić hasło w MySQL (`ALTER USER`), inaczej `docker_run.sh` czeka na bazę bez końca.

Błąd (np. baza odrzuca dane logowania) **zatrzymuje start kontenera** (kod 1, linia `02-sync-env: BLAD: ...`), tak jak w konfiguracji sprzedaży. Sklep z niezgodnymi danymi bazy lub domeną i tak by nie działał, a kontener, który nie wstaje, widać w `make ps`.

Ten sam mechanizm spełnia wymaganie D1 etapu 2: „Domena i ustawienia SSL przez zmienne środowiskowe, nie na stałe w zrzucie bazy”.

#### Rozgrzanie cache (init-scripts)

`shop/init-scripts/05-cache-warmup.sh` przy każdym starcie wykonuje jako `www-data` `bin/console cache:warmup --env=prod` (ok. 1 s). Warmer PrestaShop (`src/PrestaShopBundle/Cache/CacheWarmer.php`) tworzy w `var/cache/prod/` katalogi `purifier`, `tcpdf`, `cachefs`, `push` i `sandbox`. Instalator ich nie tworzy, a bez nich zapis produktu z opisem HTML przez API kończy się HTTP 500 (brak `purifier`), a generowanie PDF faktury może się nie udać (brak `tcpdf`). Wcześniej tworzył je przypadkiem `cache:clear` z `make theme` uruchamiany przed importem. Błąd jest zgłaszany komunikatem `BLAD`, ale nie zatrzymuje kontenera, bo sklep działa bez tych katalogów, a nie działa tylko import i faktury.

#### Konfiguracja poczty (init-scripts)

Obraz PrestaShop nie ma zmiennych środowiskowych do konfiguracji SMTP, a ustawienia poczty są zapisywane w bazie danych. Dlatego skrypt `shop/init-scripts/10-configure-mail.sh` ustawia je przez konsolę PrestaShop (`bin/console prestashop:config set`):
- PS_MAIL_METHOD = 2 - wysyłka przez własny serwer SMTP
- PS_MAIL_SERVER = MAIL_SMTP_HOST - adres serwera SMTP
- PS_MAIL_SMTP_PORT = MAIL_SMTP_PORT - port serwera SMTP
- PS_MAIL_SMTP_ENCRYPTION = off - Mailpit nie używa TLS ani logowania, dlatego PS_MAIL_USER i PS_MAIL_PASSWD zostają puste

Skrypt jest w `init-scripts`, a nie w `make init`, ponieważ adres SMTP to konfiguracja środowiska (podobnie jak domena i SSL), a nie dane sklepu. Jest stosowana przy każdym starcie kontenera na podstawie zmiennych środowiskowych, więc zmiana serwera SMTP nie wymaga ręcznych kroków ani zmian w bazie.

Szczegóły działania skryptu:
- jeżeli sklep nie jest zainstalowany (brak `app/config/parameters.php`), skrypt nic nie robi,
- konsola jest uruchamiana jako `www-data` (`runuser`, tak jak robi to instalator w obrazie). Uruchomiona jako root utworzyłaby w `var/cache` pliki, do których Apache nie mógłby zapisywać,
- skrypt zawsze kończy się kodem 0. `docker_run.sh` działa z `set -e`, więc kod różny od zera zatrzymałby start całego kontenera, a błąd konfiguracji poczty nie powinien wyłączać sklepu. Problemy są zgłaszane komunikatem `BLAD` w logach (`make logs SERVICE=shop`),
- ponowne uruchomienie ustawia te same wartości, więc nie powoduje skutków ubocznych.

#### Konfiguracja sprzedaży (init-scripts)

Skrypt `shop/init-scripts/20-configure-sales.sh` uruchamia jako `www-data` plik `shop/scripts/configure-sales.php` (w obrazie `/usr/local/share/shop-init/configure-sales.php`). Skrypt PHP ładuje PrestaShop (`config/config.inc.php`) i ustawia, korzystając z klas PrestaShop:
- kraje - aktywna tylko Polska,
- płatności - przelew tradycyjny i płatność przy odbiorze, odinstalowanie płatności czekiem, dane do przelewu, faktura od razu przy zamówieniu za pobraniem,
- przewoźników - dwóch kurierów z cenami brutto i VAT 23%, wyłączenie przewoźników z instalatora i danych demo,
- ograniczenia - darmowa dostawa od `FREE_SHIPPING_THRESHOLD` i limit wagi `MAX_ORDER_WEIGHT_KG` (zmienne z `compose.yaml`).

Uzasadnienie wyboru PHP zamiast SQL i `bin/console` jest w `docs/adr/0003-konfiguracja-sprzedazy.md`, a opis ustawień w README (sekcja „Płatności i dostawa”).

Różnice względem skryptu poczty:
- błąd konfiguracji **zatrzymuje start kontenera** (kod 1). Sklep z ustawieniami z instalatora (płatność czekiem, domyślni przewoźnicy) nie spełniałby wymagań, a sam komunikat w logu łatwo przeoczyć. Kontener, który nie wstaje, widać w `make ps`, a przyczynę w logu jako `20-configure-sales: BLAD: ...`,
- skrypt nadpisuje zmiany wprowadzone w panelu administratora (źródłem prawdy jest repo); jest idempotentny — przewoźników rozpoznaje po `id_reference` zapisanym w konfiguracji, więc restart nie tworzy duplikatów.

### Kontener proxy

Reverse proxy oparte na nginx. Kończy połączenie HTTPS, przekierowuje HTTP na HTTPS i przekazuje ruch do kontenera `shop`. Zbudowany z katalogu **./nginx** (obraz bazowy `nginx:alpine`), a następnie nazwany:

```yaml
build: ./nginx
image: proxy:dev
```

Wymuszenie platformy w celu spełnienia narzuconych wymagań:

```yaml
platform: linux/amd64
```

Zmienne środowiskowe:
- SERVER_NAME - nazwa serwera użyta w konfiguracji nginx i w certyfikacie
- HTTPS_PORT - port HTTPS widoczny na hoście, używany w adresie przekierowania 301

Mapowanie portów (porty po prawej stronie to porty wewnątrz kontenera):

```yaml
ports:
  - "${HTTP_PORT}:80"
  - "${HTTPS_PORT}:443"
```

Do jakiego katalogu w kontenerze będzie montowany wolumen z certyfikatem:

```yaml
volumes:
  - proxy_certs:/etc/nginx/certs
```

Kontener sklepu musi istnieć przed startem nginx:

```yaml
depends_on:
  - shop
```

Nginx rozwiązuje nazwę `shop` przy starcie, a przy jej braku kończy się błędem `host not found in upstream`. Nie jest to oczekiwanie na gotowość sklepu.

#### Konfiguracja nginx

Konfiguracja znajduje się w pliku `deploy/nginx/templates/default.conf.template`. Oficjalny obraz nginx przetwarza pliki `*.template` z katalogu `/etc/nginx/templates/` programem `envsubst` i zapisuje wynik w `/etc/nginx/conf.d/`. Podmieniane są tylko zmienne środowiskowe istniejące w kontenerze, więc zmienne nginx, takie jak `$request_uri`, pozostają bez zmian. Nazwa `default.conf.template` powoduje nadpisanie domyślnego `default.conf` z obrazu.

Konfiguracja zawiera dwa bloki:
- port 80 - `return 301` na `https://${SERVER_NAME}:${HTTPS_PORT}$request_uri`. Adres docelowy nie zależy od nagłówka `Host` wysłanego przez klienta, więc nie ma ryzyka open redirectu. Użycie `$request_uri` zachowuje ścieżkę i parametry zapytania.
- port 443 - TLS oraz `proxy_pass` do `shop:80` z nagłówkami `Host` (razem z portem), `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto` i `X-Forwarded-Port`. Dzięki `X-Forwarded-Proto` PrestaShop rozpoznaje, że klient połączył się przez HTTPS.
  - `proxy_redirect http://$http_host/ https://$http_host/` - Apache w kontenerze `shop` (moduł `mod_dir`, `DirectorySlash`) odpowiada na adres katalogu bez końcowego `/` (np. `/<ADMIN_FOLDER>`, `/modules`) przekierowaniem 301. Adres w nagłówku `Location` składa z nagłówka `Host` i własnego schematu `http`, bo `X-Forwarded-Proto` odczytuje tylko PrestaShop, a nie Apache. Bez tej dyrektywy przeglądarka trafiałaby na `http://<host>:<HTTPS_PORT>/...`, czyli HTTP na porcie TLS (błąd 400 nginx). Przepisywane są tylko przekierowania na własny host sklepu, adresy zewnętrzne zostają bez zmian.

#### Certyfikat

Certyfikat jest samopodpisany i generowany przez skrypt `deploy/nginx/docker-entrypoint.d/05-generate-cert.sh`, który entrypoint obrazu nginx uruchamia przed startem serwera:
- jeżeli `tls.crt` i `tls.key` już istnieją w wolumenie, generowanie jest pomijane,
- w przeciwnym razie `openssl` tworzy certyfikat RSA 2048 ważny 10 lat, z `subjectAltName` obejmującym `SERVER_NAME`, `localhost` i `127.0.0.1` (przeglądarki weryfikują SAN, a nie `CN`),
- klucz prywatny jest zapisywany bez hasła (`-noenc`), ponieważ nginx nie może go odblokować przy starcie.

Certyfikat nie trafia do repozytorium. Zmiana `SERVER_NAME` po pierwszym uruchomieniu nie wygeneruje nowego certyfikatu, ponieważ stary pozostaje w wolumenie. W takiej sytuacji usuń sam wolumen z certyfikatem (`make down`, `docker volume rm deploy_proxy_certs`, `make up`). Domenę w sklepie dopasuje `02-sync-env.sh`, więc `make reset` nie jest potrzebny.

### Kontener mail

Serwer poczty testowej Mailpit. Przechwytuje e-maile wysyłane przez sklep (m.in. po rejestracji i po złożeniu zamówienia) i nie dostarcza ich do prawdziwych adresatów. Używa gotowego obrazu, więc nie ma własnego Dockerfile:

```yaml
image: axllent/mailpit:v1.32.0
platform: linux/amd64
```

Wersja obrazu jest przypięta do konkretnego tagu, a nie do `latest`, aby środowisko było powtarzalne.

Mapowanie portu interfejsu WWW:

```yaml
ports:
  - "${MAILPIT_PORT}:8025"
```

Port 8025 to interfejs WWW Mailpit (HTTP, bez TLS). To narzędzie deweloperskie, a wymóg HTTPS dotyczy sklepu. Port SMTP (1025) nie jest publikowany na hoście, bo sklep łączy się z Mailpitem wewnątrz sieci Dockera.

Nazwa usługi (`mail`) jest jednocześnie nazwą DNS w sieci Dockera, pod którą sklep widzi serwer SMTP. Dlatego musi być zgodna z `MAIL_SMTP_HOST` w usłudze `shop` (w pliku jest o tym komentarz). Niezgodność nie powoduje błędu w logach, tylko brak wiadomości w Mailpicie.

Usługa nie ma wolumenu, więc wiadomości nie są zapisywane trwale i znikają po usunięciu kontenera.

### Kontener db

Obraz kontenera oraz wymagana platforma:

```yaml
image: mysql:8.0
platform: linux/amd64
```

Flagi konfiguracyjne potrzebne, aby baza przechowywała polskie znaki:

```yaml
command:
  - --character-set-server=utf8mb4
  - --collation-server=utf8mb4_unicode_ci
```

Zmienne środowiskowe:
- MYSQL_ROOT_PASSWORD - hasło użytkownika *root*
- MYSQL_DATABASE - nazwa bazy danych w instancji
- MYSQL_USER - użytkownik mający dostęp tylko do tej bazy danych
- MYSQL_PASSWORD - hasło powyższego użytkownika

Do jakiego katalogu w kontenerze będzie montowany wolumen:

```yaml
volumes:
  - db_data:/var/lib/mysql
```

### Kontener tools

Kontener narzędziowy do inicjalizacji danych: importer i scraper w Pythonie, bez instalowania Pythona na hoście. Uruchamia go makefile (`make init`, `make import`, `make photos`, `make cleanup-demo`) jako jednorazowe zadanie, które po zakończeniu jest usuwane:

```make
TOOLS = $(COMPOSE) run --rm --no-deps --build --user $(shell id -u):$(shell id -g) tools
```

- `--rm` usuwa kontener po zakończeniu polecenia,
- `--no-deps` nie buduje ani nie uruchamia innych usług, bo sklep musi już działać po `make up`. Dlatego usługa nie ma `depends_on`,
- `--build` przebudowuje obraz po zmianie `scraper/requirements.txt`, a bez zmian bierze go z cache w poniżej sekundy,
- `--user` sprawia, że pliki zapisane w zamontowanym repo (zdjęcia, `scraper/importer/*_mapping.json`) należą do użytkownika hosta, a nie do roota.

Obraz budowany jest z `deploy/tools/Dockerfile` (`python:3.12-slim`, zależności z `scraper/requirements.txt`, `curl` i `unzip` do archiwum zdjęć):

```yaml
build:
  context: ../scraper
  dockerfile: ../deploy/tools/Dockerfile
image: tools:dev
platform: linux/amd64
```

Kontekstem budowania jest `scraper/`, bo obraz potrzebuje tylko `requirements.txt`. Kontekst całego repo obejmowałby wyniki scrapera i zdjęcia. Kod nie jest kopiowany do obrazu, tylko montowany, więc jego zmiany działają bez przebudowy:

```yaml
volumes:
  - ..:/app
```

Usługa nie startuje przy `make up`, bo należy do profilu:

```yaml
profiles: [tools]
```

Zmienne środowiskowe:
- SHOP_URL - adres sklepu w sieci Dockera (`https://proxy`), a nie `localhost`, który w kontenerze oznacza sam kontener,
- PS_SHOP_HOST - domena sklepu (`SERVER_NAME:HTTPS_PORT`) wysyłana w nagłówku `Host` (`scraper/importer/api_client.py`). PrestaShop odpowiada przekierowaniem 302 na swoją domenę na zapytania pod innym adresem, więc bez tego nagłówka API pod `https://proxy` nie działa,
- PYTHONWARNINGS - wycisza ostrzeżenie urllib3 o samopodpisanym certyfikacie (`PS_VERIFY_SSL=0`), które pojawiałoby się przy każdym zapytaniu.

Pozostałe ustawienia (`PS_API_KEY`, `PS_TAX_RULES_GROUP_MAP`, `PS_VERIFY_SSL`) importer wczytuje sam z `/app/.env` (`load_env_file` w `scraper/importer/main.py`), dlatego usługa nie ma `env_file`. Zmiennych już ustawionych nie nadpisuje, więc wartości z `environment` mają pierwszeństwo.
