# Webservice API (BACK-1)

Konfiguracja PrestaShop Webservice API, z którego korzysta skrypt importu danych ze scrapera (wymaganie D2 etapu 1).

## Co robi konfiguracja

- włącza Webservice API (`PS_WEBSERVICE = 1`),
- rejestruje jeden klucz API pobierany z `.env` (`PS_API_KEY`),
- ogranicza klucz do metod GET, POST, PUT, DELETE na zasobach: `categories`, `products`, `combinations`, `stock_availables`, `images`, `product_options`, `product_option_values`, `product_features`, `product_feature_values`. Dostęp do pozostałych zasobów (np. `customers`, `orders`) kończy się odpowiedzią 401.

Wszystko dzieje się skryptem — bez klikania w panelu administracyjnym, bo wymagania zakładają jedną komendę inicjalizacji (`make init`), a w etapie 2 inicjalizację bez ręcznych kroków.

## Uruchomienie

```bash
openssl rand -hex 16 | tr a-f A-F   # wygenerowanie klucza; wynik wpisać do .env jako PS_API_KEY
make up                              # poczekać, aż w `make logs` pojawi się "Almost ! Starting web server now"
make init                            # włączenie API, rejestracja klucza i usunięcie danych demo
make api-check                       # weryfikacja
```

Oczekiwany wynik `make api-check`:

```
OK   api/ z kluczem -> 200
OK   api/products z kluczem -> 200
OK   api/customers z kluczem (brak uprawnien) -> 401
OK   api/ bez klucza -> 401
```

Przykładowe zapytanie (klucz jako login Basic Auth, hasło puste):

```bash
curl -k -H "Authorization: Basic $(printf %s: "$PS_API_KEY" | base64)" https://localhost:8443/api/products
```

Sklep jest dostępny wyłącznie przez HTTPS, a certyfikat jest samopodpisany, dlatego `curl` wymaga `-k`. Adres i port zależą od `SERVER_NAME` i `HTTPS_PORT` z `.env` (bazowo `localhost:8443`).

## Klucz API i bezpieczeństwo

- Klucz trzymamy wyłącznie w `.env`, który jest w `.gitignore` (razem z `.env.*`, poza `.env.example`). W repozytorium jest tylko `PS_API_KEY=your_api_key_here` w `.env.example`.
- PrestaShop wymaga klucza o długości dokładnie 32 znaków `A-Z0-9`. `make init` sprawdza format przed wysłaniem czegokolwiek do bazy — zły klucz przerywa komendę. Walidacja chroni też przed SQL injection, bo klucz jest wklejany do zapytania SQL.
- Linie `makefile` zawierające klucz zaczynają się od `@`, więc `make` nie wypisuje klucza w terminalu.
- Hasło do bazy nie przechodzi przez linię komend hosta — `mysql` uruchamiany jest w kontenerze `db` i bierze dane logowania z jego zmiennych środowiskowych (`MYSQL_USER`, `MYSQL_PASSWORD`).
- Klucza nie wklejamy do narzędzi AI.

## Plik deploy/init/webservice.sql

PrestaShop zapisuje konfigurację Webservice w czterech tabelach. Skrypt wpisuje do nich te same dane, które zapisałby panel *Parametry zaawansowane → Webservice*:

| Tabela | Co trzyma |
|---|---|
| `ps_configuration` | przełącznik `PS_WEBSERVICE` |
| `ps_webservice_account` | klucz, opis, czy aktywny |
| `ps_webservice_account_shop` | przypisanie klucza do sklepu (`id_shop = 1`) |
| `ps_webservice_permission` | jeden wiersz na parę zasób × metoda (7 × 4 = 28 wierszy) |

Kroki skryptu (całość w jednej transakcji — przy błędzie w połowie nie zostaje konto bez uprawnień):

1. **Włączenie API** — `UPDATE` wartości `PS_WEBSERVICE`, a jeśli wiersza nie ma, `INSERT`.
2. **Usunięcie poprzedniego konta** — konto rozpoznawane po opisie `Import danych (BACK-1)`. Najpierw usuwane są wiersze zależne (`permission`, `account_shop`), potem samo konto.
3. **Utworzenie konta** z kluczem `@ws_key` i przypięcie go do sklepu. `LAST_INSERT_ID()` daje id nowego konta.
4. **Uprawnienia** — `CROSS JOIN` listy zasobów z listą metod tworzy 28 wierszy jednym zapytaniem.

