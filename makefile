-include .env

# -f - specyfikacja ścieżki do pliku compose.yaml, tak by można było uruchamiać komendy z roota
# --env-file - ścieżka do pliku .env z poziomu pliku makefile. Jest konieczna bo .env i compose.yaml znajdują się w innych folderach
COMPOSE = docker compose -f deploy/compose.yaml --env-file .env
# Importer i scraper w kontenerze narzędziowym (usługa tools, deploy/tools/Dockerfile) - bez Pythona na hoście.
# --user: pliki zapisane w zamontowanym repo (zdjęcia, *_mapping.json) należą do użytkownika hosta, nie do roota.
# --build: obraz przebuduje się sam po zmianie scraper/requirements.txt (bez zmian - z cache, poniżej sekundy).
# --no-deps: bez budowania i uruchamiania innych usług - sklep musi już działać (make up; make init sprawdza to w check-shop).
TOOLS = $(COMPOSE) run --rm --no-deps --build --user $(shell id -u):$(shell id -g) tools
PYTHON = $(TOOLS) python
IMPORT_ARGS ?= --execute
# Archiwum zdjęć produktów w Releases (deploy/init/photos.sh); można nadpisać w .env
PHOTOS_RELEASE_URL ?= https://github.com/pg-ebusiness-team/prestashop-ecommerce-store/releases/download/photos_v1.0/product_photos.zip
# Adres sklepu dla api-check; nadpisywalny np. dla klastra w etapie 2
SHOP_URL ?= https://localhost:$(HTTPS_PORT)

.PHONY: help up down reset logs ps shell build init check-shop webservice cleanup-demo api-check theme test-e2e
.PHONY: facets categories import-categories import-products import photos purifier-dir

help:
	@echo "make up      - zbuduj obraz, uruchom sklep w tle i poczekaj na koniec instalacji (tworzy .env, jesli go nie ma)"
	@echo "make down    - zatrzymaj i usun kontenery (dane zostaja)"
	@echo "make reset   - usun kontenery ORAZ dane (sklep od zera)"
	@echo "make logs    - logi sklepu na zywo (domyslnie wszystkie, make logs SERVICE=[np. proxy], aby wybrać konkretne)"
	@echo "make ps      - status kontenerow"
	@echo "make shell   - powloka w kontenerze sklepu"
	@echo "make build   - zbuduj obraz bez uruchamiania"
	@echo "make init    - pelna inicjalizacja danych po make up: zdjecia, klucz API, import, filtry, opisy kategorii, motyw"
	@echo "               (kolejne kroki osobno: make photos / webservice / cleanup-demo / import / facets / categories / theme)"
	@echo "make api-check - sprawdz odpowiedzi Webservice API dla klucza z .env"
	@echo "make theme   - wlacz motyw potomny custom-child-theme, pobierz grafiki i wgraj tresci strony glownej i stron CMS, wyczysc cache"
	@echo "make facets  - ustaw filtry w lewej kolumnie list produktow i przebuduj ich indeks (po imporcie danych)"
	@echo "make categories - wgraj opisy kategorii z shop/categories/ (po imporcie danych)"
	@echo "make test-e2e - uruchom testy E2E Playwright (raport: tests/playwright-report)"
	@echo "make import-categories - importuj kategorie"
	@echo "make import-products   - importuj atrybuty, produkty i warianty"
	@echo "make import            - wykonaj pelny import"
	@echo "make photos            - pobierz zdjecia produktow z Releases (brakujace - z URL-i sklepu zrodlowego)"


# Pierwsze uruchomienie z czystego klona: .env z .env.example z wygenerowanym kluczem Webservice API
# (32 znaki A-Z0-9). Istniejący .env nie jest ruszany. Przez -include .env na górze make tworzy go
# przy dowolnym poleceniu, a potem wczytuje.
.env:
	@key=$$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n' | tr a-f A-F); \
	  awk -v key="$$key" '/^PS_API_KEY=/ { print "PS_API_KEY=" key; next } { print }' .env.example > .env
	@echo "Utworzono .env z .env.example (wygenerowany PS_API_KEY). Hasla przykladowe - do zmiany poza lokalnym uzyciem."

