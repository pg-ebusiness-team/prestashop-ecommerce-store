FROM prestashop/prestashop:8.2.8

#kopiuje plik motywo z repo do obrazu, ustawia właściciela na www-data <-- Apache z Prestashop działa jako www-data
COPY --chown=www-data:www-data themes/custom-child-theme /var/www/html/themes/custom-child-theme 
# Skrypty uruchamiane przez docker_run.sh przy każdym starcie kontenera (po instalacji, przed startem Apache)
COPY --chmod=755 init-scripts/ /tmp/init-scripts/
