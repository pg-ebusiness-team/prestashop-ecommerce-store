FROM prestashop/prestashop:8.2.8

#kopiuje plik motywo z repo do obrazu, ustawia właściciela na www-data <-- Apache z Prestashop działa jako www-data
COPY --chown=www-data:www-data themes/custom-child-theme /var/www/html/themes/custom-child-theme
COPY --chown=www-data:www-data modules/omnibusprice /var/www/html/modules/omnibusprice
# Skrypty uruchamiane przez docker_run.sh przy każdym starcie kontenera (po instalacji, przed startem Apache)
COPY --chmod=755 init-scripts/ /tmp/init-scripts/
# Skrypty PHP wywoływane przez init-scripts; poza /tmp/init-scripts/, bo docker_run.sh uruchamia każdy plik z tamtego katalogu
COPY --chmod=755 scripts/ /usr/local/share/shop-init/