Dzięki krokowi 2 skrypt jest **idempotentny**: można go uruchamiać wielokrotnie bez duplikatów. Rozpoznawanie konta po opisie, a nie po kluczu, sprawia, że po zmianie klucza w `.env` stary klucz jest usuwany, a nie zostaje w bazie z uprawnieniami.

Skrypt zakłada domyślny prefiks tabel `ps_` (compose nie ustawia `DB_PREFIX`).

## Cele w makefile

### make init

```make
init:
	@echo "$(PS_API_KEY)" | grep -qE '^[A-Z0-9]{32}$$' || { echo "PS_API_KEY w .env musi miec 32 znaki A-Z0-9"; exit 1; }
	@{ echo "SET @ws_key = '$(PS_API_KEY)';"; cat deploy/init/webservice.sql; } \
	  | $(COMPOSE) exec -T db sh -c 'MYSQL_PWD="$$MYSQL_PASSWORD" mysql -u"$$MYSQL_USER" "$$MYSQL_DATABASE"'
	@echo "Webservice API wlaczone, klucz zarejestrowany."
	$(PYTHON) -m scraper.importer.cleanup_demo --execute
```

- `-include .env` na początku `makefile` wczytuje zmienne z `.env` do `make`.
- MySQL nie czyta zmiennych środowiskowych, dlatego przed treścią pliku SQL doklejana jest linia `SET @ws_key = '...';`, a całość trafia przez pipe do `mysql`.
- `$$` w `makefile` oznacza dosłowny `$` — zmienne `$$MYSQL_USER` i `$$MYSQL_PASSWORD` rozwija powłoka w kontenerze `db`.
- `MYSQL_PWD` zamiast `-p<hasło>` — hasła nie widać na liście procesów.
- `exec -T` wyłącza TTY; bez tego pipe nie działa.
- Ostatnia linia usuwa przez API kategorie i produkty demonstracyjne z instalatora (lista nazw `DEMO_CATEGORIES` w `cleanup_demo.py`). Działa na hoście, więc wymaga Pythona z zależnościami z `scraper/requirements.txt`. Gdy danych demo już nie ma, niczego nie zmienia.

### make api-check

Wykonuje cztery zapytania `curl` i porównuje kody HTTP z oczekiwanymi (patrz [Uruchomienie](#uruchomienie)). Przy niezgodności wypisuje `FAIL` i kończy się błędem. Adres sklepu domyślnie to `https://localhost:$(HTTPS_PORT)` (zapytania idą z `-k`, bo certyfikat jest samopodpisany); można go nadpisać, np. dla klastra w etapie 2:

```bash
make api-check SHOP_URL=https://adres-sklepu
```

## Rozwiązywanie problemów

- **`Table 'ps_configuration' doesn't exist`** — `make init` uruchomione przed końcem instalacji PrestaShop. Poczekać na `Almost ! Starting web server now` w `make logs` i powtórzyć.
- **`PS_API_KEY w .env musi miec 32 znaki A-Z0-9`** — brak klucza w `.env` albo zły format; wygenerować go poleceniem z sekcji [Uruchomienie](#uruchomienie).
- **`make api-check`: `api/ z kluczem -> 401`** — klucz w `.env` zmieniony bez ponownego `make init` albo baza została wyczyszczona (`make reset`).
- **`/api/` zwraca 404** — brak reguły przepisywania adresów w `.htaccess`. Na obrazie `prestashop:8.2.8` reguła jest tworzona przy auto-instalacji; gdyby jej zabrakło, zapisać ustawienia w panelu *Ruch → SEO i URL*.

## Rozszerzanie uprawnień

Import promocji (D3) będzie wymagał dodatkowych zasobów, np. `specific_prices`. Stawki VAT nie wymagają uprawnień, bo ID grup podatkowych są w `.env` (`PS_TAX_RULES_GROUP_MAP`). Nowe zasoby wystarczy dopisać do listy zasobów w kroku 4 skryptu i uruchomić ponownie `make init`.
