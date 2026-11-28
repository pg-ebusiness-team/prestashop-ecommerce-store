# ADR 0004: Kopia zapasowa całego wolumenu sklepu i dopasowanie do bieżącego `.env` przy odtwarzaniu

- Status: zaakceptowany
- Data: 2026-11-28
- Zadanie: #32, backup i odtwarzanie (D4 etapu 1)

## Kontekst

D4 etapu 1 wymaga skryptów w `deploy/`, które tworzą kopię (zrzut bazy, zdjęcia, pliki konfiguracyjne) i odtwarzają z niej sklep. Odtworzenie na czystym środowisku ma trwać ≤10 min. Wymagany jest też eksport ustawień w repo, bez danych osobowych i sekretów.

Ograniczenia:

- Dane sklepu są w trzech wolumenach: `db_data`, `shop_data` (`/var/www/html`, 824 MB: pliki PrestaShop, zdjęcia z miniaturami, `parameters.php`, katalog admina) i `proxy_certs`. Poza nimi są `.env` i `scraper/importer/*_mapping.json`. Bez mapowań ponowny import wgrywa zdjęcia drugi raz.
- Instalator zapisuje część środowiska na stałe: dane bazy w `parameters.php`, domenę w `ps_shop_url`, `PS_SHOP_DOMAIN*` i `.htaccess` (reguły zdjęć mają warunek na `HTTP_HOST`), a także nazwę katalogu admina. `docker_run.sh` przy pustym wolumenie kopiuje pliki z obrazu i instaluje sklep. Instalację pomija, gdy widzi `parameters.php`.
- Na czystym klonie `-include .env` w makefile tworzy `.env` z `.env.example` przed każdym poleceniem make. Restore zawsze zastaje więc `.env`, zwykle z innymi hasłami niż w kopii.
- Kopia zawiera dane klientów i hasła, więc nie może trafić do repo (W1 [K]) ani do Releases. Limity W1 (repo ≤200 MB, pliki ≤10 MB) jej nie dotyczą.
- W etapie 2 (D1) domena i SSL mają pochodzić ze zmiennych środowiskowych, nie ze zrzutu bazy, a dane bazy na klastrze będą przydzielone.

## Rozważane opcje

Zakres plików:

1. **Tylko `img/` i `parameters.php`.** Mniejsze archiwum, ale odtworzenie wymaga najpierw świeżej instalacji (ok. 3 min), a potem podmiany bazy i plików. Trzeba by też odtwarzać zmiany instalatora: nazwę katalogu admina, usunięcie `install/`, pliki modułów. Pominięcie miniatur i ich ponowne wygenerowanie dla ok. 2900 zdjęć trwa kilka minut.
2. **Cały wolumen `shop_data` bez zawartości `var/cache` i `var/logs`.** Archiwum ma ok. 415 MB, a odtworzenie to rozpakowanie bez instalacji.

Środowisko przy odtwarzaniu:

1. **`.env` z kopii.** Nie działa na czystym klonie, bo make wcześniej tworzy nowy `.env`, a nadpisywanie istniejącego `.env` łamie zasadę z README.
2. **Wymaganie zgodności `.env` z kopią i przerwanie przy różnicy.** Bezpieczne, ale kopii nie da się odtworzyć na innym komputerze ani na klastrze.
3. **Bieżący `.env` opisuje środowisko, kopia dostarcza dane.** Odtworzone dane są dopasowywane do bieżącego `.env`.

Eksport ustawień:

1. **Zrzut SQL wybranych tabel.** Trudno odfiltrować sekrety i dane osobowe, a diffy w PR są nieczytelne.
2. **JSON z `ps_configuration` i `ps_configuration_lang`** przez klasy PrestaShop, z listą wykluczeń.

## Decyzja

- **Cały wolumen** `shop_data`, a do tego zrzut bazy, `proxy_certs`, mapowania, kopia `.env` (informacyjnie) i manifest z sumami SHA-256. Wszystko w jednym archiwum `backups/backup-<data>.tar` (`deploy/backup.sh`, `make backup`).
- **Bieżący `.env` opisuje środowisko.** Dopasowanie robi nowy init-script `shop/init-scripts/02-sync-env.sh` (`shop/scripts/sync-env.php`) przy każdym starcie kontenera, a nie sam restore:
  - dane bazy w `parameters.php`;
  - domena i SSL w bazie, z ponownym wygenerowaniem `.htaccess`;
  - nazwa katalogu admina.

  Klucz API ustawia `make webservice`. Restore (`deploy/restore.sh`, `make restore`) robi `down -v`, wgrywa zrzut do świeżej bazy, czyści wolumen z plików obrazu, rozpakowuje kopię i uruchamia sklep.
- **Eksport ustawień do JSON** (`deploy/config/export.php` i `import.php`, `make config-export` i `make config-import`) z wykluczeniem sekretów, danych osobowych, środowiska, ID rekordów zależnych od instancji, wersji i znaczników czasu.

## Konsekwencje

- Odtworzenie trwa ok. 1 min i działa na innym komputerze, z innymi portami i hasłami, a w etapie 2 także na klastrze z przydzieloną bazą.
- Ubocznie zmiana portu, domeny lub hasła bazy w `.env` nie wymaga już `make reset`. Wystarczy `make up`.
- `02-sync-env` zatrzymuje start kontenera przy błędzie (np. złe hasło bazy), tak jak `20-configure-sales`. Przy zgodnych wartościach niczego nie zapisuje.
- Konta, w tym hasło administratora, oraz certyfikat zostają z kopii. Trzeba to wiedzieć przy logowaniu do panelu po odtworzeniu.
- Kopia jest na dysku lokalnym i zawiera dane osobowe. Jej przechowywanie poza komputerem (np. przed `make reset`) jest po stronie zespołu.
- Kopia z działającego sklepu jest spójna dla bazy (`--single-transaction`). Pliki zapisane w trakcie kopii (np. zdjęcie wgrane w tej samej sekundzie) mogą nie pasować do zrzutu. W sklepie dydaktycznym to akceptowalne.
- Eksport ustawień nie obejmuje multistore: przy ustawieniach przypisanych do sklepu przerywa się błędem.
