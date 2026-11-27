#!/bin/sh

# Kopiuje motyw potomny z obrazu (/usr/local/share/shop-theme) do wolumenu /var/www/html przy kazdym starcie.
# Bez tego zmiany motywu w repo nie trafilyby do sklepu: wolumen zachowuje pliki z pierwszego uruchomienia.
# Katalog jest podmieniany w calosci, wiec pliki usuniete z repo znikaja tez ze sklepu.

SRC=/usr/local/share/shop-theme/custom-child-theme
DST=/var/www/html/themes/custom-child-theme

if [ ! -d "$SRC" ]; then
    echo "00-sync-theme: BLAD: brak motywu w obrazie ($SRC)"
    exit 1
fi

# Kopia obok i zamiana nazw, zeby Apache nie trafil na polowe skopiowanego motywu
rm -rf "$DST.new" "$DST.old"
cp -a "$SRC" "$DST.new"
[ -d "$DST" ] && mv "$DST" "$DST.old"
mv "$DST.new" "$DST"
rm -rf "$DST.old"

echo "00-sync-theme: motyw custom-child-theme skopiowany z obrazu"
exit 0
