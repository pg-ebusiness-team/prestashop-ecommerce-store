FROM prestashop/prestashop:8.2.8

#kopiuje plik motywo z repo do obrazu, ustawia właściciela na www-data <-- Apache z Prestashop działa jako www-data
COPY --chown=www-data:www-data themes/custom-child-theme /var/www/html/themes/custom-child-theme 
