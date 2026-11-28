# Odstępstwa od sklepu źródłowego (luksusowealkohole.pl)

Stan na 2026-11-28 (sprawdzone zapytaniami do bazy po pełnym `make init`). Tylko rzeczy zauważone i **jeszcze niewprowadzone**.

**Waga:** **3** — krytyczne, trzeba zrobić · **2** — warto zrobić, brak nie jest tragedią · **1** — odbiega, ale nieważne

## Odstępstwa od oryginału

| # | Waga | Co odbiega | Gdzie | Co zmienić |
|---|:-:|---|---|---|
| 1 | 2 | Kategoria domyślna (okruszki, adres URL) bywa zła: 657 produktów, m.in. wina, ma domyślną „Alkohole na Wielkanoc”. Produkty są już też w swoich właściwych kategoriach, więc „Wino” nie jest pusta | okruszki i URL karty produktu | importer: kategoria domyślna z pola `id_category_default`, a nie z pierwszej kategorii |
| 5 | 2 | Ucięte nazwy podkategorii z „...”, np. „Zestawy alkoholi na...” zamiast „Zestawy alkoholi na prezent” (5 kategorii) | menu, nagłówek kategorii, okruszki, stopka | scraper (pełna nazwa z nagłówka strony kategorii) + ponowny import |
| 13 | 2 | Brak filtra „Producenci”: importer nie wysyła producentów (scraper ma `manufacturer_name` w 520 rekordach), w sklepie są tylko 2 producenci demo | lewa kolumna: Whisky & Bourbon, Alkohole & likiery, okazje | importer (zasób `manufacturers` + uprawnienie w `webservice.sql`), potem `make facets` |
| 14 | 1 | Na stronach okazji (np. Prezenty świąteczne…) brak filtra „Kategorie”. W źródle to drzewo wszystkich 44 kategorii, a nasz moduł pokazuje tylko podkategorie bieżącej kategorii, których okazje nie mają | lewa kolumna stron okazji | motyw/moduł - trudne, raczej zostawić |
| 15 | 1 | Zakres suwaka ceny zaokrąglony do pełnych złotych, np. Likier 10–551 zł zamiast 11–550 zł (źródło: 12–549,99 zł, z groszami). Moduł zaokrągla dół w dół, a górę w górę (`floor`/`ceil` w `ps_facetedsearch`), a cena netto z 6 miejscami daje brutto 10,999999 zamiast 11 | lewa kolumna list produktów, filtr Cena | moduł (poza motywem) albo łatka JS w motywie - nie warto |