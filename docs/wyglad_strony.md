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

## Jak odtwarzamy to w Classic

| Element | Rozwiązanie |
| --- | --- |
| Górny pasek, logo, wyszukiwarka, konto, koszyk, pasek korzyści | nadpisany `templates/_partials/header.tpl` + CSS; moduły `ps_contactinfo`, `ps_searchbar`, `ps_customersignin`, `ps_shoppingcart` |
| Menu z rozwijanym panelem | `ps_mainmenu` + CSS (struktura `sub-menu` z Classic pasuje do siatki 6 kolumn) |
| Slider, banery, kafelki kategorii | `ps_imageslider`, `ps_customtext`; grafiki i teksty jak w źródle, pobierane przy `make theme` (ADR 0001) |
| Sekcje produktów na głównej | `ps_featuredproducts`, `ps_bestsellers`, `ps_newproducts` jako zakładki „W naszej ofercie”, `ps_specials` jako „Kup taniej” – hook `displayHomeProducts` + `templates/index.tpl` |
| Miniatura z „Dodaj do koszyka” | nadpisany `templates/catalog/_partials/miniatures/product.tpl` + CSS |
| Kategoria (filtry, podkategorie) | `ps_facetedsearch`, `ps_categorytree`; podkategorie bez zdjęć przez nadpisanie szablonu lub CSS |
| Produkt: opis i szczegóły obok siebie, „Kup razem z”, „Podobne” | CSS / nadpisanie szablonu produktu; `ps_crossselling`, `ps_categoryproducts` |
| Stopka z kolumną logo | nadpisany `templates/_partials/footer.tpl`; `ps_linklist`, `ps_contactinfo`, `ps_emailsubscription`, `ps_socialfollow` |
| Tytuły sekcji z liniami po bokach | CSS (`::before` / `::after`) |

## Zmiany w kodzie (FRONT-2)

Stan po wszystkich częściach FRONT-2: nagłówek, strona główna, miniatura produktu, sekcje produktów, stopka, kategoria i produkt.

### Nagłówek

| Plik | Zmiana |
| --- | --- |
| `templates/_partials/header.tpl` (nowy) | Górny pasek: link „Poznaj specjalną ofertę dla firm i restauracji »” (na razie do strony kontaktu), telefon i e-mail sklepu z ikonami. Środek: pusta lewa kolumna, logo pośrodku, po prawej wyszukiwarka (`displaySearch`), a pod nią konto i koszyk (`{widget}` `ps_customersignin`, `ps_shoppingcart`). Menu (`displayTop`) jest w osobnym pasku. Na stronie głównej dochodzi pasek korzyści (Wysyłka gratis od 2000 zł* - próg z `WYMAGANIA.md`, w źródle 450 zł; Karty podarunkowe, Wyjątkowe promocje, który prowadzi do promocji). |
| `config/theme.yml` | Usunięte hooki `displayNav1`/`displayNav2`, bo kontakt, konto i koszyk renderuje `header.tpl`. Dzięki temu znikają też przełączniki języka i waluty. `displayTop` zawiera tylko `ps_mainmenu`. |
| `assets/css/custom.css` | Górny pasek (flex, ikony wyrównane do tekstu). Logo wyśrodkowane i zmniejszone do 70% szerokości kolumny. Wyszukiwarka do 260 px z lupą po prawej. Konto i koszyk pisane wersalikami, bez ikony użytkownika i bez słowa „Koszyk”. Menu w jasnoszarym pasku: pozycje wersalikami (12 px, odstęp liter 2 px), równo rozłożone, hover w kolorze beżowo-złotym. Rozwijane menu: panel na całą szerokość, siatka 6 kolumn z beżową linią. Pasek korzyści w 3 komórkach, środkowa ciemniejsza. Poniżej 768 px elementy idą w kolumnę. |
| `deploy/init/home-images.txt`, `deploy/init/theme.sql` | Logo źródła (`logo.jpg`) pobierane przez `make theme`. `PS_LOGO` = `cms/home/logo.jpg`, więc Classic sam podaje wymiary i link do strony głównej. |

### Strona główna

