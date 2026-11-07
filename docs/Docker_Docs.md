# Opis architektury kontenerów

Stan architektury będzie rozwijany w czasie, a niniejszy plik aktualizowany.

## Dockerfile

**Dockerfile** bazuje na obrazie kontenera Prestashop w wersji zgodnej z wymaganiami i kopiuje do niego motyw potomny:

```dockerfile
COPY --chown=www-data:www-data themes/custom-child-theme /var/www/html/themes/custom-child-theme
```

Właścicielem musi być `www-data` (użytkownik Apache), bo PrestaShop zapisuje w katalogu motywu cache CSS/JS. Skrypt startowy obrazu dokopiowuje pliki PrestaShop z `cp -n` (bez nadpisywania), więc skopiowany motyw zostaje nienaruszony. Kolejne moduły własne dodajemy analogicznie, kolejnymi liniami *COPY*.

Sam `COPY` tylko udostępnia motyw — aktywuje go `make theme` (`bin/console prestashop:theme:enable`), ponieważ aktywny motyw jest zapisany w bazie danych.

Drugi `COPY` dodaje skrypty uruchamiane przy każdym starcie kontenera:

```dockerfile
COPY --chmod=755 init-scripts/ /tmp/init-scripts/
```

Skrypt startowy obrazu (`docker_run.sh`) wykonuje po kolei wszystkie pliki z `/tmp/init-scripts/` po zakończeniu instalacji, tuż przed uruchomieniem serwera WWW. Obraz uruchamia te pliki bezpośrednio, dlatego `--chmod=755` nadaje bit wykonywalny niezależnie od uprawnień pliku w repozytorium. Obecnie są tam dwa skrypty: konfiguracja poczty (`10-configure-mail.sh`) i konfiguracja sprzedaży (`20-configure-sales.sh`), opisane w sekcji o kontenerze `shop`. Prefiks liczbowy ustala kolejność uruchamiania.

Trzeci `COPY` dodaje skrypty PHP wywoływane przez init-scripts:

```dockerfile
COPY --chmod=755 scripts/ /usr/local/share/shop-init/
```

Nie mogą leżeć w `/tmp/init-scripts/`, bo `docker_run.sh` uruchomiłby je bezpośrednio — jako root i bez interpretera PHP, co przy `set -e` zatrzymałoby start kontenera. `--chmod=755` dotyczy też samego katalogu, który bez bitu `x` nie byłby dostępny.

## Plik compose.yaml

Póki co plik zawiera kontener sklepu, reverse proxy (nginx), serwer poczty testowej (Mailpit) oraz bazy danych, która bazuje na wolumenie.

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

#### Certyfikat

Certyfikat jest samopodpisany i generowany przez skrypt `deploy/nginx/docker-entrypoint.d/05-generate-cert.sh`, który entrypoint obrazu nginx uruchamia przed startem serwera:
- jeżeli `tls.crt` i `tls.key` już istnieją w wolumenie, generowanie jest pomijane,
- w przeciwnym razie `openssl` tworzy certyfikat RSA 2048 ważny 10 lat, z `subjectAltName` obejmującym `SERVER_NAME`, `localhost` i `127.0.0.1` (przeglądarki weryfikują SAN, a nie `CN`),
- klucz prywatny jest zapisywany bez hasła (`-noenc`), ponieważ nginx nie może go odblokować przy starcie.

Certyfikat nie trafia do repozytorium. Zmiana `SERVER_NAME` po pierwszym uruchomieniu nie wygeneruje nowego certyfikatu, ponieważ stary pozostaje w wolumenie. W takiej sytuacji należy wykonać `make reset`.

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