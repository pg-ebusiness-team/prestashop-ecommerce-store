# Refleksja zespołu

Z narzędzi AI korzystał cały zespół: trzy osoby z Claude Code, jedna z ChatGPT. Poniższe wnioski wynikają z wpisów w dzienniku.

## Gdzie AI przyspieszyło pracę

Najwięcej czasu zaoszczędziliśmy na pracy żmudnej i powtarzalnej: odwzorowaniu wyglądu sklepu źródłowego w motywie potomnym (szablony, `custom.css`, widok mobilny), spisaniu macierzy filtrów ze stron kategorii źródła, przygotowaniu opisów 19 kategorii oraz skryptach inicjalizujących (Webservice, płatności i przewoźnicy, filtry, kategorie). AI dobrze sprawdziło się też jako pomoc w diagnozie, gdy dostało konkretny objaw: wskazało, że cena z 30 dni jest w innym polu odpowiedzi AJAX niż czytał parser, że przekierowanie 301 generuje Apache z pominięciem `X-Forwarded-Proto`, i że „Dodaj do koszyka” na listach wysyłało `qty=0`, bo filtr `|default:1` nie zamienia zera. Importer kategorii i produktów powstał szybko i zaimportował 2403 produkty bez odrzuceń. Dodatkową korzyścią była dokumentacja pisana razem z kodem.

## Gdzie AI wprowadziło w błąd

Najdroższe były błędy w operacjach na środowisku, a nie w samym kodzie. Claude nadpisał wygenerowany klucz Webservice, a restart przez `make up` odtworzył kontener bez `parameters.php`, co skończyło się reinstalacją PrestaShop i ponownym importem. Skrypt konfiguracji sprzedaży wyłączył wszystkich przewoźników, bo nie ustawiał `id_reference` po `Carrier::add()`. Zdarzały się też pewnie podane, ale błędne twierdzenia: hipoteza o brakujących powiązaniach płatności z przewoźnikami, wpływ `layered_indexable_*` na filtrowanie, zła ścieżka do pliku z kategoriami, rzekomy brak `custom.css` w kontenerze. Mniejsze wpadki to błędne kodowanie XML ucinające polskie znaki, gitleaks skanujący wszystkie gałęzie i nadużywanie `!important`. Część odpowiedzi była nieprecyzyjna lub obok pytania i wymagała dopytywania. Wiele z tych błędów AI poprawiło samo, ale dopiero po uruchomieniu kodu lub obejrzeniu zrzutu ekranu.

## Czego trzeba było nauczyć się samemu

- **Jak działa PrestaShop.** Bez znajomości modelu danych (przewoźnicy, cechy, indeksy filtrów, `specific_prices`) i kolejności kroków inicjalizacji nie dało się ocenić, czy propozycja AI jest poprawna.
- **Weryfikacji.** Każdą zmianę sprawdzaliśmy niezależnie: uruchomieniem od zera, drugim uruchomieniem skryptu (idempotencja), testami, `curl`, Playwrightem i ręcznie w przeglądarce. Sama deklaracja AI, że coś działa, nie wystarczała.
- **Decyzji projektowych.** Wybór wariantu wyglądu, zakres odstępstw od źródła i ocena, co jest błędem importu, a co scrapera, pozostały po naszej stronie.

Podsumowując: AI skróciło czas pisania kodu i dokumentacji, ale nie zastąpiło zrozumienia systemu. Odpowiedzialność za poprawność została przy osobie, która zmianę zgłaszała i recenzowała.
