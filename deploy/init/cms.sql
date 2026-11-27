-- Treści stron CMS (FRONT-4), uruchamiane przez `make theme`.
-- Idempotentny: nadpisuje treść stron 1-5 z instalatora po polsku i tworzy stronę 6 - źródłem prawdy jest repo, nie panel.
-- Treść HTML stron leży w shop/cms/<id>-<nazwa>.html; make theme podaje ją jako @cms_<id> (base64, bez escapowania).
-- Tytuły i adresy zostają z instalatora (stopka ps_linklist linkuje po ID, PS_CONDITIONS_CMS_ID = 3 to regulamin w zamówieniu).
-- Dane firmy są fikcyjne (jak w theme.sql), żeby sklep testowy nie kierował klientów do istniejącej firmy.
SET NAMES utf8mb4; -- bez tego polskie znaki zapisałyby się błędnie

START TRANSACTION;

SET @pl = (SELECT id_lang FROM ps_lang WHERE iso_code = 'pl');

-- Sklep tylko po polsku (WYMAGANIA.md). Instalator zostawia aktywny angielski, a pod /en/ są teksty z instalatora
-- (zakazane w FRONT-4), do których prowadzi hreflang i przekierowanie przeglądarek z Accept-Language: en.
-- Przy jednym aktywnym języku PrestaShop usuwa prefiks /pl/ z adresów - linki w theme.sql są więc bez /pl/.
UPDATE ps_lang SET active = 0 WHERE iso_code <> 'pl';

-- 1. Dostawa
-- Nazwy, ceny i czas dostawy muszą zgadzać się z CARRIERS w shop/scripts/configure-sales.php.
UPDATE ps_cms_lang SET
  meta_keywords = 'dostawa, wysyłka, kurier, koszt dostawy, darmowa dostawa',
  meta_description = 'Koszty i czas dostawy alkoholi premium, darmowa wysyłka od 2000 zł, bezpieczne pakowanie butelek.',
  content = CONVERT(@cms_1 USING utf8mb4)
WHERE id_cms = 1 AND id_lang = @pl;

-- 2. Polityka prywatności
UPDATE ps_cms_lang SET
  meta_keywords = 'polityka prywatności, RODO, dane osobowe, cookies',
  meta_description = 'Jak sklep Luksusowe Alkohole przetwarza dane osobowe klientów i jakich plików cookies używa.',
  content = CONVERT(@cms_2 USING utf8mb4)
WHERE id_cms = 2 AND id_lang = @pl;

-- 3. Regulamin (podpięty pod zgodę w zamówieniu)
UPDATE ps_cms_lang SET
  meta_keywords = 'regulamin, zwrot, odstąpienie od umowy, reklamacja',
  meta_description = 'Regulamin sklepu internetowego Luksusowe Alkohole: zamówienia, płatności, dostawa, odstąpienie od umowy i reklamacje.',
  content = CONVERT(@cms_3 USING utf8mb4)
WHERE id_cms = 3 AND id_lang = @pl;

-- 4. O nas (O sklepie)
UPDATE ps_cms_lang SET
  meta_keywords = 'o nas, alkohole premium, whisky, koniak, kosze prezentowe',
  meta_description = 'Luksusowe Alkohole - starannie wybrane whisky, koniaki, wina i szampany oraz kosze prezentowe na każdą okazję.',
  content = CONVERT(@cms_4 USING utf8mb4)
WHERE id_cms = 4 AND id_lang = @pl;

-- 5. Płatności (Formy płatności)
-- Metody płatności muszą zgadzać się z PAYMENT_MODULES_ENABLED w shop/scripts/configure-sales.php.
UPDATE ps_cms_lang SET
  meta_keywords = 'płatności, przelew, pobranie, płatność przy odbiorze',
  meta_description = 'Formy płatności w sklepie Luksusowe Alkohole: przelew tradycyjny i płatność przy odbiorze.',
  content = CONVERT(@cms_5 USING utf8mb4)
WHERE id_cms = 5 AND id_lang = @pl;

-- 6. Oferta dla firm (menu główne i link w nagłówku). Instalator jej nie tworzy, więc INSERT zamiast UPDATE.
-- E-mail w treści fikcyjny, jak PS_SHOP_EMAIL w theme.sql.
INSERT INTO ps_cms (id_cms, id_cms_category, position, active, indexation) VALUES (6, 1, 5, 1, 0)
ON DUPLICATE KEY UPDATE active = 1;
INSERT IGNORE INTO ps_cms_shop (id_cms, id_shop) VALUES (6, 1);
INSERT INTO ps_cms_lang (id_cms, id_lang, id_shop, meta_title, meta_description, meta_keywords, content, link_rewrite)
VALUES (6, @pl, 1, 'Oferta dla firm',
  'Alkohole premium i zestawy prezentowe dla firm: upominki biznesowe z logo lub dedykacją.',
  'oferta dla firm, prezenty firmowe, upominki biznesowe, alkohol z logo',
  CONVERT(@cms_6 USING utf8mb4), 'oferta-dla-firm')
ON DUPLICATE KEY UPDATE meta_title = VALUES(meta_title), meta_description = VALUES(meta_description),
  meta_keywords = VALUES(meta_keywords), content = VALUES(content), link_rewrite = VALUES(link_rewrite);

COMMIT;
