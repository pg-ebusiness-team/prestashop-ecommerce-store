-- Opisy kategorii jak w sklepie źródłowym, uruchamiane przez `make categories` PO imporcie (kategorie zakłada importer).
-- Idempotentny: nadpisuje opisy kategorii z listy niżej - źródłem prawdy jest repo, nie panel.
-- Treść leży w shop/categories/<plik>.html; make categories podaje ją jako @`cat_<plik>` (base64, bez escapowania).
-- Znacznik <!-- więcej --> dzieli treść: część przed nim to opis pod tytułem (description), część po nim
-- jest zwinięta pod przyciskiem „Pokaż więcej” (additional_description, motyw: category-header.tpl).
-- Kategorie dopasowujemy po nazwie, bo ID nadaje importer. Scraper ucina część nazw („Zestawy alkoholi na...”),
-- więc ucięta nazwa pasuje, jeśli pełna zaczyna się od niej (jak sameName() w facets.php).
SET NAMES utf8mb4; -- bez tego polskie znaki zapisałyby się błędnie

SET @pl = (SELECT id_lang FROM ps_lang WHERE iso_code = 'pl');
SET @more = '<!-- więcej -->';

-- Pełna nazwa kategorii -> treść pliku. Kolejność jak w menu. Bez opisu w źródle (więc tu ich nie ma): Zestawy
-- prezentowe na Wielkanoc, Kosze prezentowe na Wielkanoc, Alkohole na Wielkanoc, podkategorie Alkohole & likiery
-- poza Gin, Likier, Rum i Tequila & Mezcal, Wino bezalkoholowe oraz cały dział Opakowania & Słodycze.
-- Teksty przepisane ze źródła bez stylów inline i bez linków (prowadziły do sklepu źródłowego).
CREATE TEMPORARY TABLE category_text (name VARCHAR(128) NOT NULL, content MEDIUMTEXT);
INSERT INTO category_text (name, content) VALUES
  ('Prezenty', @`cat_prezenty`),
  ('Kosze upominkowe', @`cat_kosze-upominkowe`),
  ('Zestawy upominkowe', @`cat_zestawy-upominkowe`),
  ('Zestawy alkoholi na prezent', @`cat_zestawy-alkoholi-na-prezent`),
  ('Ozdobne butelki', @`cat_ozdobne-butelki`),
  ('Karty podarunkowe', @`cat_karty-podarunkowe`),
  ('Prezenty świąteczne dla klientów', @`cat_prezenty-swiateczne-dla-klientow`),
  ('Upominki świąteczne dla pracowników', @`cat_upominki-swiateczne-dla-pracownikow`),
  ('Whisky & Bourbon', @`cat_whisky-bourbon`),
  ('Whisky', @`cat_whisky`),
  ('Bourbon', @`cat_bourbon`),
  ('Alkohole & likiery', @`cat_alkohole-likiery`),
  ('Gin', @`cat_gin`),
  ('Likier', @`cat_likier`),
  ('Rum', @`cat_rum`),
  ('Tequila & Mezcal', @`cat_tequila-mezcal`),
  ('Wino & Champagne', @`cat_wino-champagne`),
  ('Wino', @`cat_wino`),
  ('Champagne', @`cat_champagne`);

START TRANSACTION;

UPDATE ps_category_lang cl
JOIN category_text t
  ON cl.name = t.name
  OR (cl.name LIKE '%...' AND t.name LIKE CONCAT(RTRIM(LEFT(cl.name, CHAR_LENGTH(cl.name) - 3)), '%'))
SET
  cl.description = TRIM(BOTH '\n' FROM SUBSTRING_INDEX(t.content, @more, 1)),
  cl.additional_description = IF(LOCATE(@more, t.content) > 0,
                                 TRIM(BOTH '\n' FROM SUBSTRING(t.content, LOCATE(@more, t.content) + CHAR_LENGTH(@more))),
                                 '')
WHERE cl.id_lang = @pl AND t.content IS NOT NULL;

COMMIT;

-- Raport braków: pusta treść = brak pliku w shop/categories/, brak dopasowania = nie ma takiej kategorii
-- (czy import się wykonał?). Bez braków zapytanie nic nie wypisuje.
SELECT CONCAT('categories: BLAD: ',
              IF(t.content IS NULL, 'brak pliku z opisem dla „', 'nie ma kategorii „'), t.name, '”') AS ''
FROM category_text t
WHERE t.content IS NULL
   OR NOT EXISTS (
     SELECT 1 FROM ps_category_lang cl
     WHERE cl.id_lang = @pl
       AND (cl.name = t.name
            OR (cl.name LIKE '%...' AND t.name LIKE CONCAT(RTRIM(LEFT(cl.name, CHAR_LENGTH(cl.name) - 3)), '%')))
   );
