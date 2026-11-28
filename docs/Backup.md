# Kopia zapasowa, odtwarzanie i eksport ustawień

Wymaganie D4 etapu 1 ([WYMAGANIA.md](WYMAGANIA.md)): skrypty w `deploy/` tworzą kopię (zrzut bazy, zdjęcia, pliki konfiguracyjne) i odtwarzają z niej sklep, eksport ustawień w repo pozwala przywrócić konfigurację bez danych osobowych i sekretów, a odtworzenie na czystym środowisku trwa ≤10 min. Uzasadnienie rozwiązania: [ADR 0004](adr/0004-backup-i-odtwarzanie.md).

| Polecenie | Skrypt | Co robi |
|---|---|---|
| `make backup` | `deploy/backup.sh` | kopia działającego sklepu do `backups/backup-<data>.tar` |
| `make restore [BACKUP=<plik>]` | `deploy/restore.sh` | odtworzenie sklepu z kopii (domyślnie najnowszej); **usuwa bieżące dane** |
| `make config-export` | `deploy/config/export.php` | zapis ustawień sklepu do `deploy/config/configuration.json` (w repo) |
| `make config-import` | `deploy/config/import.php` | wgranie ustawień z `deploy/config/configuration.json` do działającego sklepu |

## Kopia zapasowa (`make backup`)

Wymaga działającego sklepu (`make up`). Sklep działa w trakcie kopii. Zrzut bazy jest spójny dzięki `mysqldump --single-transaction` (tabele InnoDB), a pliki są czytane z działającego kontenera. U nas kopia ze sklepem po `make init` zajmuje ok. 415 MB i powstaje w ok. 20 s.

Archiwum zawiera:

| Część | Zawartość |
|---|---|
| `db.sql.gz` | zrzut bazy bez `CREATE DATABASE`/`USE`, więc wgrywa się do bazy o dowolnej nazwie (`MYSQL_DATABASE` z bieżącego `.env`) |
| `shop_data.tar.gz` | wolumen `shop_data` (`/var/www/html`) z właścicielami plików: zdjęcia produktów i grafiki (`img/`), `app/config/parameters.php`, katalog panelu admina, moduły. Zawartość `var/cache` i `var/logs` jest pomijana, bo sklep odtwarza ją przy starcie |
| `proxy_certs.tar.gz` | certyfikat HTTPS (`proxy_certs`). Po odtworzeniu przeglądarka nie pyta ponownie o wyjątek |
| `mappings/` | `scraper/importer/*_mapping.json`. Bez nich `make import` po odtworzeniu wgrałby zdjęcia drugi raz ([Importer.md](Importer.md)) |
| `env` | kopia `.env`, tylko informacyjnie (np. hasło admina z chwili kopii). Restore go nie używa, patrz niżej |
| `manifest.txt` | data, commit, wersja PrestaShop, liczba produktów, kategorii, klientów, zamówień i zdjęć, sumy SHA-256 części |

Kopia zawiera dane klientów (konta, adresy, zamówienia z testów E2E), hasło bazy w `parameters.php` i `.env`. Dlatego katalog `backups/` jest w `.gitignore`, archiwum ma uprawnienia `600` i **nie może trafić do repozytorium ani do Releases** (W1 [K]: brak sekretów w repo). Kopia leży na dysku komputera, na którym ją zrobiono, więc przed `make reset` albo przeniesieniem na inny komputer skopiuj plik w bezpieczne miejsce.

Przy błędzie (np. zatrzymana baza, ucięty zrzut bez linii `-- Dump completed`) skrypt kończy się komunikatem `backup: BLAD: ...` i nie zostawia niepełnego archiwum.

## Odtwarzanie (`make restore`)

```bash
make restore                                        # najnowsza kopia z backups/
make restore BACKUP=backups/backup-20261128-011531.tar
CONFIRM=tak make restore BACKUP=...                 # bez pytania o potwierdzenie
```

Kroki `deploy/restore.sh`:

