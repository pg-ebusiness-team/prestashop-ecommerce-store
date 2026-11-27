-include .env

# -f - specyfikacja ścieżki do pliku compose.yaml, tak by można było uruchamiać komendy z roota
# --env-file - ścieżka do pliku .env z poziomu pliku makefile. Jest konieczna bo .env i compose.yaml znajdują się w innych folderach
COMPOSE = docker compose -f deploy/compose.yaml --env-file .env
# Importer PrestaShop
PYTHON ?= python3
IMPORT_ARGS ?= --execute
# Adres sklepu dla api-check; nadpisywalny np. dla klastra w etapie 2
SHOP_URL ?= https://localhost:$(HTTPS_PORT)

.PHONY: help up down reset logs ps shell build init api-check theme omnibus-install test-e2e import-categories import-products import

help:
	@echo "make up      - zbuduj obraz i uruchom sklep w tle"
	@echo "make down    - zatrzymaj i usun kontenery (dane zostaja)"
	@echo "make reset   - usun kontenery ORAZ dane (sklep od zera)"
	@echo "make logs    - logi sklepu na zywo (domyslnie wszystkie, make logs SERVICE=[np. proxy], aby wybrać konkretne)"
	@echo "make ps      - status kontenerow"
	@echo "make shell   - powloka w kontenerze sklepu"
	@echo "make build   - zbuduj obraz bez uruchamiania"
	@echo "make init    - wlacz Webservice API i zarejestruj klucz PS_API_KEY"
	@echo "make api-check - sprawdz odpowiedzi Webservice API dla klucza z .env"
	@echo "make theme   - wlacz motyw potomny custom-child-theme, pobierz grafiki i wgraj tresci strony glownej i stron CMS, wyczysc cache"
	@echo "make omnibus-install - zainstaluj modul Omnibusprice"
	@echo "make test-e2e - uruchom testy E2E Playwright (raport: tests/playwright-report)"
	@echo "make import-categories - importuj kategorie"
	@echo "make import-products   - importuj atrybuty, produkty i warianty"
	@echo "make import            - wykonaj pelny import"


up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f $(SERVICE)

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec shop bash

build:
	$(COMPOSE) build

init:
	@echo "$(PS_API_KEY)" | grep -qE '^[A-Z0-9]{32}$$' || { echo "PS_API_KEY w .env musi miec 32 znaki A-Z0-9"; exit 1; }
	@{ echo "SET @ws_key = '$(PS_API_KEY)';"; cat deploy/init/webservice.sql; } \
	  | $(COMPOSE) exec -T db sh -c 'MYSQL_PWD="$$MYSQL_PASSWORD" mysql -u"$$MYSQL_USER" "$$MYSQL_DATABASE"'
	@echo "Webservice API wlaczone, klucz zarejestrowany."
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
	@# 1. Sprawdzamy, czy jest plik dla każdej strony 1-5. Bez tego brakująca strona dostałaby pustą treść (NULL).
	@#    Sprawdzenie jest osobno, bo błąd wewnątrz potoku (|) niżej nie zatrzymałby make.
	@# 2. Dla każdego pliku wypisujemy linię SQL: SET @cms_<id> = FROM_BASE64('<treść pliku w base64>');
	@#    <id> to numer z początku nazwy pliku (= id_cms w PrestaShop). Base64 zawiera tylko A-Z, a-z, 0-9, +, / i =,
	@#    więc apostrofy, cudzysłowy i backslashe z HTML nie psują zapytania i nie trzeba ich escapować.
	@# 3. Za tymi liniami doklejamy cms.sql, który wpisuje @cms_<id> do ps_cms_lang. Całość idzie jednym połączeniem
	@#    do mysql, bo zmienne @ żyją tylko w obrębie jednej sesji.
	@for id in 1 2 3 4 5; do ls shop/cms/$$id-*.html >/dev/null 2>&1 || { echo "Brak pliku shop/cms/$$id-*.html"; exit 1; }; done
	@{ for f in shop/cms/*.html; do id=$$(basename "$$f"); id=$${id%%-*}; \
	    printf "SET @cms_%s = FROM_BASE64('%s');\n" "$$id" "$$(base64 < "$$f" | tr -d '\n')"; done; \
	  cat deploy/init/cms.sql; } \
	  | $(COMPOSE) exec -T db sh -c 'MYSQL_PWD="$$MYSQL_PASSWORD" mysql -u"$$MYSQL_USER" "$$MYSQL_DATABASE"'
	$(COMPOSE) exec -T -u www-data shop php bin/console cache:clear --env=prod


# Instalacja modułu Omnibusprice
omnibus-install:
	$(COMPOSE) exec -T -u www-data shop php bin/console prestashop:module install omnibusprice

# Import danych do PrestaShop
import-categories:
	$(PYTHON) -m scraper.importer.main $(IMPORT_ARGS) --categories-only

import-products:
	$(PYTHON) -m scraper.importer.main $(IMPORT_ARGS) --products-only

import:
	$(PYTHON) -m scraper.importer.main $(IMPORT_ARGS)

# Testy E2E: instalacja zależności i Chromium, potem testy na adresie SHOP_URL
test-e2e:
	cd tests && npm ci && npx playwright install chromium && BASE_URL=$(SHOP_URL) npm run test:e2e