| Plik | Zmiana |
| --- | --- |
| `config/theme.yml` | Kolejność `displayHome`: slider, blok tekstowy (kafelki i banery), polecane, bestsellery, nowości, promocje. `ps_banner` wyłączony (`to_disable`), bo oba banery są w `ps_customtext`. |
| `deploy/init/theme.sql` (nowy) | 8 slajdów `ps_imageslider` z tekstami ze źródła (nadtytuł, tytuł, podtytuł, przycisk „sprawdź naszą ofertę”) dla wszystkich języków. Treść `ps_customtext`: sekcja „Polecamy w szczególności” z 4 kafelkami kategorii i 2 banery (Kosze prezentowe, Duże pojemności & miniaturki). Linki prowadzą przez wyszukiwarkę, bo ID kategorii zmienią się po imporcie. Skrypt jest idempotentny i nadpisuje zmiany z panelu. |
| `deploy/init/home-images.txt` (nowy) | Lista `nazwa URL`: 8 slajdów, 4 kafelki, 2 banery i logo. Grafiki nie są w repo (ADR 0001). |
| `makefile` (`make theme`) | Po włączeniu motywu pobiera grafiki do `img/cms/home/` (przy błędzie przerywa i podaje nazwę pliku), wgrywa `theme.sql` i czyści cache. |
| `assets/css/custom.css` | Slider na pełną szerokość, przyklejony do paska korzyści. Od 768 px ma zawsze 700 px wysokości (`object-fit: cover`, zdjęcie przybliżone i przycięte). Gradient od lewej pod tekstem. Podpis wyrównany do lewej krawędzi kontenera: tytuł w Playfair 4.5rem, przycisk z białą ramką. Tytuły sekcji szeryfowe z liniami po bokach, bez wersalików Classic. Kafelki w siatce 4 kolumn (na telefonie 2), banery w 2 kolumnach z tekstem na prawej części zdjęcia (na telefonie 1 kolumna, tekst pod zdjęciem). Na telefonie podpis slajdu jest pod zdjęciem, na grafitowym tle. |
| `docs/adr/0001-grafiki-strony-glownej.md` (nowy) | Decyzja: grafiki identyczne ze źródłem, pobierane przy inicjalizacji zamiast trzymania ich w repo. |
| `README.md` | Opis `make theme`: pobiera grafiki (wymaga internetu), wgrywa treści i nadpisuje zmiany z panelu. |

### Miniatura produktu

| Plik | Zmiana |
| --- | --- |
| `templates/catalog/_partials/miniatures/product.tpl` (nowy, na bazie Classic) | W rogu zdjęcia sama ikona oka (szybki podgląd Classic, z `aria-label`). Na dole zdjęcia pasek „Dodaj do koszyka”: formularz do koszyka obsługiwany AJAX-em z `core.js` (`data-button-action="add-to-cart"`) otwiera okno koszyka. Gdy produktu nie da się dodać z listy (brak w magazynie, wymagana personalizacja), w tym miejscu jest link „Zobacz”. Wstęga „Promocja” przy obniżonej cenie zamiast flag Classic („Nowy”, „-20%”, „Pakiet”). Pełna nazwa produktu, obcinana przez CSS. Bez procentu rabatu i bez linków do wariantów. |
| `assets/css/custom.css` | Szary blok nazwy (Playfair 1.25rem, jedna linia z „…”) i ceny bez pogrubienia. Po najechaniu lub fokusie z klawiatury blok robi się grafitowy z białym tekstem, a z dołu zdjęcia wysuwa się beżowy pasek „Dodaj do koszyka” (po najechaniu czarny) i pojawia się ikona oka. Na ekranach dotykowych (`hover: none`) pasek i oko są widoczne zawsze. Ukośna wstęga w kolorze `#8a7350` (brand-500 przyciemniony do kontrastu 4.5:1). Serce `blockwishlist` ukryte w miniaturze. |
| `deploy/init/theme.sql` | Poprawka ikon `blockreassurance`: instalator zapisuje `//modules/...`, przez co na stronie produktu i w koszyku pojawiały się błędy `ERR_NAME_NOT_RESOLVED` w konsoli. |

### Sekcje produktów na stronie głównej

