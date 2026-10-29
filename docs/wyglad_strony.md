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
4. **„W naszej ofercie”** (szare tło): zakładki Wszystkie / Bestsellery / Nowości, siatka 4×2 produktów,
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
| Zakładki „W naszej ofercie” | zastępujemy osobnymi sekcjami: polecane, nowości, bestsellery |
| Przycisk WhatsApp | zewnętrzny serwis |
| reCAPTCHA w newsletterze | zewnętrzny serwis |
| Bramka wieku 18+ | potrzebna, ale poza zakresem FRONT-2 (osobny ticket) |
| Widok mobilny | osobny ticket o responsywności; Classic jest responsywny domyślnie |

## Jak odtwarzamy to w Classic

| Element | Rozwiązanie |
| --- | --- |
| Górny pasek, logo, wyszukiwarka, konto, koszyk, pasek korzyści | nadpisany `templates/_partials/header.tpl` + CSS; moduły `ps_contactinfo`, `ps_searchbar`, `ps_customersignin`, `ps_shoppingcart` |
| Menu z rozwijanym panelem | `ps_mainmenu` + CSS (struktura `sub-menu` z Classic pasuje do siatki 6 kolumn) |
| Slider, banery, kafelki kategorii | `ps_imageslider`, `ps_banner`, `ps_customtext` (własne grafiki, nie ze źródła) |
| Sekcje produktów na głównej | `ps_featuredproducts`, `ps_newproducts`, `ps_bestsellers`, `ps_specials` – kolejność w `displayHome` w `theme.yml` |
| Miniatura z „Dodaj do koszyka” | nadpisany `templates/catalog/_partials/miniatures/product.tpl` + CSS |
| Kategoria (filtry, podkategorie) | `ps_facetedsearch`, `ps_categorytree`; podkategorie bez zdjęć przez nadpisanie szablonu lub CSS |
| Produkt: opis i szczegóły obok siebie, „Kup razem z”, „Podobne” | CSS / nadpisanie szablonu produktu; `ps_crossselling`, `ps_categoryproducts` |
| Stopka z kolumną logo | nadpisany `templates/_partials/footer.tpl`; `ps_linklist`, `ps_contactinfo`, `ps_emailsubscription`, `ps_socialfollow` |
| Tytuły sekcji z liniami po bokach | CSS (`::before` / `::after`) |
