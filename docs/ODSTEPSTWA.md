# Odstępstwa od sklepu źródłowego (luksusowealkohole.pl)

Stan na 2026-11-25. Tylko rzeczy zauważone i **jeszcze niewprowadzone**.

**Waga:** **3** — krytyczne, trzeba zrobić · **2** — warto zrobić, brak nie jest tragedią · **1** — odbiega, ale nieważne

## Odstępstwa od oryginału

| # | Waga | Co odbiega | Gdzie | Co zmienić |
|---|:-:|---|---|---|
| 1 | 3 | Wina są w złej kategorii: 592 wina trafiły do „Alkohole na Wielkanoc”, a kategoria „Wino” jest pusta (podobnie 184 likiery i 37 nalewek) | Prezenty › Alkohole na Wielkanoc; Wino & Champagne › Wino | importer: kategoria domyślna z pola `id_category_default`, a nie z pierwszego pliku |
| 2 | 3 | Produkt należy tylko do jednej kategorii, a w źródle do kilku. Przez to 7 podkategorii jest pustych (wymóg W3 [K]: 0 pustych): Wino, Kosze upominkowe, Zestawy upominkowe, Prezenty świąteczne…, Upominki świąteczne…, Zestawy prezentowe na…, Kosze prezentowe na… | listy produktów w tych podkategoriach | importer: przypisać produkt do wszystkich kategorii, w których znalazł go scraper |
| 3 | 3 | „Karty podarunkowe” jest pusta. W źródle link przekierowuje na stronę główną, więc scraper nie znalazł tam produktów | Prezenty › Karty podarunkowe | importer (pominąć kategorię) albo `theme.sql` (ukryć ją) |
| 4 | 3 | W sklepie zostały dane demo z instalatora: 19 produktów, kategorie Clothes / Accessories / Art, cechy Composition / Property. Prowadzący losuje 10 produktów do porównania ze źródłem (W3 [K]) i może trafić na produkt demo | lista produktów, wyszukiwarka, karta produktu | inicjalizacja (`deploy/`) albo importer: usunąć dane demo |
| 5 | 2 | Ucięte nazwy podkategorii z „...”, np. „Zestawy alkoholi na...” zamiast „Zestawy alkoholi na prezent” (5 kategorii) | menu, nagłówek kategorii, okruszki, stopka | scraper (pełna nazwa z nagłówka strony kategorii) + ponowny import |
| 6 | 2 | Brak opisu kategorii pod tytułem (w źródle ma go 24 z 39 kategorii) | strona kategorii, pod nagłówkiem | scraper + importer (szablon już go wyświetla) |
| 7 | 2 | Brak rozwijanej części opisu „Pokaż więcej” (w źródle 13 kategorii) | strona kategorii, pod opisem | scraper + importer (`additional_description`) + motyw (`category-header.tpl`) |