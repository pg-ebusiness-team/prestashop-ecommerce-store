-include .env

# -f - specyfikacja ścieżki do pliku compose.yaml, tak by można było uruchamiać komendy z roota
# --env-file - ścieżka do pliku .env z poziomu pliku makefile. Jest konieczna bo .env i compose.yaml znajdują się w innych folderach
COMPOSE = docker compose -f deploy/compose.yaml --env-file .env
# Adres sklepu dla api-check; nadpisywalny np. dla klastra w etapie 2
SHOP_URL ?= https://localhost:$(HTTPS_PORT)

.PHONY: help up down reset logs ps shell build init api-check theme

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
	@echo "make theme   - wlacz motyw potomny custom-child-theme, pobierz grafiki i wgraj tresci strony glownej, wyczysc cache"


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
	$(COMPOSE) exec -T -u www-data shop php bin/console cache:clear --env=prod