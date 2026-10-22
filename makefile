# -f - specyfikacja ścieżki do pliku compose.yaml, tak by można było uruchamiać komendy z roota
# --env-file - ścieżka do pliku .env z poziomu pliku makefile. Jest konieczna bo .env i compose.yaml znajdują się w innych folderach
COMPOSE = docker compose -f deploy/compose.yaml --env-file .env

.PHONY: help up down reset logs ps shell build

help:
	@echo "make up      - zbuduj obraz i uruchom sklep w tle"
	@echo "make down    - zatrzymaj i usun kontenery (dane zostaja)"
	@echo "make reset   - usun kontenery ORAZ dane (sklep od zera)"
	@echo "make logs    - logi sklepu na zywo"
	@echo "make ps      - status kontenerow"
	@echo "make shell   - powloka w kontenerze sklepu"
	@echo "make build   - zbuduj obraz bez uruchamiania"

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f shop

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec shop bash

build:
	$(COMPOSE) build