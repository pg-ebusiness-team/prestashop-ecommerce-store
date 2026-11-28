# Wygląd sklepu źródłowego (luksusowealkohole.pl)

Analiza układu na potrzeby FRONT-2 (Wariant A: układ zbliżony do źródła, bez wymogu kolorystyki).
Źródło działa na płatnym motywie **Winecy** (Codezeel, `/themes/Winecy/`). Jego kodu nie kopiujemy –
układ odtwarzamy własnym kodem w `custom-child-theme` (dziedziczy po Classic).

Analiza na podstawie zrzutów w szerokości 1440 px (strona główna, kategoria, produkt, koszyk, menu, karta po najechaniu).
Zrzuty są poza repo – grafiki źródła są chronione prawem autorskim.

## Ogólny styl

- Minimalistyczny, „premium”: dużo bieli, jasnoszare tła sekcji (`#f8f8f8`), cienkie beżowe linie.
- Treść w kontenerze ~1140 px, wyśrodkowana; slider i paski menu na pełną szerokość.
- Typografia: nagłówki szeryfowe (Playfair Display), treść bezszeryfowa (Lato).
  Menu, przyciski i etykiety pisane wersalikami z dużym odstępem liter.
- Tytuły sekcji: duży szeryfowy napis na środku z poziomą linią po obu stronach (`—— Tytuł ——`).
- Przyciski: prostokątne, bez zaokrągleń. Główne beżowe (`#e6ded7`) z ciemnym tekstem,
  drugorzędne białe z grafitową ramką („Zobacz wszystkie produkty”).
- Kolory i fonty są już w `shop/themes/custom-child-theme/assets/css/custom.css` (FRONT-1).

## Nagłówek (wspólny dla wszystkich stron)

1. **Górny pasek** (biały, cienka linia pod spodem):
   po lewej link „Poznaj specjalną ofertę dla firm i restauracji »”, po prawej telefon i e-mail z ikonami.
2. **Środek nagłówka**: logo wyśrodkowane. Po prawej wyszukiwarka (pole „Szukaj...” z ikoną lupy w ramce),
   pod nią „ZALOGUJ SIĘ” z rozwijaną listą i ikona torby-koszyka z licznikiem.
   Lewa strona pusta.
3. **Menu główne**: jasnoszary pasek na pełną szerokość, 6 pozycji wersalikami, równo rozłożonych:
   Prezenty, Whisky & Bourbon, Alkohole & likiery, Wino & Champagne, Opakowania & Słodycze, Oferta dla firm.
   Aktywna pozycja i hover w kolorze beżowo-złotym (`#a48d66`).
   Menu przykleja się do góry przy przewijaniu (sticky).
4. **Rozwijane menu**: biały panel pod paskiem, podkategorie (jeden poziom) w siatce 6 kolumn,
   wersaliki, cienka beżowa linia pod każdą pozycją.
5. **Pasek korzyści** (tylko strona główna): beżowy pasek z 3 komórkami z ikonami –
   „Wysyłka gratis od 450 zł*”, „Karty podarunkowe”, „Wyjątkowe promocje”.

## Strona główna (kolejność sekcji)

1. **Slider** na pełną szerokość: mały nadtytuł, duży szeryfowy tytuł, podtytuł, przycisk z białą ramką.
2. **„Polecamy w szczególności”**: 4 kafelki kategorii (zdjęcie + nazwa na szarym tle pod spodem).
3. **2 banery obok siebie**: ciemne zdjęcie, tytuł, podpis, przycisk „Zobacz produkty” z białą ramką.
4. **„W naszej ofercie”** (szare tło): zakładki Wszystkie / Bestsellery / Nowości (każda ma 8 produktów), siatka 4×2,
   przycisk „Zobacz wszystkie produkty”.
5. **„Nasz poradnik”**: 3 karty wpisów blogowych.
6. **„Kup taniej”** (szare tło): 4 produkty w promocji, przycisk „Wszystkie produkty wyprzedażowe”.
7. **„Opinie klientów”**: w źródle pusta sekcja (widżet zewnętrzny).
8. **„Ostatnie wpisy na naszym blogu”**: 3 karty wpisów.
9. Stopka.

