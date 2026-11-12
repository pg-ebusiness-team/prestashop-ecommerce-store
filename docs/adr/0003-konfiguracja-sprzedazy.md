# ADR 0003: Konfiguracja sprzedaży skryptem PHP uruchamianym przy starcie kontenera

- Status: zaakceptowany
- Data: 2026-11-07
- Zadanie: konfiguracja sprzedaży (płatności, przewoźnicy, ograniczenia dostawy)

## Kontekst

W3 etapu 1 wymaga: przelewu tradycyjnego i płatności przy odbiorze (bez metod niestosowanych w Polsce), 2 nowych
przewoźników o różnych opłatach, darmowej dostawy powyżej 2000 zł brutto i braku dostawy powyżej 50 kg.
Od tej konfiguracji zależą testy E2E (płatność przy odbiorze, wybór nowego przewoźnika, pobranie faktury).

Ograniczenia:

- sklep musi działać z czystego klona: jedna komenda startowa + jedna komenda inicjalizacji danych;
  konfiguracja nie może istnieć tylko w panelu, bo `make reset` ją kasuje;
- w etapie 2 (D1) baza ma się inicjalizować automatycznie przy pierwszym starcie stacku na klastrze, bez ręcznych
  kroków;
- na odbiorze typowe modyfikacje to np. zmiana progu darmowej dostawy na 1500 zł — zmiana ma być prosta;
- przewoźnik w PrestaShop to ~10 powiązanych tabel (`carrier`, `carrier_lang`, `carrier_shop`, `carrier_zone`,
  `carrier_group`, `range_weight`, `delivery`, `carrier_tax_rules_group_shop`, `module_carrier`), a po edycji
  w panelu dostaje nowe `id_carrier` (stałe zostaje tylko `id_reference`).

## Rozważane opcje

1. **Ręcznie w panelu + zrzut bazy.** Najszybsze, ale konfiguracji nie widać w repo i w review, zrzut zawiera
   domenę i dane instalacji, a każda zmiana wymaga nowego zrzutu.
2. **Plik SQL uruchamiany przez `make`** (jak `deploy/init/theme.sql`). Spójne z repo, ale przewoźnika trzeba
   ręcznie złożyć z wielu tabel i odtworzyć logikę PrestaShop (`id_reference`, powiązania z modułami płatności,
   cache); instalacji modułu w SQL nie da się poprawnie zrobić (hooki). Dokłada też komendę do README.
3. **Webservice API.** Ma zasoby `carriers`, `weight_ranges`, `deliveries`, ale nie obsługuje modułów ani większości
   kluczy konfiguracji, a klucz API musiałby dostać uprawnienia wykraczające poza import danych (D2).
4. **Skrypt PHP na klasach PrestaShop, uruchamiany przez init-script przy każdym starcie kontenera.**

## Decyzja

Opcja 4.

- `shop/scripts/configure-sales.php` ładuje `config/config.inc.php` i używa klas `Module`, `Configuration`,
  `OrderState` (a w kolejnych etapach `Carrier`, `RangeWeight`). PrestaShop sam pilnuje powiązanych tabel i cache.
- `shop/init-scripts/20-configure-sales.sh` uruchamia go jako `www-data` po instalacji, przed startem Apache —
  tym samym mechanizmem co konfiguracja poczty (`10-configure-mail.sh`).
- Skrypt jest idempotentny: zmienia tylko to, co odbiega od opisanego stanu; przewoźników rozpoznaje po
  `id_reference`, więc kolejne starty nie tworzą duplikatów. `Carrier::add()` sam nadaje `id_reference = id_carrier`,
  więc skrypt zapisuje je po utworzeniu w konfiguracji (`SALES_CARRIER_REF_STANDARD`, `SALES_CARRIER_REF_EXPRESS`) —
  tak samo robią to moduły przewoźników PrestaShop.
- Przewoźnicy spoza skryptu (z instalatora, danych demo albo dodani w panelu) są przy starcie wyłączani, nie usuwani,
  bo mogą się do nich odwoływać zamówienia.
- Plik PHP leży w obrazie w `/usr/local/share/shop-init/`, a nie w `/tmp/init-scripts/`, bo `docker_run.sh`
  wykonuje każdy plik z tego katalogu.

## Konsekwencje

- Konfiguracja jest w repo, przechodzi review i działa po `make reset` bez dodatkowej komendy.
- Ten sam obraz na klastrze sam się skonfiguruje przy starcie (krok w stronę D1 etapu 2).
- Zmiany wprowadzone w panelu zostaną nadpisane przy kolejnym starcie kontenera — źródłem prawdy jest repo
  (tak samo jak w `theme.sql` i `cms.sql`). Trzeba to wiedzieć przed modyfikacją na odbiorze.
- Próg darmowej dostawy i limit wagi są w zmiennych środowiskowych (`FREE_SHIPPING_THRESHOLD`,
  `MAX_ORDER_WEIGHT_KG` w `deploy/compose.yaml`), więc ich zmiana nie wymaga przebudowy obrazu — wystarczy `make up`.
- Próg działa tak, jak liczy go PrestaShop: od wartości koszyka z VAT, po rabatach, bez kosztu dostawy,
  z warunkiem `>=`. Wymaganie mówi „powyżej 2000 zł”, a sklep daje darmową dostawę już od 2000,00 zł — różnica
  jednego grosza, akceptowana zamiast nadpisywania klasy `Cart`.
- Limit wagi to `max_weight` przewoźnika, a nie górna granica przedziału wag: PrestaShop porównuje go warunkiem
  „waga koszyka > limit” niezależnie od darmowej dostawy, więc zamówienie ważące dokładnie 50 kg przechodzi,
  a cięższe nie ma żadnego przewoźnika. Granica przedziału jest wyłączna (`[od, do)`), więc 50 kg by nie przeszło.
- Aktywna jest tylko Polska. Płatności są przypisane wyłącznie do niej, więc adres w innym kraju dałby w koszyku
  komunikat o braku metod płatności. Kraje są wyłączane, nie usuwane — adresy kont demo w USA i Francji zostają.
- Start kontenera wydłuża się o czas jednego wywołania PHP (ładowanie PrestaShop, kilka zapytań).
- Błąd konfiguracji zatrzymuje start kontenera (`docker_run.sh` działa z `set -e`, a skrypt kończy się kodem 1),
  inaczej niż przy poczcie (`10-configure-mail.sh`), której brak nie psuje sprzedaży. Sklep z ustawieniami
  z instalatora (płatność czekiem, domyślni przewoźnicy) nie spełniałby wymagań, a jedyny ślad błędu w logu łatwo
  przeoczyć. Kontener, który nie wstaje, widać od razu w `make ps`; przyczyna jest w logu jako
  `20-configure-sales: BLAD: ...`. Chwilowe błędy (np. baza jeszcze niegotowa) znikają przy restarcie, bo skrypt
  jest idempotentny. Na klastrze (etap 2) trwały błąd da pętlę restartów usługi — widoczną w `docker service ps`.
- Zamówienie za pobraniem ma fakturę od razu po złożeniu (stan „Oczekiwanie na płatność przy odbiorze” dostaje
  flagę `invoice`), bo klient musi ją pobrać w testach E2E. Zamówienie przelewem dostaje fakturę dopiero po
  zmianie stanu na „Płatność zaakceptowana”.
