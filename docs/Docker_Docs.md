# Opis architektury kontenerów

Stan architektury będzie rozwijany w czasie, a niniejszy plik aktualizowany.

## Dockerfile

**Dockerfile** bazuje na obrazie kontenera Prestashop w wersji zgodnej z wymaganiami i kopiuje do niego motyw potomny:

```dockerfile
COPY --chown=www-data:www-data themes/custom-child-theme /var/www/html/themes/custom-child-theme
```

Właścicielem musi być `www-data` (użytkownik Apache), bo PrestaShop zapisuje w katalogu motywu cache CSS/JS. Skrypt startowy obrazu dokopiowuje pliki PrestaShop z `cp -n` (bez nadpisywania), więc skopiowany motyw zostaje nienaruszony. Kolejne moduły własne dodajemy analogicznie, kolejnymi liniami *COPY*.

Sam `COPY` tylko udostępnia motyw — aktywuje go `make theme` (`bin/console prestashop:theme:enable`), ponieważ aktywny motyw jest zapisany w bazie danych.

## Plik compose.yaml

Póki co plik zawiera kontener sklepu, reverse proxy (nginx) oraz bazy danych, która bazuje na wolumenie.

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
- PS_COUNTRY - bazowy kraj w Prestashop
- PS_DOMAIN - adres sklepu
- ADMIN_MAIL - mail użytkownika admin, używany w panelu admina
- ADMIN_PASSWD - hasło użytkownika admin
- PS_FOLDER_ADMIN - miejsce panelu admina. Adres: PS_DOMAIN/PS_FOLDER_ADMIN
- PS_ENABLE_SSL - włącza HTTPS w sklepie. Wartość jest zapisywana w bazie przy pierwszej instalacji.

Kontener nie publikuje portów na hoście. Cały ruch przechodzi przez kontener `proxy`, co gwarantuje, że sklep jest dostępny wyłącznie przez HTTPS.

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