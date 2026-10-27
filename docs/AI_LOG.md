# Dziennik AI

| Data i autor | Narzędzie i model | Zadanie | Co otrzymano | Co było błędne | Weryfikacja |
| --- | --- | --- | --- | --- | --- |
| 2026-10-26, Bartosz Pacyga | Claude Code (Claude Opus 5.5) | BACK-1 (#9): włączenie Webservice API i klucz z ograniczonymi uprawnieniami | Plan zadania na podstawie `docs/WYMAGANIA.md`; skrypt `deploy/init/webservice.sql`; aktualizacja README i dokumentacji | Claude nadpisał wygenerowany klucz, pierwotny klucz przepadł, wygenerowano nowy.| Uruchomienie na czystym środowisku (`make up`, `make init` ×2): 1 konto, 20 uprawnień, brak duplikatów; weryfikacja dokumentacji |
| 2026-10-27, Bartosz Pacyga | Claude Code (Claude Opus 5.5) | dokończenie wymagań formalnych repozytorium | Analiza W1/D5 z `docs/WYMAGANIA.md`; workflow `.github/workflows/ci.yml` (ruff + pytest scrapera, gitleaks) na każdy PR do `main` | Pierwsza wersja skanowała gitleaksem wszystkie gałęzie (`--all`) — w CI blokowałoby to każdy PR przez cudze gałęzie; zmieniono na `--log-opts=HEAD`. | Wersje akcji i narzędzi sprawdzone w GitHub Releases (checkout v7, setup-python v7, ruff 0.17.3, gitleaks 8.30.1); gitleaks 8.30.1 na `HEAD`: 0 znalezisk, na `--all`: 1 fałszywy alarm w `docs/Webservice_API.md` z gałęzi `feat/9` |

## Refleksja zespołu
*(Uzupełnimy pod koniec etapu)*