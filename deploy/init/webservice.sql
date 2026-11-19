-- Rejestruje klucz Webservice dla skryptu importu. Wymaga: SET @ws_key = '<32 znaki A-Z0-9>';
-- Idempotentny: konto rozpoznajemy po opisie, więc zmiana klucza w .env podmienia stare konto.
SET @ws_desc = 'Import danych (BACK-1)';

START TRANSACTION; -- wszystko pomiędzy tym a COMMIT, wykonuje się albo w całości albo wcale

-- 1. Włączenie Webservice
UPDATE ps_configuration SET value = '1', date_upd = NOW() WHERE name = 'PS_WEBSERVICE';
INSERT INTO ps_configuration (name, value, date_add, date_upd)
SELECT 'PS_WEBSERVICE', '1', NOW(), NOW() FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM ps_configuration WHERE name = 'PS_WEBSERVICE');

-- 2. Usunięcie poprzedniego konta (ponowne uruchomienie = brak duplikatów)
DELETE FROM ps_webservice_permission WHERE id_webservice_account IN
  (SELECT id_webservice_account FROM ps_webservice_account WHERE description = @ws_desc);
DELETE FROM ps_webservice_account_shop WHERE id_webservice_account IN
  (SELECT id_webservice_account FROM ps_webservice_account WHERE description = @ws_desc);
DELETE FROM ps_webservice_account WHERE description = @ws_desc;

-- 3. Nowe konto i przypięcie do sklepu
INSERT INTO ps_webservice_account (`key`, description, class_name, is_module, active)
VALUES (@ws_key, @ws_desc, 'WebserviceRequest', 0, 1);
SET @ws_id = LAST_INSERT_ID();
INSERT INTO ps_webservice_account_shop (id_webservice_account, id_shop) VALUES (@ws_id, 1);

-- 4. Uprawnienia: iloczyn kartezjański zasobów i metod = 28 wierszy
INSERT INTO ps_webservice_permission (resource, method, id_webservice_account)
SELECT r.res, m.meth, @ws_id
FROM (SELECT 'categories' AS res UNION ALL SELECT 'products' UNION ALL SELECT 'combinations'
      UNION ALL SELECT 'stock_availables' UNION ALL SELECT 'images'
      UNION ALL SELECT 'product_options' UNION ALL SELECT 'product_option_values') r
CROSS JOIN (SELECT 'GET' AS meth UNION ALL SELECT 'POST' UNION ALL SELECT 'PUT' UNION ALL SELECT 'DELETE') m;

COMMIT;
