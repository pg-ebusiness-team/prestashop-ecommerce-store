# Wymagania projektowe — Biznes elektroniczny 2026/2027

Zestawienie wymagań z opisów etapu 1/2 i 2/2 (eNauczanie PG). Progi z tabel metryk wpisano przy odpowiednich punktach.

**Legenda:** **[K]** — warunek krytyczny; jego niespełnienie oznacza 0 pkt za całe wymaganie.

**Stan (2026-11-25):** `[x]` — spełnione i sprawdzone w repozytorium lub na uruchomionym sklepie; `[ ]` — niespełnione albo jeszcze niesprawdzone (znane braki dopisane jako *stan*). Przy PR, który spełnia wymaganie, zaznacz je tutaj.

## Spis treści

- [Etap 1 — sklep PrestaShop w kontenerach](#etap-1--sklep-prestashop-w-kontenerach)
- [Etap 2 — Docker Swarm, CI/CD, GA4](#etap-2--docker-swarm-cicd-ga4)
- [Ocenianie (oba etapy)](#ocenianie-oba-etapy)

---

## Etap 1 — sklep PrestaShop w kontenerach

Czas: 8 tygodni, odbiór na 4. spotkaniu projektowym. Decyzje z etapu 1 (struktura repo, obrazy, inicjalizacja danych) bezpośrednio wpływają na nakład pracy w etapie 2.

### Stack i zasady ogólne

- [x] PrestaShop 8.x (zalecany najnowszy 8.2.x); można bazować na obrazie `prestashop/prestashop:8.x`
- [x] PHP 8.1, MySQL 8.0 lub MariaDB 10.6+
- [x] Wyłącznie kontenery Docker — wariant z VM niedopuszczalny
- [x] Docker Compose v2: plik `compose.yaml`, komenda `docker compose`, **bez** klucza `version:`
- [x] Obrazy budowane dla `linux/amd64` (lub multi-arch) — uwaga na Apple Silicon (domyślnie arm64)
- [ ] Repozytorium na GitHub (zalecany) lub GitLab (GitLab Free: prywatna grupa maks. 5 osób łącznie z prowadzącym)
- [x] Testy E2E w **Playwright** (TS/JS, Python, Java lub C#), headless — **Selenium niedopuszczalny**
- [x] Scraper w dowolnym języku/bibliotece
- [x] Poczta testowa: Mailpit lub MailHog jako kontener
- Płatne moduły PrestaShop dozwolone, ale żadne wymaganie ich nie zakłada

### Wymagana struktura repozytorium

| Katalog | Zawartość |
|---|---|
| `shop/` | kod sklepu, motyw i moduły własne, Dockerfile |
| `scraper/` | kod scrapera wraz z testami |
| `scraper-results/` | wyniki w UTF-8 (JSON lub CSV) z URL-ami źródłowymi zdjęć + maks. 20 przykładowych zdjęć |
| `tests/` | testy E2E |
| `deploy/` | `compose.yaml`, skrypty instalacji, inicjalizacji danych, backupu i odtwarzania |
| `docs/` | `AI_LOG.md`, ADR, dodatkowa dokumentacja |

### Zdjęcia produktów

- [x] Zdjęcia **nie** w repozytorium ani w Git LFS
- [x] Scraper zapisuje zdjęcia w katalogu wykluczonym w `.gitignore`
- [x] Pełny zbiór publikowany jako jedno archiwum (zip/tar.gz, ≤1 GB) w zakładce **Releases** — *wydanie `photos_v1.0`, `product_photos.zip` 76 MB, 2887 zdjęć; brakuje 1 zdjęcia, którego nie ma też w źródle (404, produkt 1496)*
- [x] Skrypt inicjalizacji pobiera archiwum z Releases, a gdy jest niedostępne — ponownie pobiera zdjęcia z URL-i z wyników scrapowania — *`deploy/init/photos.sh` (`make photos`, krok `make init`), fallback: scraper `--photos-only`*
- [x] Dłuższy bok 800–1600 px, JPEG lub WebP, ≤300 KB na plik — *wszystkie 2887 zdjęć z `photos_v1.0`: WebP, 1000 px, ≤300 KB*

### Narzędzia AI i dziennik AI

- [ ] Kod wygenerowany przez AI trafia do `main` wyłącznie przez PR z merytorycznym review człowieka
- [ ] PR z istotnymi fragmentami od AI ma etykietę `ai-assisted` i opis, jak zweryfikowano poprawność
- [ ] Do narzędzi AI nie trafiają hasła, klucze API ani dane dostępowe do klastra
- [x] `docs/AI_LOG.md` prowadzony jako tabela z kolumnami:

  | Kolumna | Co wpisać |
  |---|---|
  | Data i autor | kto i kiedy korzystał |
  | Narzędzie i model | np. Claude, ChatGPT, Copilot, agent w IDE |
  | Zadanie | numer issue/PR i cel użycia |
  | Co otrzymano | krótki opis kodu lub odpowiedzi |
  | Co było błędne | błędy, halucynacje, nieaktualne API, problemy z bezpieczeństwem |
  | Weryfikacja | test, dokumentacja, ręczne uruchomienie |

- [ ] Wpis dodaje osoba korzystająca z narzędzia, w tym samym PR co kod
- [ ] Minimum **2 wpisy na osobę** w etapie — *stan: Jakub Romanowski ma 1 wpis*
- [ ] Na końcu refleksja zespołu (≤1 strona): gdzie AI przyspieszyło pracę, gdzie wprowadziło w błąd, czego trzeba było nauczyć się samemu — *stan: do napisania*
- Zespół bez AI opisuje to w refleksji i nie traci punktów
- Podczas obrony nie można zasłaniać się tym, że kod napisało AI

### W1. Repozytorium i proces pracy (3 pkt)

- [ ] **[K]** Repo na GitHub/GitLab z dostępem dla wszystkich członków zespołu i prowadzącego
- [ ] **[K]** Brak bezpośrednich commitów/pushy do `main` (poza inicjalnym) — 100% zmian przez scalony PR/MR zaakceptowany przez inną osobę; brak force push (weryfikacja ręczna; ochrona gałęzi niewymagana)
- [ ] **[K]** Brak sekretów w repo (hasła, klucze webservice, klucze prywatne) — konfiguracja przez `.env`, w repo tylko `.env.example`; **gitleaks na całej historii: 0 znalezisk**
- [x] `.gitignore` wyklucza cache, uploady, logi, `vendor/`, `node_modules/`
- [x] `README.md`: opis projektu, wersja PrestaShop, uruchomienie krok po kroku, skład zespołu
- [ ] `main` zawiera wersję prezentowaną na odbiorze; prace robocze w gałęziach pobocznych
- [ ] Zadania jako issues z przypisaną osobą; każde issue kończy się PR
- [ ] Recenzje zawierają merytoryczne komentarze, nie tylko akceptację
- [ ] Struktura katalogów zgodna z tabelą powyżej — *stan: jest `scraper_results/` zamiast `scraper-results/`*
- [ ] Każda osoba jest **autorem ≥3** i **recenzentem ≥3** scalonych PR
- [x] Repo ≤200 MB, brak plików >10 MB, brak pełnego zbioru zdjęć — *`scraper_results/product_photos.zip` (72 MB) i `products.zip` usunięte z `main` w #7, `*.zip` w `.gitignore`; w historii zostają (bez force push)*

### W2. Scraper (4 pkt)

- [x] **[K]** Kod scrapera i wyniki (UTF-8) w repozytorium
- [ ] **[K]** Wyniki obejmują kategorie, podkategorie i produkty z polami:
  - [x] nazwa
  - [ ] opis — *stan: brak w 63 z 2397 zebranych produktów (54 z nich mają krótki opis)*
  - [x] cena brutto
  - [x] stawka VAT (jeśli dostępna)
  - [x] atrybuty (np. kolor, materiał, rozmiar)
  - [ ] waga (jeśli dostępna)
  - [ ] zdjęcia: ≥1 na każdy produkt, ≥2 dla 50 wybranych produktów, w rozdzielczości pozwalającej na ostre powiększenie (miniatury nieakceptowane) — *stan: 34 zebrane produkty bez zdjęć; importer je pomija*
- [x] Ograniczenie tempa: **≤2 zapytania/s** (weryfikacja w kodzie i logach)
- [x] Respektowanie `robots.txt`
- [x] Identyfikacja nagłówkiem User-Agent
- [x] Możliwość przerwania i wznowienia bez ponownego pobierania zapisanych danych
- [x] Walidacja względem schematu (JSON Schema / pydantic), błędy w logu
- [ ] 0 produktów bez nazwy, ceny, opisu lub zdjęć — *stan: 63 bez pełnego opisu, 34 bez zdjęć*
- [x] Testy jednostkowe parsowania na zapisanych lokalnie stronach HTML
- Dane wyłącznie do celów dydaktycznych — sklep nie może być publicznie dostępny w internecie

### W3. Sklep na PrestaShop 8.x (8 pkt)

**Środowisko**

- [x] **[K]** Sklep działa w zestawie kontenerów zarządzanych przez Docker Compose v2
- [ ] **[K]** Uruchomienie z czystego klona według README: jedna komenda startowa + jedna komenda inicjalizacji danych (np. `docker compose up -d` i `make init`); **≤15 min** do działającego sklepu z danymi — *stan: `make up` + `make init` (#7); lokalnie `make up` ok. 1 min, `make init` 4 min 31 s; do potwierdzenia na czystym klonie z pobieraniem obrazów*
- [x] **[K]** Ruch wyłącznie przez HTTPS z self-signed certyfikatem; HTTP → **301** na HTTPS
- [ ] E-maile trafiają do Mailpit/MailHog: wiadomość po rejestracji i po złożeniu zamówienia

**Funkcjonalność**

- [ ] **[K]** Bez błędów działają: menu górne, stopka, wyszukiwarka, rejestracja, logowanie, lista produktów, karta produktu, koszyk, zakup, historia zamówień
- [ ] **[K]** Interfejs klienta po polsku, poprawne polskie znaki
- [x] Strony CMS z treściami dostosowanymi do sklepu (bez tekstów z instalatora i lorem ipsum):
  - [x] O sklepie
  - [x] Regulamin
  - [x] Polityka prywatności
  - [x] Dostawa
  - [x] Formy płatności
- [x] Informacja o plikach cookies

**Dane**

- [ ] **[K]** ≥1000 produktów (chyba że sklep źródłowy ma mniej)
- [ ] **[K]** ≥4 kategorie, każda z ≥2 podkategoriami, 0 pustych
- [ ] **[K]** Nazwy, opisy, zdjęcia, ceny i stawki VAT zgodne ze źródłem — **10 z 10** losowych produktów zgodnych
- [ ] Stan magazynowy każdego produktu i wariantu: 0–10 szt.
- [ ] **5–20%** produktów ze stanem 0

**Konfiguracja sprzedaży**

- [x] ≥2 metody płatności stosowane w Polsce, w tym **przelew tradycyjny** i **płatność przy odbiorze**, bez integracji z operatorami płatności
- [x] Brak metod płatności niestosowanych w Polsce
- [x] 2 nowych przewoźników o różnych opłatach
- [x] Darmowa dostawa dla zamówień powyżej **2000 zł brutto**
- [x] Dostawa niemożliwa dla zamówień o wadze powyżej **50 kg**

**Metryki**

- [ ] 0 odpowiedzi 4xx/5xx (poza celowymi 404) — crawler prowadzącego, ≥200 podstron
- [ ] 0 błędów JS w konsoli na stronie głównej, kategorii, produktu i w koszyku
- [ ] Lighthouse Performance strony głównej ≥60 (desktop, z ignorowaniem certyfikatu)

### W4. Testy E2E (5 pkt)

Skrypt Playwright w trybie headless wykonuje w całości w **≤5 min**:

- [ ] 1. Dodanie do koszyka 10 produktów w różnych ilościach, z dwóch różnych kategorii — *stan: `tests/e2e/koszyk.spec.ts` (PR `feat/2/e2e-cart-tests`), nieuruchomiony na pełnym imporcie*
- [ ] 2. Wyszukanie produktu po nazwie i dodanie losowego produktu z wyników — *stan: `tests/e2e/koszyk.spec.ts` (PR `feat/2/e2e-cart-tests`), nieuruchomiony na pełnym imporcie*
- [ ] 3. Usunięcie z koszyka 3 produktów — *stan: `tests/e2e/koszyk.spec.ts` (PR `feat/2/e2e-cart-tests`), nieuruchomiony na pełnym imporcie*
- [ ] 4. Rejestracja nowego konta
- [ ] 5. Złożenie zamówienia na zawartość koszyka
- [ ] 6. Wybór płatności przy odbiorze
- [ ] 7. Wybór jednego z dwóch nowych przewoźników
- [ ] 8. Zatwierdzenie zamówienia
- [ ] 9. Sprawdzenie statusu zamówienia
- [ ] 10. Pobranie faktury VAT

Warunki dodatkowe:

- [ ] **[K]** Testy uruchamia jedna komenda opisana w README; adres sklepu przekazywany parametrem lub zmienną środowiskową (w etapie 2 te same testy idą na klaster)
- [ ] Każdy krok ma asercję sprawdzającą efekt, nie tylko wykonanie kliknięcia — *stan: jest tylko test dymny*
- [ ] Raport (JUnit XML lub HTML) i zrzut ekranu przy błędzie
- [ ] Brak `sleep` jako głównego mechanizmu synchronizacji
- [ ] Stabilność: 3 z 3 kolejnych uruchomień zakończone sukcesem

### Wymagania dodatkowe etapu 1 (20 pkt)

Oceniane tylko po zaliczeniu W1–W4; możliwe punkty częściowe.

#### D1. Wygląd sklepu (5 pkt)

- [ ] Wybrany wariant:
  - Wariant A: układ identyczny/zbliżony do sklepu źródłowego (bez wymogu kolorystyki)
  - Wariant B: autorski, estetyczny wygląd dopasowany do asortymentu
- [x] Na stronie głównej ≥1 działający baner w tematyce sklepu
- [ ] Poprawne działanie przy szerokości ekranu 360 px
- [ ] Lighthouse Accessibility ≥85
- [x] Zmiany jako **motyw potomny (child theme)**, bez edycji plików motywu Classic

#### D2. Import danych przez API (4 pkt)

- [ ] Skrypt tworzy przez Webservice API kategorie, podkategorie i produkty (zdjęcia, ceny, VAT, stany, waga) z wyników scrapowania
- [x] Idempotentność: ponowne uruchomienie aktualizuje rekordy, 0 duplikatów — *drugie `make init`: 2332 zaktualizowane, 0 utworzonych, 0 zduplikowanych `reference`*
- [x] Klucz API w zmiennej środowiskowej, uprawnienia ograniczone do potrzebnych zasobów
- [x] Raport liczby utworzonych, zaktualizowanych i odrzuconych rekordów
- [x] Import 1000 produktów ze zdjęciami ≤30 min (log skryptu) — *2332 produkty ze zdjęciami w 4 min 1 s (`Czas wykonania` w logu importera)*

#### D3. Promocje i warianty produktów (3 pkt)

- [ ] ≥20 produktów z promocją cenową (stara cena, rabat, nowa cena) — *stan: importer nie tworzy `specific_prices`*
- [ ] Przy każdej promocji najniższa cena z 30 dni przed obniżką (**dyrektywa Omnibus**) — gotowy moduł lub własny
- [ ] ≥5 produktów z ≥2 wariantami, każdy wariant z osobnym stanem magazynowym

#### D4. Backup i odtwarzanie (3 pkt)

- [x] Skrypty w `deploy/` tworzą kopię (zrzut bazy, zdjęcia, pliki konfiguracyjne) i odtwarzają z niej sklep — *`deploy/backup.sh` (`make backup`) i `deploy/restore.sh` (`make restore`), [Backup.md](Backup.md); kopia 415 MB w 18 s, odtworzenie w 50 s, liczby produktów, kategorii, klientów, zamówień i zdjęć zgodne z manifestem*
- [x] Eksport ustawień w repo pozwala przywrócić konfigurację; bez danych osobowych i sekretów — *`deploy/config/configuration.json` (`make config-export`, `make config-import`): 376 ustawień i 19 językowych, 33 wykluczone (sekrety, e-mail admina, środowisko, ID z instancji, wersje); gitleaks: 0 znalezisk*
- [x] Demonstracja odtworzenia na czystym środowisku na odbiorze w **≤10 min** — *sprawdzone przed odbiorem: nowy `git clone`, wygenerowany `.env` z innymi portami, hasłem bazy i katalogiem admina, usunięte obrazy sklepu i proxy; `CONFIRM=tak make restore` w 46 s z budowaniem obrazów; potem `make import` 0 utworzonych i 0 duplikatów, `make test-e2e` 2/2; procedura w [Backup.md](Backup.md#demonstracja-na-czystym-środowisku-odbiór-10-min)*

#### D5. Ciągła integracja jakości kodu (2 pkt)

- [x] Pipeline (GitHub Actions / GitLab CI) dla każdego PR: linter (np. ruff, eslint) + testy jednostkowe scrapera
- [ ] Żaden PR nie scalony przy nieudanym pipeline (weryfikacja ręczna)

#### D6. Dziennik AI i decyzje architektoniczne (3 pkt)

- [ ] Dziennik AI zgodny z formatem, zakończony refleksją zespołu — *stan: brak refleksji*
- [x] ≥3 ADR w `docs/adr/`: kontekst, rozważane opcje, decyzja, konsekwencje (np. biblioteka scrapera, sposób importu, architektura kontenerów, przechowywanie zdjęć)

### Odbiór etapu 1

1. [ ] **Oddanie wersji** — najpóźniej 48 h przed spotkaniem tag `etap1` na `main` + release; oceniana tylko oznaczona wersja
2. **Weryfikacja wstępna** — prowadzący klonuje repo, uruchamia sklep wg README, mierzy metryki; brak uruchomienia z czystego klona = W3 niezaliczone
3. **Prezentacja zespołu (≤10 min)** — działający sklep, testy E2E na żywo, omówienie architektury
4. **Obrona indywidualna (~5 min/os.)** — pytania o kod, PR lub wpis z dziennika AI, także o części innych osób
5. **Modyfikacja na żywo (≤15 min/os.)** — na własnym komputerze, na lokalnie uruchomionym sklepie; dokumentacja i AI dozwolone, trzeba wyjaśnić zmianę

Przykładowe zadania modyfikacji:

- zmiana progu darmowej dostawy na 1500 zł i pokazanie efektu w koszyku
- dodanie do scrapera nowego atrybutu i aktualizacja schematu walidacji
- dodanie do E2E kroku sprawdzającego stronę Regulamin
- naprawa celowo zepsutej konfiguracji kontenera (zmienna środowiskowa, port)
- zmiana treści lub linku baneru
- dodanie wariantu do produktu przez skrypt importu lub panel

---

## Etap 2 — Docker Swarm, CI/CD, GA4

**Warunek przystąpienia: zaliczony etap 1.** Sklep na klastrze musi spełniać co najmniej wymagania obowiązkowe etapu 1.

### Środowisko klastra i narzędzia

- [ ] Dokładnie **jeden stack** Docker Swarm, wdrożony `docker stack deploy` z pliku kompozycji w repo
- [ ] Nazwa stacku, porty i dane dostępowe do bazy zgodne z przydziałem z instrukcji klastra
- [ ] Dostęp przez VPN i SSH — danych nie commitować
- [ ] Plik kompozycji w formacie Compose Specification; zasoby i repliki w sekcji `deploy`
- [ ] Rejestr: **GitHub Container Registry (GHCR), obrazy publiczne**, `linux/amd64`, tag wersji lub skrótu commita
- [ ] Baza: wyłącznie przydzielona baza i użytkownik na wspólnym serwerze bazodanowym
- [ ] CI/CD: GitHub Actions lub GitLab CI, sekrety w ustawieniach repo (GitLab Free — 400 min/mies., obrazy budować na self-hosted runnerze)
- [ ] Wszystkie obrazy w kompozycji, także pomocnicze (Mailpit, Redis itp.), jako własne kopie w GHCR — limit Docker Hub: 100 anonimowych pobrań / 6 h / IP
- [ ] W pipeline logowanie do Docker Hub darmowym kontem przed pobraniem obrazów bazowych
- [ ] Analityka: Google Analytics 4 (Universal Analytics i „cele” nie istnieją od 2023 r. — w GA4 zdarzenia i kluczowe zdarzenia)
- [ ] Baner zgody na cookies zgodny z **Consent Mode v2**
- Usługi zużywające nadmiernie CPU/RAM lub zajmujące cudze porty mogą zostać zatrzymane bez ostrzeżenia

### Dziennik AI (kontynuacja)

- [ ] ≥2 nowe wpisy na osobę w `docs/AI_LOG.md`
- [ ] Refleksja zespołu za etap 2
- [ ] Do AI nie trafiają dane VPN, klastra, bazy, rejestru ani konta Google (zastępować przykładowymi wartościami)
- [ ] Opis weryfikacji wygenerowanych konfiguracji Swarm, pipeline i GA4 z aktualną dokumentacją (typowe pułapki: składnia UA, przestarzałe akcje CI, opcje Compose ignorowane przez Swarm)

### W1. Obrazy i kompozycja (6 pkt)

- [ ] **[K]** Dockerfile dla własnych obrazów + plik kompozycji w `deploy/` wdrażający sklep na klaster
- [ ] **[K]** Kompozycja używa wyłącznie gotowych obrazów z GHCR (także pomocniczych), **bez sekcji `build`**
- [ ] **[K]** Obrazy dla `linux/amd64`, oznaczone konkretną wersją lub skrótem commita — `latest` nie może być jedynym tagiem
- [ ] **[K]** Na klastrze dokładnie jeden stack zespołu, zgodny z przydzieloną nazwą i portami
- [ ] Obrazy bez sekretów, katalogu `install` i plików deweloperskich
- [ ] Hasła i klucze jako Docker secrets lub zmienne środowiskowe spoza repo
- [ ] Budowanie wieloetapowe lub inne techniki redukcji rozmiaru — obraz sklepu **≤1,2 GB** (bez zdjęć)
- [ ] 0 sekretów w obrazach i repo (gitleaks + inspekcja warstw)
- [ ] Wdrożenie stacku ≤10 min do działającego sklepu

### W2. Sklep działający na klastrze (5 pkt)

- [ ] **[K]** Spełnione wszystkie wymagania obowiązkowe etapu 1 (funkcjonalność, dane, HTTPS, przewoźnicy, płatności, język polski)
- [ ] **[K]** Sklep korzysta z bazy na wspólnym serwerze bazodanowym klastra
- [ ] Zdjęcia i pliki przesyłane do sklepu w wolumenie — przetrwają restart kontenera
- [ ] Healthchecki i polityka restartu po awarii dla usług
- [ ] Powiadomienia e-mail działają (SMTP prowadzącego lub własny Mailpit)
- [ ] 0 odpowiedzi 4xx/5xx (poza celowymi 404) — crawler, ≥200 podstron
- [ ] Lighthouse Performance strony głównej ≥60 (desktop)

### W3. Integracja z Google Analytics 4 (5 pkt)

- [ ] **[K]** Właściwość i strumień danych GA4; prowadzący ma rolę co najmniej **Czytelnik**
- [ ] **[K]** Zdarzenia e-commerce z parametrami `value`, `currency`, `items` (moduł lub implementacja muszą obsługiwać GA4):
  - [ ] `view_item`
  - [ ] `add_to_cart`
  - [ ] `begin_checkout`
  - [ ] `purchase`
- [ ] **[K]** W **standardowych raportach** dane o odwiedzinach i wartości zamówień z ≥48 h przed odbiorem (widok czasu rzeczywistego nie wystarcza)
- [ ] ≥20 zdarzeń `purchase` z wartością (raport Monetyzacja)
- [ ] ≥50 sesji (raport Pozyskiwanie)
- [ ] Baner Consent Mode v2: przed zgodą znaczniki analityczne nie zapisują cookies
- [ ] Umiejętność pokazania poprawności zdarzeń w **DebugView**
- Raporty standardowe mają opóźnienie 24–48 h — integracja **co najmniej tydzień przed odbiorem**

### W4. Testy E2E na klastrze (4 pkt)

- [ ] **[K]** Testy z etapu 1 wykonują wszystkie kroki na sklepie w klastrze w ≤5 min
- [ ] 3 z 3 uruchomień zakończone sukcesem
- [ ] Zamówienia testowe rozpoznawalne (np. testowy e-mail)
- [ ] Ruch testowy wykluczony w GA4 lub możliwy do odfiltrowania

### Wymagania dodatkowe etapu 2 (20 pkt)

Oceniane tylko po zaliczeniu W1–W4; możliwe punkty częściowe.

#### D1. Automatyczna inicjalizacja bazy danych (4 pkt)

- [ ] Przy pierwszym starcie stacku automatyczna inicjalizacja: schemat, konfiguracja, kategorie, produkty, zdjęcia z archiwum w Releases — bez ręcznych kroków w panelu
- [ ] Po inicjalizacji sklep spełnia wymagania obowiązkowe etapu 1
- [ ] Ponowne uruchomienie nie nadpisuje danych ani nie tworzy duplikatów
- [ ] Domena i ustawienia SSL przez zmienne środowiskowe, nie na stałe w zrzucie bazy
- [ ] Wdrożenie z automatyczną inicjalizacją ≤20 min

#### D2. Pipeline CI/CD (5 pkt)

- [ ] (2 pkt) Automatyczne uruchomienie po push do `main` i budowa obrazu sklepu
- [ ] (1 pkt) Testy (co najmniej testy jednostkowe scrapera i linter) przed publikacją obrazu
- [ ] (1 pkt) Skan podatności obrazu (np. Trivy) z opublikowanym raportem; obraz z podatnościami krytycznymi nie jest publikowany — **0 krytycznych z dostępną poprawką**
- [ ] (1 pkt) Publikacja obrazu z tagiem wersji/SHA i aktualizacja usługi na klastrze — przez self-hosted runner w sieci klastra (jeśli instrukcja pozwala) lub jeden skrypt wdrożeniowy (runnery GitHuba nie mają dostępu przez VPN)
- [ ] Czas od push do opublikowania obrazu ≤15 min

#### D3. Zasoby i odporność na awarie (3 pkt)

- [ ] Każda usługa ma górne limity CPU (vCore) i RAM w `deploy.resources`, dobrane na podstawie pomiaru
- [ ] Szczyt pamięci ≤80% limitu, 0 restartów z braku pamięci podczas testu obciążeniowego
- [ ] Hasła i klucze jako **Docker secrets**
- [ ] Aktualizacja usługi bez przerwy lub z przerwą **≤30 s** (`update_config` + healthchecki)

#### D4. Wydajność i cache (3 pkt)

- [ ] Cache włączony podczas odbioru (Smarty, CCC, OPcache, opcjonalnie Redis/Memcached)
- [ ] Test obciążeniowy (k6 lub Locust) na klastrze przed i po włączeniu cache; raport z porównaniem w `docs/`
- [ ] Przy 20 równoczesnych użytkownikach przez 2 min:
  - [ ] p95 ≤1,5 s dla strony głównej
  - [ ] p95 ≤2 s dla strony kategorii
  - [ ] odsetek błędów <1%
  - [ ] spadek p95 o ≥30% względem pomiaru bez cache

#### D5. Kluczowe zdarzenia w GA4 (3 pkt)

- [ ] Kluczowe zdarzenie zakończonej rejestracji (`page_view` strony po rejestracji lub własne `sign_up`)
- [ ] Własne zdarzenie emitowane po stronie sklepu przy kliknięciu baneru lub dodaniu do koszyka produktu w promocji, oznaczone jako kluczowe
- [ ] Lejek w Eksploracjach GA4: wyświetlenie produktu → dodanie do koszyka → rozpoczęcie zamówienia → zakup
- [ ] Pokazanie w GA4 historii osiągnięcia obu kluczowych zdarzeń

#### D6. Bezpieczeństwo i obserwowalność (2 pkt)

Jedna z opcji:

- [ ] **Opcja A:** skan bazowy OWASP ZAP sklepu na klastrze, raport w `docs/`, usunięcie lub uzasadnienie wszystkich alertów wysokiego ryzyka
- [ ] **Opcja B:** monitoring usług stacku (np. cAdvisor + Prometheus + Grafana albo Uptime Kuma) z dashboardem dostępności oraz zużycia CPU i pamięci

### Odbiór etapu 2

1. [ ] **Oddanie wersji** — najpóźniej 48 h przed spotkaniem tag `etap2` na `main`; na klastrze działa stack z tej wersji
2. **Weryfikacja wstępna** — stack na klastrze, rejestr obrazów, historia pipeline, dostęp do GA4, metryki
3. **Prezentacja zespołu (≤10 min)** — sklep na klastrze, testy E2E, omówienie pipeline i raportów GA4
4. **Scenariusz awarii (≤15 min, cały zespół)** — prowadzący np. usuwa usługę, zmienia obraz na nieistniejący tag lub ogranicza pamięć; zespół diagnozuje i przywraca sklep **bez utraty danych**. Przekroczenie czasu = **−2 pkt** z wyniku zespołowego
5. **Obrona indywidualna (~5 min/os.)** — kompozycja, Dockerfile, pipeline, GA4, dziennik AI, także części innych osób
6. **Modyfikacja na żywo (≤15 min/os.)** — zmiana musi trafić na klaster

Przykładowe zadania modyfikacji:

- zmiana limitu pamięci usługi i wdrożenie bez przerwy w działaniu
- nowy parametr własnego zdarzenia GA4 pokazany w DebugView
- zwiększenie liczby replik i wyjaśnienie wpływu na sesje użytkowników
- dodanie kroku do pipeline (np. dodatkowy tag obrazu) i uruchomienie go
- zmiana treści baneru, build przez pipeline, aktualizacja usługi
- odczytanie logów usługi i wskazanie przyczyny celowego błędu

---

## Ocenianie (oba etapy)

- Każdy etap: **40 pkt** — 20 pkt obowiązkowe + 20 pkt dodatkowe
- Zaliczenie etapu: wszystkie warunki **[K]** + **≥50% punktów w każdym z W1–W4**
- Wynik indywidualny = punkty zespołu × współczynnik indywidualny

### Punktacja

| Wymaganie | Etap 1 | Etap 2 |
|---|---|---|
| W1 | Repozytorium i proces — 3 | Obrazy i kompozycja — 6 |
| W2 | Scraper — 4 | Sklep na klastrze — 5 |
| W3 | Sklep PrestaShop — 8 | Google Analytics 4 — 5 |
| W4 | Testy E2E — 5 | Testy E2E na klastrze — 4 |
| D1 | Wygląd sklepu — 5 | Automatyczna inicjalizacja DB — 4 |
| D2 | Import przez API — 4 | Pipeline CI/CD — 5 |
| D3 | Promocje i warianty — 3 | Zasoby i odporność — 3 |
| D4 | Backup i odtwarzanie — 3 | Wydajność i cache — 3 |
| D5 | CI jakości kodu — 2 | Kluczowe zdarzenia GA4 — 3 |
| D6 | Dziennik AI i ADR — 3 | Bezpieczeństwo / obserwowalność — 2 |
| **Razem** | **40** | **40** |

### Współczynnik indywidualny

| Współczynnik | Kryterium |
|---|---|
| 1,0 | Swobodnie wyjaśnia kod/wdrożenie i decyzje zespołu, modyfikację wykonuje samodzielnie |
| 0,75 | Wyjaśnia własną część, w pozostałych ma luki; modyfikację wykonuje z drobną pomocą |
| 0,5 | Rozumie wyłącznie fragmenty własnej pracy, modyfikacji nie kończy |
| 0 | Nie potrafi wyjaśnić własnego kodu ani konfiguracji ani wykonać modyfikacji |

Osoba ze współczynnikiem 0 ma prawo do jednej poprawkowej obrony w ciągu 2 tygodni; po niej współczynnik wynosi najwyżej 0,75.

### Skala ocen

| Procent | Punkty | Ocena |
|---|---|---|
| 100% | 40 | 5,0 |
| od 90% | 36–39,5 | 4,5 |
| od 75% | 30–35,5 | 4,0 |
| od 65% | 26–29,5 | 3,5 |
| od 50% | 20–25,5 | 3,0 |
| poniżej 50% | poniżej 20 | 2,0 |
