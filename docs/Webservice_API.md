# Webservice API (BACK-1)

Konfiguracja PrestaShop Webservice API, z którego korzysta skrypt importu danych ze scrapera (wymaganie D2 etapu 1).

## Co robi konfiguracja

- włącza Webservice API (`PS_WEBSERVICE = 1`),
- rejestruje jeden klucz API pobierany z `.env` (`PS_API_KEY`),
- ogranicza klucz do metod GET, POST, PUT, DELETE na zasobach: `categories`, `products`, `combinations`, `stock_availables`, `images`, `product_options`, `product_option_values`, `specific_prices` (promocje), `product_features`, `product_feature_values`. Dostęp do pozostałych zasobów (np. `customers`, `orders`) kończy się odpowiedzią 401.

Wszystko robi skrypt, bez klikania w panelu (jedna komenda inicjalizacji, w etapie 2 bez ręcznych kroków).

## Uruchomienie

```bash
make up          # przy pierwszym uruchomieniu tworzy .env z wygenerowanym PS_API_KEY; kończy się po instalacji sklepu
make init        # pełna inicjalizacja; włączenie API i rejestracja klucza to jej krok `webservice`
make api-check   # weryfikacja
```

Sam klucz bez reszty inicjalizacji rejestruje `make webservice`. Klucz wpisany ręcznie do `.env` musi mieć 32 znaki `A-Z0-9`, np. z `openssl rand -hex 16 | tr a-f A-F`.

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

`-k`, bo certyfikat jest samopodpisany. Adres zależy od `SERVER_NAME` i `HTTPS_PORT` z `.env`.

## Klucz API i bezpieczeństwo

- Klucz trzymamy wyłącznie w `.env`, który jest w `.gitignore` (razem z `.env.*`, poza `.env.example`). W repozytorium jest tylko `PS_API_KEY=your_api_key_here` w `.env.example`.
- PrestaShop wymaga klucza o długości dokładnie 32 znaków `A-Z0-9`. `make init` sprawdza format przed wysłaniem czegokolwiek do bazy — zły klucz przerywa komendę. Walidacja chroni też przed SQL injection, bo klucz jest wklejany do zapytania SQL.
- Linie `makefile` zawierające klucz zaczynają się od `@`, więc `make` nie wypisuje klucza w terminalu.
- Hasło do bazy nie przechodzi przez linię komend hosta — `mysql` uruchamiany jest w kontenerze `db` i bierze dane logowania z jego zmiennych środowiskowych (`MYSQL_USER`, `MYSQL_PASSWORD`).
- Klucza nie wklejamy do narzędzi AI.

## Plik deploy/init/webservice.sql

Skrypt wpisuje do czterech tabel to samo, co panel *Parametry zaawansowane → Webservice*:

| Tabela | Co trzyma |
|---|---|
| `ps_configuration` | przełącznik `PS_WEBSERVICE` |
| `ps_webservice_account` | klucz, opis, czy aktywny |
| `ps_webservice_account_shop` | przypisanie klucza do sklepu (`id_shop = 1`) |
| `ps_webservice_permission` | jeden wiersz na parę zasób × metoda (10 × 4 = 40 wierszy) |

Kroki skryptu (całość w jednej transakcji — przy błędzie w połowie nie zostaje konto bez uprawnień):

1. **Włączenie API** — `UPDATE` wartości `PS_WEBSERVICE`, a jeśli wiersza nie ma, `INSERT`.
2. **Usunięcie poprzedniego konta** — konto rozpoznawane po opisie `Import danych (BACK-1)`. Najpierw usuwane są wiersze zależne (`permission`, `account_shop`), potem samo konto.
3. **Utworzenie konta** z kluczem `@ws_key` i przypięcie go do sklepu. `LAST_INSERT_ID()` daje id nowego konta.
4. **Uprawnienia** — `CROSS JOIN` listy zasobów z listą metod tworzy 40 wierszy jednym zapytaniem.

Dzięki krokowi 2 skrypt jest **idempotentny**, a że konto jest rozpoznawane po opisie, a nie po kluczu, po zmianie klucza w `.env` stary klucz znika z bazy.

Skrypt zakłada domyślny prefiks tabel `ps_` (compose nie ustawia `DB_PREFIX`).

## Cele w makefile

### make webservice (krok `make init`)

Sprawdza format klucza, dokleja przed `webservice.sql` linię `SET @ws_key = '<klucz>';` (MySQL nie czyta zmiennych środowiskowych) i przekazuje całość przez pipe do `mysql` w kontenerze `db` (`exec -T`, bez TTY). Hasło idzie przez `MYSQL_PWD` w kontenerze, więc nie widać go na liście procesów.

Kolejny krok `make init`, `make cleanup-demo`, usuwa przez API kategorie i produkty demo z instalatora (`DEMO_CATEGORIES` w `cleanup_demo.py`); bez danych demo niczego nie zmienia.

### make api-check

Cztery zapytania `curl` z porównaniem kodów HTTP (patrz [Uruchomienie](#uruchomienie)); niezgodność to `FAIL` i błąd. Domyślny adres `https://localhost:$(HTTPS_PORT)` można nadpisać, np. dla klastra:

```bash
make api-check SHOP_URL=https://adres-sklepu
```

## Rozwiązywanie problemów

- **`Table 'ps_configuration' doesn't exist`** — `make webservice` uruchomione przed końcem instalacji PrestaShop. `make init` sprawdza to wcześniej (`check-shop`). Poczekać na koniec `make up` i powtórzyć.
- **`PS_API_KEY w .env musi miec 32 znaki A-Z0-9`** — brak klucza w `.env` albo zły format; wygenerować go poleceniem z sekcji [Uruchomienie](#uruchomienie).
- **`make api-check`: `api/ z kluczem -> 401`** — klucz w `.env` zmieniony bez ponownego `make init` (lub `make webservice`) albo baza została wyczyszczona (`make reset`).
- **`/api/` zwraca 404** — brak reguły przepisywania adresów w `.htaccess`. Na obrazie `prestashop:8.2.8` reguła jest tworzona przy auto-instalacji; gdyby jej zabrakło, zapisać ustawienia w panelu *Ruch → SEO i URL*.

## Klucz a moduł Omnibus

Ten sam klucz autoryzuje zapis najniższych cen z 30 dni do własnego modułu `omnibusprice` (`POST /module/omnibusprice/sync`, Basic Auth jak w API). To nie jest zasób Webservice, więc nie ma go w `ps_webservice_permission`: kontroler modułu sprawdza tylko, czy klucz istnieje w `ps_webservice_account` i jest aktywny. Opis modułu: README, sekcja „Promocje i Omnibus”.

## Rozszerzanie uprawnień

Stawki VAT nie wymagają uprawnień, bo ID grup podatkowych są w `.env` (`PS_TAX_RULES_GROUP_MAP`). Nowe zasoby wystarczy dopisać do listy zasobów w kroku 4 skryptu i uruchomić ponownie `make init`.