1. Rozpakowanie kopii do katalogu tymczasowego i sprawdzenie sum SHA-256 z manifestu. Do tego momentu nic nie jest zmieniane, więc uszkodzona kopia niczego nie usuwa.
2. Wypisanie nazw zmiennych (bez wartości), którymi `.env` z kopii różni się od bieżącego.
3. Potwierdzenie (`tak`).
4. `docker compose down -v`, czyli usunięcie bieżących kontenerów, bazy i wolumenów, tak jak `make reset`, oraz mapowań importera.
5. Start świeżej bazy z bazą i użytkownikiem z bieżącego `.env` i wgranie zrzutu.
6. Wgranie plików do pustego wolumenu `shop_data`. Docker przy pierwszym montażu kopiuje do wolumenu pliki z obrazu (m.in. `admin/` i `install/`), dlatego skrypt najpierw je usuwa. Potem certyfikat i mapowania.
7. Start sklepu jak `make up`. `docker_run.sh` widzi `parameters.php`, więc nie instaluje PrestaShop od nowa.
8. `make webservice`: klucz Webservice API z bieżącego `.env`.
9. Porównanie liczby produktów, kategorii, klientów, zamówień i zdjęć z manifestem oraz łączny czas.

U nas odtworzenie trwa ok. 1 min (bez pobierania obrazów Dockera).

### Bieżący `.env` opisuje środowisko, kopia dostarcza dane