| Plik | Zmiana |
| --- | --- |
| `templates/index.tpl` (nowy, `extends parent:index.tpl`) | Po `displayHome` (slider, kafelki, banery) jest sekcja „W naszej ofercie” na szarym tle z zakładkami Wszystkie / Bestsellery / Nowości. To zakładki Bootstrapa z Classic (`data-toggle="tab"`), bez własnego JS. Zakładka, której moduł nic nie zwraca (bestsellery bez zamówień), jest pomijana. Pod spodem jest sekcja „Kup taniej”. |
| `config/theme.yml` | `displayHome` ma tylko slider i `ps_customtext`. Moduły produktów (`ps_featuredproducts`, `ps_bestsellers`, `ps_newproducts`, `ps_specials`) są podpięte pod własny hook `displayHomeProducts`, który `index.tpl` wywołuje osobno dla każdego modułu (`mod=...`). |
| `templates/catalog/_partials/home-products.tpl` (nowy) | Wspólna siatka: 4 kolumny (`col-lg-3`), od 576 px 2, na telefonie 1. Pod spodem przycisk z ramką. |
| `modules/{ps_featuredproducts,ps_bestsellers,ps_newproducts,ps_specials}/views/templates/hook/*.tpl` (nowe) | Zawartość zakładek z przyciskami: „Zobacz wszystkie produkty” / „bestsellery” / „nowości”. `ps_specials` renderuje własną sekcję „Kup taniej” z przyciskiem „Wszystkie produkty wyprzedażowe”. Jest na białym tle, bo w źródle oddziela ją od szarej „W naszej ofercie” blog, którego nie mamy. |
| `assets/css/custom.css` | Odstępy sekcji. Szare tło na całą szerokość okna (`box-shadow` + `clip-path`). Zakładki: prostokąty z beżową ramką i wersalikami, aktywna na beżowym tle, na telefonie dzielą szerokość po równo. Przycisk z grafitową ramką. |
| `deploy/init/theme.sql` | Liczba produktów jak w źródle: po 8 w każdej zakładce, 4 w „Kup taniej”. |
| `templates/catalog/_partials/miniatures/product.tpl` | Link dla produktów, których nie da się dodać z listy: „Zobacz produkt” (Classic nie ma polskiego tłumaczenia „View”). |

### Stopka

| Plik | Zmiana |
| --- | --- |
| `templates/_partials/footer.tpl` (nowy) | 4 kolumny jak w źródle. Pierwsza: logo (przezroczysta wersja ze źródła, `footer-logo.png`), opis sklepu ze źródła oraz adres, telefon, faks i e-mail z ikonami. Dane kontaktowe biorą się z konfiguracji sklepu (`$shop`). Kolejne kolumny: „Produkty” i „Nasza firma” (`ps_linklist`) oraz newsletter (`ps_emailsubscription`). Dolny pasek: ikony Facebook i Instagram (`ps_socialfollow`) po lewej, „© rok nazwa sklepu” na środku. Moduły są wywoływane po nazwie (`mod=...`), żeby trafiły do właściwych kolumn. Okna `blockwishlist` i `displayFooterAfter` zostają na końcu. |
| `modules/ps_linklist/views/templates/hook/linkblock.tpl` (nowy) | Każdy blok linków to osobna kolumna (`nav` z nagłówkiem), bez zwijania z Classic. |
| `modules/ps_emailsubscription/views/templates/hook/ps_emailsubscription.tpl` (nowy) | Tytuł i tekst ze źródła. Pole z linią pod spodem, a obok koperta jako przycisk wysyłki (z `aria-label`). Pola formularza, komunikaty i hooki zgód (RODO) jak w Classic. |
| `modules/ps_socialfollow/ps_socialfollow.tpl` (nowy) | Same ikony (szare SVG z Classic, `.icon-gray`), bez bloku, gdy nie ma linków. |
| `assets/css/custom.css` | Styl stopki z FRONT-1 zastąpiony: siatka 4 kolumn (poniżej 992 px 2, poniżej 576 px 1). Nagłówki w Playfair. Linki i nagłówki pisane od wielkich liter jak w źródle (`capitalize`). Newsletter bez białego tła z Classic. Dolny pasek z linią u góry. |
| `deploy/init/theme.sql` | Bloki linków: „Produkty” i „Nasza firma” (pl), bez linku „Sklepy”. Polskie tytuły i adresy stron CMS z danych demo: Dostawa, Polityka prywatności, Regulamin, O nas, Płatności (treść dodana w FRONT-4: `shop/cms/`). Linki Facebook i Instagram ze źródła. |
| `deploy/init/home-images.txt` | `footer-logo.png` ze źródła. |

### Strona kategorii

