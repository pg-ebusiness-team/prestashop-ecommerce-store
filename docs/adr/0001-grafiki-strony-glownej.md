# ADR 0001: Grafiki strony głównej pobierane ze sklepu źródłowego przy inicjalizacji

- Status: zaakceptowany
- Data: 2026-11-03
- Zadanie: FRONT-2 (Wariant A wyglądu)

## Kontekst

Strona główna (slider, 4 kafelki kategorii, 2 banery, logo w nagłówku i stopce) ma wyglądać jak w luksusowealkohole.pl.
Prowadzący zdecydował, że grafiki i teksty tych elementów mają być **identyczne jak w źródle**.

Ograniczenia:

- grafiki należą do sklepu źródłowego (i częściowo do marek, np. Balvenie, Ardbeg);
- `WYMAGANIA.md` zabrania trzymania zdjęć produktów w repozytorium - pobiera je skrypt inicjalizacji;
- w etapie 2 obraz sklepu trafia do GHCR jako **publiczny**, więc wszystko, co jest w motywie, zostaje rozpowszechnione;
- konfiguracja modułów (slider, blok tekstowy) jest w bazie i musi dać się odtworzyć po `make reset`.

## Rozważane opcje

1. **Grafiki w motywie potomnym (w repo).** Najprostsze, ale cudze grafiki trafiłyby do repo i do publicznego obrazu.
2. **Własne zdjęcia z Pexels/Unsplash w motywie.** Zgodne z licencją, ale niezgodne z decyzją prowadzącego (grafiki identyczne ze źródłem).
3. **W repo tylko lista URL-i, pliki pobierane przy inicjalizacji** - tak jak zdjęcia produktów.

## Decyzja

Opcja 3.

- `deploy/init/home-images.txt` - lista `nazwa-pliku URL` (14 grafik `.webp`, logo `.jpg` i logo stopki `.png`).
- `make theme` pobiera je w kontenerze do `img/cms/home/` (katalog PrestaShop na grafiki treści), potem wgrywa
  `deploy/init/theme.sql`, który wskazuje na te pliki w sliderze i bloku `ps_customtext`.
- Pobieranie przy każdym `make theme`: kontener po przebudowie (`make up`) traci pliki spoza bazy.

## Konsekwencje

- Repo i obraz Dockera nie zawierają grafik źródła.
- `make theme` wymaga dostępu do luksusowealkohole.pl. Gdy grafika jest niedostępna, `curl -f` przerywa polecenie
  z nazwą pliku, zamiast zostawić puste miejsca na stronie.
- Zmiana adresów grafik w źródle psuje inicjalizację - trzeba wtedy zaktualizować `home-images.txt`.
  Zapasowe archiwum (GitHub Releases) dodamy razem z mechanizmem dla zdjęć produktów.
- Treści slidera i bloku tekstowego ustawione w panelu są nadpisywane przez `make theme` - źródłem prawdy jest repo.
