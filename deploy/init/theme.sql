-- Treści modułów strony głównej (FRONT-2), uruchamiane przez `make theme`.
-- Idempotentny: przy każdym uruchomieniu nadpisuje slider i blok ps_customtext - źródłem prawdy jest repo, nie panel.
-- Teksty i grafiki jak w sklepie źródłowym (docs/adr/0001-grafiki-strony-glownej.md).
-- Grafiki pobiera wcześniej `make theme` do img/cms/home/ (lista: deploy/init/home-images.txt).
SET NAMES utf8mb4; -- bez tego polskie znaki zapisałyby się błędnie

START TRANSACTION;

-- 1. Slider (ps_imageslider)
-- Moduł składa adres jako /modules/ps_imageslider/images/<image>, a grafiki leżą w /img/cms/home/ - stąd ../../../
SET @img = '../../../img/cms/home/';

DELETE FROM ps_homeslider_slides_lang;
DELETE FROM ps_homeslider;
DELETE FROM ps_homeslider_slides;

INSERT INTO ps_homeslider_slides (id_homeslider_slides, position, active)
VALUES (1, 1, 1), (2, 2, 1), (3, 3, 1), (4, 4, 1), (5, 5, 1), (6, 6, 1), (7, 7, 1), (8, 8, 1);
INSERT INTO ps_homeslider (id_homeslider_slides, id_shop)
VALUES (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1);

-- Linki przez wyszukiwarkę: ID kategorii i produktów zmienią się po imporcie (D2).
-- Bez prefiksu /pl/: sklep ma jeden aktywny język (cms.sql), więc PrestaShop nie dodaje go do adresów.
INSERT INTO ps_homeslider_slides_lang (id_homeslider_slides, id_lang, title, description, legend, url, image)
SELECT s.id, l.id_lang, s.title,
  CONCAT('<p class="slide-kicker">', s.kicker, '</p><p>', s.subtitle, '</p><span class="slide-btn">sprawdź naszą ofertę</span>'),
  s.legend, s.url, CONCAT(@img, 'slide-', s.id, '.webp')
FROM (
            SELECT 1 AS id, 'gwarantujemy każdemu' AS kicker, 'Luksus Wyboru' AS title,
                   'ARDBEG DOLCE Ekskluzywna Whisky Single Malt' AS subtitle, 'Ardbeg Dolce' AS legend, '/szukaj?s=ardbeg' AS url
  UNION ALL SELECT 2, 'gwarantujemy każdemu', 'Luksus Wyboru',
                   'Oferujemy ponad 5 tysięcy starannie wyselekcjonowanych produktów', 'Luksus Wyboru', '/szukaj?s=arcturus'
  UNION ALL SELECT 3, 'luksus wyboru', 'Chopin Oak Cask No 9', '9 Lat starzenia', 'Chopin Vodka 9', '/szukaj?s=chopin'
  UNION ALL SELECT 4, 'A HARRISON FORD', 'Limited Edition', 'Glenmorangie 16 YO', 'A Harrison Ford', '/szukaj?s=glenmo'
  UNION ALL SELECT 5, 'gwarantujemy każdemu', 'Luksus Wyboru', 'The Balvenie 14 YO Single Malt', 'The Balvenie 14 YO', '/szukaj?s=balvenie'
  UNION ALL SELECT 6, 'gwarantujemy każdemu', 'Luksus Wyboru',
                   'Oferujemy ponad 5 tysięcy starannie wyselekcjonowanych produktów', 'Luksus Wyboru', '/szukaj?s=chivas'
  UNION ALL SELECT 7, 'gwarantujemy każdemu', 'Luksus Wyboru', 'The Balvenie 16 YO Single Malt', 'The Balvenie 16 YO', '/szukaj?s=balvenie'
  UNION ALL SELECT 8, 'gwarantujemy każdemu', 'Luksus Wyboru', 'The Balvenie 21 YO Single Malt', 'The Balvenie 21 YO', '/szukaj?s=balvenie'
) s
CROSS JOIN ps_lang l;