| Plik | Zmiana |
| --- | --- |
| `templates/catalog/listing/category.tpl` (nowy, `extends parent:`) | Tytuł, opis i podkategorie na całą szerokość nad lewą kolumną, jak w źródle. Są dołożone do bloku `breadcrumb` layoutu, który leży przed wierszem kolumn, a w prawej kolumnie usunięte. Filtrowanie AJAX dalej podmienia nagłówek po `id="js-product-list-header"`. |
| `templates/_partials/breadcrumb.tpl` (nowy) | Kopia Classic bez wewnętrznego `{block name='breadcrumb'}`. Ma tę samą nazwę co blok layoutu, więc nadpisanie go w `category.tpl` dublowało nagłówek. |
| `templates/catalog/_partials/category-header.tpl` (nowy) | Duży tytuł (h1 także na kolejnych stronach) i opis (tylko na 1. stronie), bez karty i zdjęcia kategorii. |
| `templates/catalog/_partials/subcategories.tpl` (nowy) | Same nazwy podkategorii w ramkach, bez zdjęć. |
| `templates/_partials/pagination.tpl` (nowy) | „Pokazano x-y z z” po lewej, numery w kwadratach po prawej, strzałki z tekstem tylko dla czytników ekranu (`sr-only`), `aria-current` na bieżącej stronie. |
| `config/theme.yml` | W `displayLeftColumn` tylko filtry (`ps_facetedsearch`). `ps_categorytree` jest w `to_disable`, bo bez tego zostałby w starym hooku. |
| `assets/css/custom.css` | Białe tło wszystkich stron (Classic: szare). Ścieżka z poziomymi kreskami zamiast „/”. Tytuł kategorii w Playfair 4rem (na telefonie 2.25rem). Podkategorie w beżowych ramkach. Filtry w beżowej ramce: tytuł „Filtruj według” bez wersalików, sekcje oddzielone linią, liczby produktów wyrównane do prawej, kwadratowe checkboxy, grafitowy suwak ceny. Nad siatką samo sortowanie (liczba produktów jest w paginacji). Paginacja: aktualna strona na beżowym tle. |

### Strona produktu

| Plik | Zmiana |
| --- | --- |
| `templates/catalog/product.tpl` (nowy, `extends parent:`) | Kolejność jak w źródle: nazwa, krótki opis, „Indeks”, warianty, cena, ilość i „Dodaj do koszyka”. Cena jest przeniesiona do bloku `product_discounts` w `.product-container`, więc `core.js` dalej podmienia ją po zmianie wariantu. Pod zdjęciem uwaga o możliwej różnicy zdjęcia (tekst ze źródła), bez flag „Nowy”/„-20%”. Zamiast zakładek Classic pod spodem są dwie kolumny: „Opis produktu” i „Szczegóły” (tabela cech produktu). Dalej „Kup razem z” (akcesoria produktu) na szarym tle. |
| `modules/ps_categoryproducts/views/templates/hook/ps_categoryproducts.tpl` (nowy) | „Podobne produkty” w stylu sekcji ze strony głównej, siatka 4 kolumn. |
| `config/theme.yml` | `displayFooterProduct`: `ps_categoryproducts` zamiast opinii. W `to_disable`: `productcomments` (opinie), `ps_sharebuttons` (udostępnianie), `blockreassurance` (blok „Security/Delivery/Return policy” na produkcie i w koszyku). W źródle ich nie ma, a przy włączeniu modułu w panelu wrócą. Usunięte z list hooków, żeby nie wisiały tam wyłączone moduły. |
| `assets/css/custom.css` | Zdjęcie w cienkiej ramce, powiększenie jako beżowy kwadrat w rogu (zamiast warstwy na całym zdjęciu). Nazwa w Playfair 2.25rem. Cena 1.75rem pogrubiona, bezszeryfowa. Wysokie pole ilości (4rem) i beżowy przycisk z wersalikami. Bez etykiety „Ilość”, bo pole ma `aria-label`. Kolumny opisu i szczegółów oddzielone od góry beżową linią, wiersze tabeli cech z beżową linią. Na telefonie jedna kolumna. Sekcje produktów (`.home-products`) działają teraz na każdej stronie, a `#wrapper` ucina poziomy nadmiar szarego tła wszędzie, nie tylko na głównej. |
| `deploy/init/theme.sql` | 4 „Podobne produkty” jak w źródle (domyślnie 16). |

### Koszyk