## Karta produktu na liście (miniatura)

- Zdjęcie na białym tle, pod nim szary blok (`#f1f1f1`) z wyśrodkowaną nazwą (szeryfowa, jedna linia, obcięta „…”)
  i ceną.
- Promocja: beżowa ukośna wstęga „Promocja” w lewym górnym rogu, stara cena przekreślona obok nowej,
  pod ceną „Najniższa cena w ciągu 30 dni: …” (Omnibus).
- **Po najechaniu**: ikona oka (szybki podgląd) w prawym górnym rogu zdjęcia,
  beżowy pasek „Dodaj do koszyka” na dole zdjęcia, blok nazwy i ceny zmienia tło na grafitowe z białym tekstem.
- Siatka: 4 kolumny na stronie głównej i w sekcjach produktu, 3 kolumny w kategorii (obok lewej kolumny).

## Strona kategorii

1. Ścieżka nawigacji z elementami oddzielonymi poziomą kreską (`luksusowealkohole.pl —— Alkohole —— Alkohole & likiery`).
2. Duży szeryfowy tytuł kategorii, pod nim opis (zwijany „Pokaż więcej” przy długim tekście).
3. **„Podkategorie”**: same nazwy w prostokątnych ramkach-przyciskach, w wierszu (bez zdjęć).
4. Lewa kolumna **„Filtruj według”** w ramce: cena (suwak), producenci, kraj, rodzaj, pojemność –
   checkboxy z liczbą produktów, długie listy zwinięte pod „więcej...”.
5. Nad siatką po prawej: wybór „Produktów na stronę”.
6. Siatka 3 kolumn miniatur.

## Strona produktu

1. Ścieżka nawigacji jak w kategorii.
2. **Lewa połowa**: duże zdjęcie w cienkiej ramce z przyciskiem powiększenia, pod nim miniatury ze strzałkami,
   drobna uwaga o możliwej różnicy zdjęcia.
3. **Prawa połowa**: nazwa (szeryfowa), krótki opis, indeks, informacja o wariantach,
   wybór wariantu (np. pojemność), cena, pole ilości ze strzałkami, beżowy przycisk „Dodaj do koszyka”.
4. Pod spodem, oddzielone beżową linią, dwie kolumny: **„Opis produktu”** i **„Szczegóły”**
   (tabela cech: kraj, alkohol, wiek – wiersze oddzielone liniami). Bez zakładek.
5. **„Kup razem z”** i **„Podobne produkty”**: siatki 4 kolumn miniatur na szarym tle.

## Koszyk

- Duży tytuł „Koszyk”, link „‹ Kontynuuj zakupy”.
- Po lewej lista produktów: miniatura w ramce, nazwa, wariant, cena jedn., pole ilości, suma, ikona kosza.
- Po prawej dwa boksy w ramce: **„Podsumowanie”** (liczba produktów, dostawa, ile brakuje do darmowej dostawy,
  razem brutto, beżowy przycisk „Przejdź do kasy”) oraz **„Kod rabatowy”** (pole + przycisk „Zastosuj”).

## Stopka

- Jasnoszare tło, 4 kolumny:
  1. logo, krótki opis sklepu, adres, telefony, e-mail (z ikonami),
  2. **Produkty**: promocje, nowe produkty, najczęściej kupowane, kategorie,
  3. **Nasza firma**: dostawa, polityka prywatności, regulamin, o nas, płatności, kontakt, mapa strony,
  4. **Subskrybuj newsletter**: tekst, pole e-mail z ikoną koperty, reCAPTCHA.
- Dolny pasek: ikony Facebook i Instagram po lewej, „© 2026 luksusowealkohole.pl” na środku.

## Elementy, które pomijamy

