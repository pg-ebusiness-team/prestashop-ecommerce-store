#!/bin/sh
# Zdjęcia produktów do scraper_results/product_photos/ (WYMAGANIA.md: „Skrypt inicjalizacji pobiera archiwum
# z Releases, a gdy jest niedostępne — ponownie pobiera zdjęcia z URL-i z wyników scrapowania”).
# Uruchamiany w kontenerze tools z katalogu repo (/app): make photos / make init.
#
# 1. Archiwum z Releases (URL w $1), o ile nie zostało już rozpakowane - znacznik .release z URL-em.
# 2. Scraper (--photos-only) dociąga z URL-i ze scraper_results/products tylko brakujące zdjęcia:
#    po udanym archiwum to pojedyncze pliki, bez archiwum - cały zbiór (ok. 2900 zdjęć, ≤2 zapytania/s, ok. 25 min).
set -eu

URL="${1:?Podaj URL archiwum zdjęć (PHOTOS_RELEASE_URL)}"
RESULTS=scraper_results
DIR="$RESULTS/product_photos"
MARKER="$DIR/.release"

count_photos() {
    find "$DIR" -type f \( -name '*.webp' -o -name '*.jpg' -o -name '*.png' \) 2>/dev/null | wc -l
}

release_ok=0
if [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "$URL" ]; then
    echo "photos: archiwum z Releases już rozpakowane ($(count_photos) zdjęć), pomijam pobieranie"
    release_ok=1
else
    tmp=$(mktemp -d)
    echo "photos: pobieram archiwum $URL"
    if curl -fL --retry 3 --connect-timeout 15 -o "$tmp/photos.zip" "$URL" \
        && unzip -tq "$tmp/photos.zip" >/dev/null; then
        # Archiwum musi zawierać wyłącznie katalog product_photos/ - inaczej mogłoby nadpisać inne pliki repo
        if unzip -Z1 "$tmp/photos.zip" | grep -qv '^product_photos/'; then
            echo "photos: BLAD: archiwum zawiera pliki spoza product_photos/, odrzucam je - pobieram zdjęcia z URL-i"
        else
            unzip -oq "$tmp/photos.zip" -d "$RESULTS"
            echo "$URL" > "$MARKER"
            release_ok=1
            echo "photos: rozpakowano archiwum ($(count_photos) zdjęć)"
        fi
    else
        echo "photos: archiwum niedostępne lub uszkodzone - pobieram zdjęcia z URL-i ze sklepu źródłowego"
    fi
    rm -rf "$tmp"
fi

echo "photos: uzupełniam brakujące zdjęcia z URL-i (scraper --photos-only)"
if python scraper/main.py --photos-only; then
    echo "photos: gotowe ($(count_photos) zdjęć)"
elif [ "$release_ok" = 1 ]; then
    # Sklep źródłowy niedostępny, ale zdjęcia z archiwum są - import może iść dalej
    echo "photos: UWAGA: nie udało się uzupełnić zdjęć z URL-i, zostaje $(count_photos) zdjęć z archiwum"
else
    echo "photos: BLAD: brak archiwum i nie udało się pobrać zdjęć z URL-i"
    exit 1
fi