| Plik | Zmiana |
| --- | --- |
| `templates/checkout/cart.tpl` (nowy, `extends parent:`) | Duży tytuł „Koszyk” nad listą, „Kontynuuj zakupy” nad produktami (w Classic był pod spodem). Po prawej dwa boksy: „Podsumowanie” (sumy i przycisk do kasy) oraz „Kod rabatowy”. Klasy `.js-cart-detailed-totals` i `.js-cart-voucher` zostają z Classic, więc `core.js` dalej odświeża oba boksy po zmianie ilości i dodaniu kodu. |
| `templates/checkout/_partials/cart-detailed-totals.tpl` (nowy) | Sumy z Classic bez kodu rabatowego (jest w osobnym boksie). Nowy wiersz „Do darmowej dostawy brakuje: …” liczony z progu `PS_SHIPPING_FREE_PRICE` (Sklep > Wysyłka > Preferencje). Bez progu wiersza nie ma. Próg zmienia się w `deploy/compose.yaml` (ADR 0003), bo zmianę z panelu nadpisze kolejny start kontenera. |
| `templates/checkout/_partials/cart-voucher.tpl` (nowy) | Pole kodu zawsze widoczne, bez zwijanego „Masz kod promocyjny?”. Placeholder „Wpisz kod rabatowy”, przycisk „Zastosuj”. Ten sam plik jest w podsumowaniu zamówienia (checkout). |
| `assets/css/custom.css` | Tytuł 4rem, miniatura w beżowej ramce, nazwa w Playfair, wysokie pole ilości. Boksy w beżowej ramce z szeryfowym tytułem, wiersze sum wersalikami z kwotą po prawej, sekcje oddzielone beżową linią, przycisk do kasy na całą szerokość. Kod rabatowy: pole z linią pod spodem i przycisk obok. |

### Znane ograniczenia

- Menu nie jest sticky, bo wymagałoby JS.
- Link dla firm prowadzi do strony kontaktu.
- Sekcje produktów są puste do czasu importu (`make init` usuwa dane demo). Bestsellery są ukryte, dopóki nie ma zamówień.
- `make theme` wymaga dostępu do luksusowealkohole.pl.
- Na telefonie slider nie ma osobnych grafik (źródło ma wersje `_m`). To temat ticketu o responsywności.
- Miniatura nie pokazuje „Najniższa cena w ciągu 30 dni” (Omnibus). PrestaShop nie ma tego natywnie, potrzebny byłby moduł.
- Dane kontaktowe w stopce i nazwa w copyright pochodzą z konfiguracji sklepu. `theme.sql` ustawia przykładowe, fikcyjne dane (Luksusowe Alkohole, ul. Przykładowa 1, 00-001 Warszawa, `sklep@example.com`, telefon +48 123 456 789, faks 22 000 00 00). To nie są dane sklepu źródłowego, żeby sklep testowy nie kierował klientów do istniejącej firmy.
- Kolumna „Produkty” nie ma jeszcze linków do kategorii ze źródła (Whisky & Bourbon itd.), bo `theme.sql` ich nie ustawia, a ID kategorii są znane dopiero po imporcie.
- Brak reCAPTCHA w newsletterze (zewnętrzny serwis, w tabeli pominiętych).
- Kategoria: nie ma wyboru „Produktów na stronę” ze źródła (Classic go nie ma; zostaje sortowanie). Długi opis nie zwija się pod „Pokaż więcej”. Sekcje filtrów nie zwijają się na komputerze (strzałki ^ w źródle).
- Produkt: „Indeks” nie zmienia się po wyborze innego wariantu (pokazuje indeks produktu). „Kup razem z” pojawia się dopiero, gdy produkt ma akcesoria (dane demo ich nie mają). Załączniki i dodatkowe zakładki modułów (Classic: zakładki) nie są wyświetlane. Miniatury zdjęć bez strzałek ze źródła (Classic przewija je tylko przy wielu zdjęciach).
- Koszyk: boks „Kod rabatowy” pojawia się dopiero, gdy w sklepie istnieje choć jedna reguła koszyka (PrestaShop wtedy włącza kody). Wiersz „Do darmowej dostawy brakuje” bierze próg z `PS_SHIPPING_FREE_PRICE`, które przy każdym starcie kontenera ustawia `configure-sales.php` (ADR 0003). Liczy brakującą kwotę od sumy produktów, bez kodów rabatowych.
