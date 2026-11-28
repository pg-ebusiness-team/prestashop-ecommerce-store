#!/bin/sh

# Kopiuje motyw potomny i moduł omnibusprice z obrazu (/usr/local/share) do wolumenu /var/www/html przy kazdym starcie.
# Bez tego zmiany w repo nie trafilyby do sklepu: wolumen zachowuje pliki z pierwszego uruchomienia.
# Katalog jest podmieniany w calosci, wiec pliki usuniete z repo znikaja tez ze sklepu.

sync_dir() {
    SRC=$1
    DST=$2
    if [ ! -d "$SRC" ]; then
        echo "00-sync-theme: BLAD: brak katalogu w obrazie ($SRC)"
        exit 1
    fi
    # Kopia obok i zamiana nazw, zeby Apache nie trafil na polowe skopiowanego katalogu
    rm -rf "$DST.new" "$DST.old"
    cp -a "$SRC" "$DST.new"
    [ -d "$DST" ] && mv "$DST" "$DST.old"
    mv "$DST.new" "$DST"
    rm -rf "$DST.old"
    echo "00-sync-theme: $DST skopiowany z obrazu"
}

sync_dir /usr/local/share/shop-theme/custom-child-theme /var/www/html/themes/custom-child-theme
sync_dir /usr/local/share/shop-modules/omnibusprice /var/www/html/modules/omnibusprice
exit 0