-- 2. Kafelki kategorii i 2 banery (ps_customtext)
-- alt="" w kafelkach: nazwa kategorii jest tekstem w tym samym linku, czytnik nie powtórzy jej dwa razy.
UPDATE ps_info_lang SET text = '
<section class="home-categories">
  <h2 class="products-section-title">Polecamy w szczególności</h2>
  <div class="home-tiles">
    <a class="home-tile" href="/szukaj?s=whisky"><img src="/img/cms/home/tile-whisky.webp" alt="" width="540" height="540" loading="lazy"><span class="home-tile-name">Whisky &amp; Bourbon</span></a>
    <a class="home-tile" href="/szukaj?s=likier"><img src="/img/cms/home/tile-likiery.webp" alt="" width="540" height="540" loading="lazy"><span class="home-tile-name">Alkohole &amp; likiery</span></a>
    <a class="home-tile" href="/szukaj?s=wino"><img src="/img/cms/home/tile-wino.webp" alt="" width="540" height="540" loading="lazy"><span class="home-tile-name">Wino &amp; Champagne</span></a>
    <a class="home-tile" href="/szukaj?s=opakowanie"><img src="/img/cms/home/tile-opakowania.webp" alt="" width="540" height="540" loading="lazy"><span class="home-tile-name">Opakowania &amp; Słodycze</span></a>
  </div>
</section>
<section class="home-banners">
  <a class="home-banner" href="/szukaj?s=kosz">
    <img src="/img/cms/home/banner-kosze.webp" alt="" width="807" height="446" loading="lazy">
    <span class="home-banner-content">
      <span class="home-banner-title">Kosze<br>Prezentowe</span>
      <span class="home-banner-text">upominki w eleganckiej formie</span>
      <span class="home-banner-btn">zobacz produkty</span>
    </span>
  </a>
  <a class="home-banner" href="/szukaj?s=miniatur">
    <img src="/img/cms/home/banner-miniatury.webp" alt="" width="672" height="371" loading="lazy">
    <span class="home-banner-content">
      <span class="home-banner-title">Duże pojemności<br>&amp; miniaturki</span>
      <span class="home-banner-text">idealne na prezent</span>
      <span class="home-banner-btn">zobacz produkty</span>
    </span>
  </a>
</section>';

-- 3. Logo w nagłówku: PS_LOGO jest względne do img/, plik pobiera `make theme`
UPDATE ps_configuration SET value = 'cms/home/logo.jpg', date_upd = NOW() WHERE name = 'PS_LOGO';

-- 4. Liczba produktów na stronie głównej jak w źródle: po 8 w każdej zakładce „W naszej ofercie”, 4 w „Kup taniej”.
UPDATE ps_configuration SET value = '8', date_upd = NOW()
WHERE name IN ('HOME_FEATURED_NBR', 'NEW_PRODUCTS_NBR', 'PS_BLOCK_BESTSELLERS_TO_DISPLAY');
UPDATE ps_configuration SET value = '4', date_upd = NOW() WHERE name = 'BLOCKSPECIALS_SPECIALS_NBR';

-- 5. blockreassurance (produkt, koszyk): instalator zapisuje ikony jako //modules/..., co przeglądarka czyta
-- jako host „modules” -> błędy ERR_NAME_NOT_RESOLVED w konsoli.
UPDATE ps_psreassurance SET icon = REPLACE(icon, '//modules/', '/modules/') WHERE icon LIKE '//modules/%';

-- 4. telefon w pasku nagłowka ($shop.phone)
DELETE FROM ps_configuration WHERE name = 'PS_SHOP_PHONE';
INSERT INTO ps_configuration (id_shop_group, id_shop, name, value, date_add, date_upd)
VALUES (NULL, NULL, 'PS_SHOP_PHONE', '+48 123 456 789', NOW(), NOW());

