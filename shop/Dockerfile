FROM prestashop/prestashop:8.2.8

# Motyw potomny trafia poza /var/www/html, bo /var/www/html jest wolumenem (deploy/compose.yaml) - plik z obrazu
# w wolumenie zmieniłby się tylko przy pustym wolumenie. Do themes/ kopiuje go przy każdym starcie 00-sync-theme.sh.
# Właściciel www-data <-- Apache z PrestaShop działa jako www-data
COPY --chown=www-data:www-data themes/custom-child-theme /usr/local/share/shop-theme/custom-child-theme
# Moduł Omnibus - z tego samego powodu poza wolumenem, kopiuje go 00-sync-theme.sh
COPY --chown=www-data:www-data modules/omnibusprice /usr/local/share/shop-modules/omnibusprice
# Skrypty uruchamiane przez docker_run.sh przy każdym starcie kontenera (po instalacji, przed startem Apache)
COPY --chmod=755 init-scripts/ /tmp/init-scripts/
# Skrypty PHP wywoływane przez init-scripts; poza /tmp/init-scripts/, bo docker_run.sh uruchamia każdy plik z tamtego katalogu
COPY --chmod=755 scripts/ /usr/local/share/shop-init/
