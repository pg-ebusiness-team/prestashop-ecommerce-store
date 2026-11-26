
-- SKLEP-28: Walidacja stanów magazynowych PrestaShop 8
-- Kontekst sklepu: id_shop = 1, id_shop_group = 0

-- 1. Walidacja zakresu stanów magazynowych 0–10.

SELECT
    COUNT(*) AS stock_records,
    COALESCE(SUM(quantity < 0 OR quantity > 10), 0)
        AS invalid_records,
    COALESCE(MIN(quantity), 0) AS min_quantity,
    COALESCE(MAX(quantity), 0) AS max_quantity,
    CASE
        WHEN COALESCE(SUM(quantity < 0 OR quantity > 10), 0) = 0
        THEN 'OK'
        ELSE 'BLAD'
    END AS validation_result
FROM ps_stock_available
WHERE id_shop = 1
  AND id_shop_group = 0;


-- 2. Walidacja udziału produktów całkowicie niedostępnych.
-- Produkty z wariantami: suma stanów wszystkich wariantów.
-- Produkty bez wariantów: stan rekordu bazowego.

WITH product_stock AS (
    SELECT
        p.id_product,
        COALESCE(
            SUM(
                CASE
                    WHEN sa.id_product_attribute > 0
                        THEN sa.quantity
                    WHEN sa.id_product_attribute = 0
                        AND NOT EXISTS (
                            SELECT 1
                            FROM ps_stock_available variants
                            WHERE variants.id_product = p.id_product
                              AND variants.id_shop = 1
                              AND variants.id_shop_group = 0
                              AND variants.id_product_attribute > 0
                        )
                        THEN sa.quantity
                    ELSE 0
                END
            ),
            0
        ) AS total_quantity
    FROM ps_product_shop p
    LEFT JOIN ps_stock_available sa
        ON sa.id_product = p.id_product
       AND sa.id_shop = 1
       AND sa.id_shop_group = 0
    WHERE p.id_shop = 1
    GROUP BY p.id_product
),
summary AS (
    SELECT
        COUNT(*) AS total_products,
        SUM(CASE WHEN total_quantity = 0 THEN 1 ELSE 0 END)
            AS unavailable_products
    FROM product_stock
)
SELECT
    total_products,
    unavailable_products,
    ROUND(
        100.0 * unavailable_products / NULLIF(total_products, 0),
        2
    ) AS unavailable_percentage,
    CASE
        WHEN total_products > 0
         AND 100.0 * unavailable_products / total_products BETWEEN 5 AND 20
        THEN 'OK'
        ELSE 'BLAD'
    END AS validation_result
FROM summary;