# --wait: polecenie kończy się dopiero, gdy sklep jest zainstalowany (healthcheck usługi shop), więc zaraz
# po nim można uruchomić make init. Błąd instalacji lub konfiguracji sprzedaży kończy je kodem != 0.
up: .env
	$(COMPOSE) up -d --build --wait --wait-timeout 900

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v
	rm -f scraper/importer/*_mapping.json

logs:
	$(COMPOSE) logs -f $(SERVICE)

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec shop bash

build:
	$(COMPOSE) build

# Pełna inicjalizacja danych po `make up` (WYMAGANIA.md W3: jedna komenda inicjalizacji). Kolejność wynika z zależności:
#  photos       - pierwsze, bo nie zależy od sklepu: bez zdjęć kończy się błędem, zanim cokolwiek zmieni w bazie
#  webservice   - klucz API, bez niego nie działa cleanup-demo ani import
#  cleanup-demo - usuwa kategorie i produkty demo z instalatora
#  import       - kategorie, atrybuty, cechy, produkty, zdjęcia (Webservice API)
#  facets, categories - dopasowują kategorie i cechy po nazwie, więc po imporcie
#  theme        - menu i stopka z kategorii po nazwie, więc po imporcie; na końcu czyści cache (także po SQL-ach wyżej)
# Każdy krok jest idempotentny, więc ponowne `make init` aktualizuje dane bez duplikatów.
# $(MAKE) z listą celów wykonuje je po kolei i zatrzymuje się na pierwszym błędzie.
init:
	@start=$$(date +%s); \
	$(MAKE) --no-print-directory check-shop photos webservice cleanup-demo import facets categories theme || exit 1; \
	elapsed=$$(( $$(date +%s) - start )); \
	echo ""; \
	echo "make init: gotowe w $$(( elapsed / 60 )) min $$(( elapsed % 60 )) s. Sklep: https://$(SERVER_NAME):$(HTTPS_PORT)"

# Czy `make up` się zakończył: usługa shop musi mieć status healthy (healthcheck w deploy/compose.yaml)
check-shop:
	@health=$$($(COMPOSE) ps shop --format '{{.Health}}' 2>/dev/null); \
	case "$$health" in \
	  healthy) echo "check-shop: sklep gotowy" ;; \
	  "") echo "check-shop: BLAD: sklep nie dziala - uruchom najpierw: make up"; exit 1 ;; \
	  *) echo "check-shop: BLAD: sklep ma status '$$health' - poczekaj na koniec make up albo sprawdz: make logs SERVICE=shop"; exit 1 ;; \
	esac

# Włącza Webservice API i rejestruje klucz PS_API_KEY z .env (deploy/init/webservice.sql)
webservice:
	@echo "$(PS_API_KEY)" | grep -qE '^[A-Z0-9]{32}$$' || { echo "PS_API_KEY w .env musi miec 32 znaki A-Z0-9"; exit 1; }
	@{ echo "SET @ws_key = '$(PS_API_KEY)';"; cat deploy/init/webservice.sql; } \
	  | $(COMPOSE) exec -T db sh -c 'MYSQL_PWD="$$MYSQL_PASSWORD" mysql -u"$$MYSQL_USER" "$$MYSQL_DATABASE"'
	@echo "Webservice API wlaczone, klucz zarejestrowany."

# Usuwa przez API kategorie i produkty demo z instalatora
cleanup-demo:
	$(PYTHON) -m scraper.importer.cleanup_demo --execute

# Oczekiwane kody: klucz dziala, nie ma dostepu poza swoimi zasobami, bez klucza brak dostepu
api-check:
	@check() { code=$$(curl -s -k -o /dev/null -w '%{http_code}' $$3 "$(SHOP_URL)/$$1"); \
	  if [ "$$code" = "$$2" ]; then echo "OK   $$4 -> $$code"; else echo "FAIL $$4 -> $$code (oczekiwano $$2)"; exit 1; fi; }; \
	check api/ 200 "-u $(PS_API_KEY):" "api/ z kluczem"; \
	check api/products 200 "-u $(PS_API_KEY):" "api/products z kluczem"; \
	check api/customers 401 "-u $(PS_API_KEY):" "api/customers z kluczem (brak uprawnien)"; \
	check api/ 401 "" "api/ bez klucza"

# -u www-data: pliki cache muszą należeć do użytkownika Apache, inaczej sklep nie zapisze kolejnych
theme:
	$(COMPOSE) exec -T -u www-data shop php bin/console prestashop:theme:enable custom-child-theme
	@echo "Pobieranie grafik strony glownej (deploy/init/home-images.txt)..."
	@grep -Ev '^(#|$$)' deploy/init/home-images.txt | $(COMPOSE) exec -T -u www-data shop sh -c \
	  'mkdir -p img/cms/home && while read name url; do curl -fsS -o "img/cms/home/$$name" "$$url" || { echo "Nie udalo sie pobrac $$name"; exit 1; }; done'
	@$(COMPOSE) exec -T db sh -c 'MYSQL_PWD="$$MYSQL_PASSWORD" mysql -u"$$MYSQL_USER" "$$MYSQL_DATABASE"' < deploy/init/theme.sql
	@# Strony CMS (treść w shop/cms/, metadane w deploy/init/cms.sql):
	@# 1. Sprawdzamy, czy jest plik dla każdej strony 1-6. Bez tego brakująca strona dostałaby pustą treść (NULL).
	@#    Sprawdzenie jest osobno, bo błąd wewnątrz potoku (|) niżej nie zatrzymałby make.
	@# 2. Dla każdego pliku wypisujemy linię SQL: SET @cms_<id> = FROM_BASE64('<treść pliku w base64>');
	@#    <id> to numer z początku nazwy pliku (= id_cms w PrestaShop). Base64 zawiera tylko A-Z, a-z, 0-9, +, / i =,
	@#    więc apostrofy, cudzysłowy i backslashe z HTML nie psują zapytania i nie trzeba ich escapować.
	@# 3. Za tymi liniami doklejamy cms.sql, który wpisuje @cms_<id> do ps_cms_lang. Całość idzie jednym połączeniem
	@#    do mysql, bo zmienne @ żyją tylko w obrębie jednej sesji.
	@for id in 1 2 3 4 5 6; do ls shop/cms/$$id-*.html >/dev/null 2>&1 || { echo "Brak pliku shop/cms/$$id-*.html"; exit 1; }; done
	@{ for f in shop/cms/*.html; do id=$$(basename "$$f"); id=$${id%%-*}; \
	    printf "SET @cms_%s = FROM_BASE64('%s');\n" "$$id" "$$(base64 < "$$f" | tr -d '\n')"; done; \
	  cat deploy/init/cms.sql; } \
	  | $(COMPOSE) exec -T db sh -c 'MYSQL_PWD="$$MYSQL_PASSWORD" mysql -u"$$MYSQL_USER" "$$MYSQL_DATABASE"'
	$(COMPOSE) exec -T -u www-data shop php bin/console cache:clear --env=prod

# Filtry (ps_facetedsearch) po imporcie - dopasowuje kategorie i cechy po nazwie, więc bez importu zgłosi braki.
# Skrypt idzie przez stdin, więc nie trzeba przebudowywać obrazu; -u www-data jak przy theme (pliki cache).
facets:
	$(COMPOSE) exec -T -u www-data shop php < deploy/init/facets.php

# Opisy kategorii po imporcie - jak strony CMS w theme: każdy plik shop/categories/<plik>.html idzie jako
# SET @`cat_<plik>` = FROM_BASE64('...'), a categories.sql wpisuje je do kategorii o nazwach z listy.
# Raport braków z categories.sql (linie „categories: BLAD”) zatrzymuje make.
categories:
	@out=$$({ for f in shop/categories/*.html; do name=$$(basename "$$f" .html); \
	    printf "SET @\`cat_%s\` = FROM_BASE64('%s');\n" "$$name" "$$(base64 < "$$f" | tr -d '\n')"; done; \
	  cat deploy/init/categories.sql; } \
	  | $(COMPOSE) exec -T db sh -c 'MYSQL_PWD="$$MYSQL_PASSWORD" mysql -N -u"$$MYSQL_USER" "$$MYSQL_DATABASE"') || exit 1; \
	if [ -n "$$out" ]; then echo "$$out"; exit 1; fi
	@echo "categories: gotowe"
# Zdjęcia produktów: archiwum z Releases, brakujące z URL-i z wyników scrapera (fallback)
photos:
	$(TOOLS) sh deploy/init/photos.sh "$(PHOTOS_RELEASE_URL)"

# Import danych do PrestaShop
# API czyści opisy HTML przez HTMLPurifier, który zapisuje cache w var/cache/prod/purifier. PrestaShop nie tworzy
# tego katalogu (po instalacji i po cache:clear go nie ma), a brak kończy każdy zapis opisu błędem HTTP 500.
purifier-dir:
	@$(COMPOSE) exec -T -u www-data shop mkdir -p var/cache/prod/purifier

import-categories: purifier-dir
	$(PYTHON) -m scraper.importer.main $(IMPORT_ARGS) --categories-only

import-products: purifier-dir
	$(PYTHON) -m scraper.importer.main $(IMPORT_ARGS) --products-only

import: purifier-dir
	$(PYTHON) -m scraper.importer.main $(IMPORT_ARGS)

# Testy E2E: instalacja zależności i Chromium, potem testy na adresie SHOP_URL
test-e2e:
	cd tests && npm ci && npx playwright install chromium && BASE_URL=$(SHOP_URL) npm run test:e2e