-- 6. Stopka jak w źródle (templates/_partials/footer.tpl)
-- Bloki linków ps_linklist: polskie nazwy, w „Nasza firma” bez „Sklepy” (w źródle ich nie ma).
-- Linki do kategorii z kolumny „Produkty” w źródle dodamy po imporcie kategorii (D2).
UPDATE ps_link_block_lang SET name = 'Produkty' WHERE id_link_block = 1 AND id_lang = (SELECT id_lang FROM ps_lang WHERE iso_code = 'pl');
UPDATE ps_link_block_lang SET name = 'Nasza firma' WHERE id_link_block = 2 AND id_lang = (SELECT id_lang FROM ps_lang WHERE iso_code = 'pl');
UPDATE ps_link_block
SET content = '{"cms":["1","2","3","4","5"],"product":[false],"static":["contact","sitemap"],"category":[false]}'
WHERE id_link_block = 2;
-- Strony CMS z danych demo: polskie tytuły jak w źródle. Treść zostaje demo - podmienią ją strony prawne (osobne zadanie).
UPDATE ps_cms_lang c JOIN ps_lang l ON l.id_lang = c.id_lang AND l.iso_code = 'pl'
JOIN (
            SELECT 1 AS id_cms, 'Dostawa' AS title, 'dostawa' AS rewrite
  UNION ALL SELECT 2, 'Polityka prywatności', 'polityka-prywatnosci'
  UNION ALL SELECT 3, 'Regulamin', 'regulamin'
  UNION ALL SELECT 4, 'O nas', 'o-nas'
  UNION ALL SELECT 5, 'Płatności', 'platnosci'
) t ON t.id_cms = c.id_cms
SET c.meta_title = t.title, c.head_seo_title = t.title, c.link_rewrite = t.rewrite;
-- ps_socialfollow: profile sklepu źródłowego (ikony w dolnym pasku stopki)
UPDATE ps_configuration SET value = 'https://www.facebook.com/profile.php?id=61563778851821', date_upd = NOW() WHERE name = 'BLOCKSOCIAL_FACEBOOK';
UPDATE ps_configuration SET value = 'https://www.instagram.com/salonwin.pl/', date_upd = NOW() WHERE name = 'BLOCKSOCIAL_INSTAGRAM';

-- 7. Przykładowe dane kontaktowe sklepu (stopka, copyright, nadawca maili). Celowo fikcyjne, a nie dane
-- sklepu źródłowego, żeby sklep testowy nie kierował klientów do istniejącej firmy. Telefon ustawia sekcja wyżej.
DELETE FROM ps_configuration
WHERE name IN ('PS_SHOP_NAME', 'PS_SHOP_EMAIL', 'PS_SHOP_ADDR1', 'PS_SHOP_CODE', 'PS_SHOP_CITY', 'PS_SHOP_COUNTRY_ID', 'PS_SHOP_FAX');
INSERT INTO ps_configuration (id_shop_group, id_shop, name, value, date_add, date_upd)
SELECT NULL, NULL, t.name, t.value, NOW(), NOW()
FROM (
            SELECT 'PS_SHOP_NAME' AS name, 'Luksusowe Alkohole' AS value
  UNION ALL SELECT 'PS_SHOP_EMAIL', 'sklep@example.com'
  UNION ALL SELECT 'PS_SHOP_ADDR1', 'ul. Przykładowa 1'
  UNION ALL SELECT 'PS_SHOP_CODE', '00-001'
  UNION ALL SELECT 'PS_SHOP_CITY', 'Warszawa'
  UNION ALL SELECT 'PS_SHOP_COUNTRY_ID', (SELECT CAST(id_country AS CHAR) FROM ps_country WHERE iso_code = 'PL')
  UNION ALL SELECT 'PS_SHOP_FAX', '22 000 00 00'
) t;

-- 8. „Podobne produkty” na stronie produktu: 4 jak w źródle (domyślnie 16)
UPDATE ps_configuration SET value = '4', date_upd = NOW() WHERE name = 'CATEGORYPRODUCTS_DISPLAY_PRODUCTS';

COMMIT;