| Element | Powód |
| --- | --- |
| Blog („Nasz poradnik”, „Ostatnie wpisy”) | Classic nie ma bloga; wymagałby osobnego modułu |
| „Opinie klientów”, widżet TrustMate | zewnętrzny serwis |
| Przycisk WhatsApp | zewnętrzny serwis |
| reCAPTCHA w newsletterze | zewnętrzny serwis |
| Bramka wieku 18+ | poza zakresem FRONT-2; dodana w FRONT-4 (`templates/_partials/age-gate.tpl`, ADR 0002) |
| Widok mobilny | osobny ticket o responsywności; Classic jest responsywny domyślnie |

## Implementacja w motywie potomnym (FRONT-2)

Ścieżki względem `shop/themes/custom-child-theme/`. Wszystkie style są w `assets/css/custom.css`; nadpisane szablony Classic rozszerzają oryginał (`extends parent:`), gdzie się da. Treści i ustawienia modułów wgrywa `deploy/init/theme.sql`, grafiki źródła pobiera `make theme` z listy `deploy/init/home-images.txt` (poza repo, [ADR 0001](adr/0001-grafiki-strony-glownej.md)).

| Obszar | Pliki | Rozwiązanie |
|---|---|---|
| Nagłówek | `templates/_partials/header.tpl`, `config/theme.yml` | Górny pasek (link „oferta dla firm”, telefon, e-mail), logo pośrodku, po prawej wyszukiwarka, konto i koszyk. Menu `ps_mainmenu` w osobnym pasku z rozwijaną siatką 6 kolumn. Na stronie głównej pasek korzyści („Wysyłka gratis od 2000 zł*” — próg z wymagań, w źródle 450 zł). Usunięte `displayNav1/2`, więc nie ma przełączników języka i waluty. Logo `PS_LOGO` = `cms/home/logo.jpg`. |
| Strona główna | `config/theme.yml`, `templates/index.tpl`, `templates/catalog/_partials/home-products.tpl`, `modules/ps_{featuredproducts,bestsellers,newproducts,specials}/…` | `displayHome`: 8 slajdów `ps_imageslider` i `ps_customtext` z kafelkami „Polecamy w szczególności” i 2 banerami (linki przez wyszukiwarkę, bo ID kategorii zmieniają się po imporcie). Moduły produktów podpięte pod własny hook `displayHomeProducts`: zakładki Bootstrapa „W naszej ofercie” (Wszystkie / Bestsellery / Nowości, po 8 produktów; pusta zakładka znika) i sekcja „Kup taniej” (4 produkty). `ps_banner` wyłączony. |
| Miniatura produktu | `templates/catalog/_partials/miniatures/product.tpl` | Ikona szybkiego podglądu i pasek „Dodaj do koszyka” (AJAX z `core.js`) po najechaniu, na dotyku zawsze widoczne; gdy produktu nie da się dodać z listy — „Zobacz produkt”. Wstęga „Promocja” zamiast flag Classic. Nazwa w jednej linii z „…”. |
| Stopka | `templates/_partials/footer.tpl`, `modules/ps_linklist/…/linkblock.tpl`, `modules/ps_emailsubscription/…`, `modules/ps_socialfollow/…` | 4 kolumny: logo i dane kontaktowe sklepu (fikcyjne, z `theme.sql`), „Produkty”, „Nasza firma” (strony CMS, kontakt, mapa strony), newsletter. Dolny pasek: Facebook, Instagram, copyright. |
| Kategoria | `templates/catalog/listing/category.tpl`, `templates/_partials/breadcrumb.tpl`, `templates/catalog/_partials/{category-header,subcategories}.tpl`, `templates/_partials/pagination.tpl` | Tytuł, opis i podkategorie (same nazwy w ramkach) na całą szerokość nad lewą kolumną. Okruszki z poziomymi kreskami. W lewej kolumnie tylko filtry `ps_facetedsearch` (`ps_categorytree` wyłączony). Paginacja z „Pokazano x–y z z”. Białe tło wszystkich stron. |
| Produkt | `templates/catalog/product.tpl`, `modules/ps_categoryproducts/…` | Kolejność jak w źródle: nazwa, krótki opis, indeks, warianty, cena (w bloku podmienianym przez `core.js` po zmianie wariantu), ilość, przycisk. Pod spodem dwie kolumny „Opis produktu” i „Szczegóły” zamiast zakładek, „Kup razem z” i 4 „Podobne produkty”. Wyłączone `productcomments`, `ps_sharebuttons`, `blockreassurance` (włączenie w panelu je przywróci). |
| Koszyk | `templates/checkout/cart.tpl`, `templates/checkout/_partials/{cart-detailed-totals,cart-voucher}.tpl` | Tytuł „Koszyk”, „Kontynuuj zakupy” nad listą, po prawej boksy „Podsumowanie” (z wierszem „Do darmowej dostawy brakuje: …” liczonym z `PS_SHIPPING_FREE_PRICE`) i „Kod rabatowy” (pole zawsze widoczne). Klasy `js-*` z Classic zostają, więc `core.js` odświeża boksy. |