Restore nie korzysta z `.env` z kopii. Na czystym klonie i tak by się nie dało: `-include .env` w makefile tworzy `.env` z `.env.example` przed każdym poleceniem make, także przed `make restore`. Zamiast tego sklep jest dopasowywany do bieżącego `.env`. Robi to przy każdym starcie kontenera init-script `02-sync-env.sh` ([Docker_Docs.md](Docker_Docs.md#dopasowanie-do-zmiennych-środowiskowych-init-scripts)):

| Ustawienie z kopii | Dopasowywane do |
|---|---|
| dane bazy w `parameters.php` | `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` |
| domena i SSL w bazie oraz `.htaccess` | `SERVER_NAME`, `HTTPS_PORT` |
| nazwa katalogu panelu admina | `ADMIN_FOLDER` |
| klucz Webservice API (`make webservice`) | `PS_API_KEY` |

Kopię można więc odtworzyć na innym komputerze, z innymi portami i hasłami. Zostają z kopii:

- **konta**, w tym administratora: do panelu logujesz się e-mailem i hasłem z chwili kopii (są w pliku `env` w archiwum), a nie z `ADMIN_MAIL` i `ADMIN_PASSWD` bieżącego `.env`;
- **certyfikat**: wystawiony dla `SERVER_NAME` z chwili kopii. Przy innym `SERVER_NAME` przeglądarka i tak ostrzega (certyfikat jest samopodpisany), a nowy certyfikat wygeneruje usunięcie wolumenu: `make down`, `docker volume rm deploy_proxy_certs`, `make up`.

Mailpit nie ma wolumenu, więc wiadomości sprzed odtworzenia znikają.

### Demonstracja na czystym środowisku (odbiór, ≤10 min)

Wolumeny mają nazwy z przedrostkiem `deploy_` (nazwa projektu Compose pochodzi od katalogu `deploy/` z `compose.yaml`). Drugi klon na tym samym komputerze używa więc tych samych wolumenów. „Czyste środowisko” na jednym komputerze to `make reset` albo `make restore`, który sam robi `down -v`.

1. Przed odbiorem: `make backup` i skopiowanie archiwum poza katalog repo.
2. Na odbiorze, w nowym klonie repozytorium:
   ```bash
   mkdir backups && cp <ścieżka>/backup-<data>.tar backups/
   CONFIRM=tak make restore
   ```
3. Sprawdzenie: `make ps` (shop `healthy`), sklep pod adresem z końca komunikatu, `make api-check`, `make test-e2e`.

Na czystym klonie `make restore` buduje też obrazy, a przy pierwszym uruchomieniu na komputerze pobiera obrazy bazowe. To doliczy się do ok. 1 min samego odtworzenia.

## Eksport ustawień (`make config-export`, `make config-import`)

Kopia zapasowa nie może trafić do repo, a wymaganie mówi o eksporcie ustawień **w repo**. Dlatego ustawienia sklepu są dodatkowo eksportowane do `deploy/config/configuration.json`, który jest commitowany.

Część konfiguracji jest już w repo jako kod i odtwarza się sama:

| Ustawienia | Gdzie w repo | Kiedy działa |
|---|---|---|
| płatności, przewoźnicy, kraje, darmowa dostawa, limit wagi | `shop/scripts/configure-sales.php` | każdy start kontenera |
| poczta (SMTP) | `shop/init-scripts/10-configure-mail.sh` | każdy start kontenera |
| domena, SSL, dane bazy, katalog admina | `shop/scripts/sync-env.php` | każdy start kontenera |
| motyw, strona główna, menu, stopka, strony CMS | `deploy/init/theme.sql`, `cms.sql`, `shop/cms/` | `make theme` (`make init`) |
| filtry list produktów, opisy kategorii | `deploy/init/facets.php`, `categories.sql` | `make facets`, `make categories` |
| Webservice API | `deploy/init/webservice.sql` | `make webservice` |

Eksport obejmuje całą resztę, czyli wszystkie wartości z `ps_configuration` i `ps_configuration_lang`: ustawienia produktów, zamówień, wyszukiwarki, modułów, danych sklepu itd. W pliku jest 376 ustawień i 19 wartości językowych. Klucze są posortowane, a wartości językowe zapisane po kodzie ISO języka (`pl`), więc zmiana w panelu daje w PR jednolinijkowy diff.

**Wykluczenia.** Lista i powody są w `deploy/config/export.php`, a `make config-export` wypisuje je przy każdym uruchomieniu:

- **sekrety:** nazwy z `KEY`, `TOKEN`, `PASSWD`, `PASSWORD`, `SECRET`, `SALT` (np. `NW_SALT`, `PS_SMARTY_CONSOLE_KEY`, `PS_MAIL_PASSWD`). Wyjątki to ustawienia, które tylko mają te słowa w nazwie (polityka haseł, `PS_TOKEN_ENABLE`);
- **dane osobowe:** każda wartość zawierająca `ADMIN_MAIL` (np. `MA_MERCHANT_MAILS`, `PS_LOGS_EMAIL_RECEIVERS`) oraz login SMTP. Dane sklepu (`PS_SHOP_EMAIL`, adres, telefon) są fikcyjne (`theme.sql`), więc zostają;
- **środowisko:** domena, SSL i SMTP, które przy starcie ustawiają init-scripts ze zmiennych;
- **ID rekordów z instancji:** przewoźnicy (`SALES_CARRIER_REF_*`, `PS_CARRIER_DEFAULT`) i górne menu z ID kategorii (`MOD_BLOCKTOPMENU_ITEMS`). W innej bazie te ID wskazywałyby inne rekordy, a ustawiają je `configure-sales.php` i `theme.sql`;
- **wersje, znaczniki czasu i stan wewnętrzny,** np. `PS_VERSION_DB`, `PS_IMG_UPDATE_TIME`, `PS_NEWSLETTER_RAND`.

Plik sprawdza gitleaks: `gitleaks dir deploy/config` daje 0 znalezisk (to samo sprawdza CI na całym repo).

**Import** zapisuje tylko wartości różne od bieżących, więc ponowne `make config-import` nic nie zmienia. Nie usuwa ustawień nieobecnych w pliku, a na końcu czyści cache. Nie wchodzi do `make init`. Ustawienia, które przy starcie kontenera nadpisują init-scripts, i tak wrócą przy następnym restarcie do wersji z repo.

**Po zmianie ustawień w panelu,** które mają zostać w repo: `make config-export` i commit `deploy/config/configuration.json` w PR.