Poprawka przy okazji: `theme.sql` naprawia ścieżki ikon `blockreassurance` (instalator zapisuje `//modules/...`, co dawało błędy `ERR_NAME_NOT_RESOLVED` w konsoli).

### Późniejsze zmiany

- Link „Poznaj specjalną ofertę dla firm i restauracji »” w górnym pasku prowadzi do strony CMS „Oferta dla firm” (`shop/cms/6-oferta-dla-firm.html`).
- Kolumna „Produkty” w stopce ma linki do kategorii z menu. `theme.sql` wyszukuje je po nazwie, dlatego `make theme` idzie po imporcie.
- Opis kategorii: część po `<!-- więcej -->` w `shop/categories/*.html` jest zwinięta pod przyciskiem „Pokaż więcej” (`category-header.tpl`, collapse z Classic).
- Pod ceną na miniaturze i karcie produktu moduł `omnibusprice` pokazuje „Najniższa cena z 30 dni: …” (hook `displayProductPriceBlock`, typ `after_price`; styl `.omnibus-price` w `custom.css`). Opis modułu w README.
- Baner cookies i okno 18+ (`templates/_partials/cookie-banner.tpl`, `age-gate.tpl`, ADR 0002).

### Znane ograniczenia

- Menu nie jest sticky, bo wymagałoby JS.
- Sekcje produktów są puste do czasu importu (`make init` usuwa dane demo). Bestsellery są ukryte, dopóki nie ma zamówień.
- `make theme` wymaga dostępu do luksusowealkohole.pl.
- Na telefonie slider nie ma osobnych grafik (źródło ma wersje `_m`). To temat ticketu o responsywności.
- Dane kontaktowe w stopce i nazwa w copyright pochodzą z konfiguracji sklepu. `theme.sql` ustawia przykładowe, fikcyjne dane (Luksusowe Alkohole, ul. Przykładowa 1, 00-001 Warszawa, `sklep@example.com`, telefon +48 123 456 789, faks 22 000 00 00). To nie są dane sklepu źródłowego, żeby sklep testowy nie kierował klientów do istniejącej firmy.
- Brak reCAPTCHA w newsletterze (zewnętrzny serwis, w tabeli pominiętych).
- Kategoria: nie ma wyboru „Produktów na stronę” ze źródła (Classic go nie ma; zostaje sortowanie). Sekcje filtrów nie zwijają się na komputerze (strzałki ^ w źródle).
- Produkt: „Indeks” nie zmienia się po wyborze innego wariantu (pokazuje indeks produktu). „Kup razem z” pojawia się dopiero, gdy produkt ma akcesoria (dane demo ich nie mają). Załączniki i dodatkowe zakładki modułów (Classic: zakładki) nie są wyświetlane. Miniatury zdjęć bez strzałek ze źródła (Classic przewija je tylko przy wielu zdjęciach).
- Koszyk: boks „Kod rabatowy” pojawia się dopiero, gdy w sklepie istnieje choć jedna reguła koszyka (PrestaShop wtedy włącza kody). Wiersz „Do darmowej dostawy brakuje” bierze próg z `PS_SHIPPING_FREE_PRICE`, które przy każdym starcie kontenera ustawia `configure-sales.php` (ADR 0003). Liczy brakującą kwotę od sumy produktów, bez kodów rabatowych.
