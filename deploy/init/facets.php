<?php
/**
 * Filtry na listach produktów (moduł ps_facetedsearch, lewa kolumna) jak w sklepie źródłowym.
 *
 * Uruchamiany przez `make facets` PO imporcie: kategorie, cechy i atrybuty dopasowujemy po nazwie, bo ich ID
 * nadaje importer. Idempotentny: usuwa wszystkie szablony filtrów (także szablon z instalatora z filtrami demo)
 * i zakłada je od nowa - źródłem prawdy jest repo, nie panel.
 *
 * Szablony zapisujemy w ps_layered_filter tak jak panel modułu (serialize()), a potem moduł sam rozpisuje je
 * na kategorie (buildLayeredCategories). Samo wpisanie ps_layered_category nie wystarczy: moduł odtwarza tę
 * tabelę z szablonów przy każdym dodaniu lub usunięciu kategorii, więc wpisy spoza szablonów by zniknęły.
 */

declare(strict_types=1);

// Ładuje PrestaShop jak każda strona sklepu (tak samo jak shop/scripts/configure-sales.php)
require '/var/www/html/config/config.inc.php';

const LANGUAGE_ID = 1;

// Rodzaj pola filtra - wartości jak w panelu modułu
const CHECKBOX = 0;
const RADIO = 1;
const DROPDOWN = 2;

/*
 * Grupy kategorii i ich filtry, spisane z lewej kolumny stron kategorii sklepu źródłowego.
 *
 * Filtr: ['price'] | ['categories', rodzaj] | ['manufacturer', rodzaj] | ['feature', nazwa] | ['attribute', nazwa].
 * Kolejność filtrów = kolejność w lewej kolumnie. Filtr bez wartości w danej kategorii moduł ukrywa, tak jak
 * źródło - dlatego wystarczy jedna lista na grupę (np. Absynt nie ma producentów, więc nie widać filtra Producent).
 * Karty podarunkowe celowo nie mają filtrów (w źródle też ich nie ma).
 */
const TEMPLATES = [
    [
        'name' => 'Działy: Prezenty, Opakowania & Słodycze',
        'categories' => ['Prezenty', 'Opakowania & Słodycze'],
        'filters' => [['price'], ['categories', RADIO]],
    ],
    [
        'name' => 'Whisky & Bourbon',
        'categories' => ['Whisky & Bourbon', 'Whisky', 'Bourbon'],
        'filters' => [
            ['price'], ['manufacturer', CHECKBOX], ['feature', 'Kraj'], ['feature', 'Rodzaj'], ['feature', 'Wiek'],
            ['feature', 'Region'], ['attribute', 'Pojemność'],
        ],
    ],
    [
        'name' => 'Alkohole & likiery',
        'categories' => [
            'Alkohole & likiery', 'Absynt', 'Aperitif', 'Armaniak', 'Brandy', 'Calvados', 'Gin', 'Grappa', 'Koniak',
            'Likier', 'Miód pitny', 'Nalewki', 'Rum', 'Sake', 'Wódka', 'Tequila & Mezcal',
        ],
        'filters' => [
            ['price'], ['feature', 'Kraj'], ['attribute', 'Pojemność'], ['manufacturer', DROPDOWN], ['feature', 'Wiek'],
            ['feature', 'Kolor'], ['feature', 'Rodzaj'],
        ],
    ],
    [
        'name' => 'Wino & Champagne',
        'categories' => ['Wino & Champagne', 'Wino', 'Wino bezalkoholowe', 'Champagne'],
        'filters' => [
            ['price'], ['feature', 'Kraj'], ['feature', 'Kolor'], ['feature', 'Rodzaj'], ['feature', 'Szczep'],
            ['feature', 'Region'], ['feature', 'Charakter'],
        ],
    ],
    [
        'name' => 'Okazje',
        'categories' => [
            'Kosze upominkowe', 'Prezenty świąteczne dla klientów', 'Upominki świąteczne dla pracowników',
            'Zestawy prezentowe na Wielkanoc', 'Kosze prezentowe na Wielkanoc', 'Alkohole na Wielkanoc',
        ],
        'filters' => [
            ['categories', CHECKBOX], ['price'], ['manufacturer', DROPDOWN], ['feature', 'Rodzaj'],
            ['attribute', 'Pojemność'], ['feature', 'Region'], ['feature', 'Kolor'], ['feature', 'Wiek'],
        ],
    ],
    [
        'name' => 'Tylko cena',
        'categories' => [
            'Zestawy upominkowe', 'Zestawy alkoholi na prezent', 'Ozdobne butelki', 'Opakowania & Akcesoria', 'Słodycze',
            'Kawa', 'Herbata',
        ],
        'filters' => [['price']],
    ],
    [
        // Strony spoza kategorii z lewą kolumną (theme.yml) - w źródle Nowości i Promocje mają Cenę i Kategorie
        'name' => 'Nowości, promocje, bestsellery, producenci',
        'controllers' => ['new-products', 'prices-drop', 'best-sales', 'manufacturer', 'supplier'],
        'filters' => [['price'], ['categories', RADIO]],
    ],
];

$problems = 0;

function problem(string $message): void
{
    global $problems;
    ++$problems;
    fwrite(STDERR, "facets: BLAD: $message\n");
}

/**
 * Czy nazwa w sklepie odpowiada nazwie z listy. Scraper ucina część nazw („Zestawy alkoholi na...”), więc ucięta
 * pasuje, jeśli pełna nazwa zaczyna się od niej - skrypt zadziała też po poprawieniu nazw w scraperze.
 */
function sameName(string $inShop, string $wanted): bool
{
    if ($inShop === $wanted) {
        return true;
    }

    return str_ends_with($inShop, '...') && str_starts_with($wanted, rtrim(substr($inShop, 0, -3)));
}

/** @return int[] */
function categoryIds(array $wantedNames, array $shopCategories): array
{
    $ids = [];

    foreach ($wantedNames as $wanted) {
        $found = array_keys(array_filter($shopCategories, fn ($name) => sameName($name, $wanted)));

        if (!$found) {
            problem("nie ma kategorii „{$wanted}” (czy import się wykonał?)");
        }

        array_push($ids, ...$found);
    }

    return $ids;
}

/** Klucz filtra w szablonie, w formacie panelu modułu (np. layered_selection_feat_3). */
function filterKey(array $filter, array $features, array $attributeGroups): ?string
{
    switch ($filter[0]) {
        case 'price':
            return 'layered_selection_price_slider';
        case 'categories':
            return 'layered_selection_subcategories';
        case 'manufacturer':
            return 'layered_selection_manufacturer';
        case 'feature':
            $id = $features[$filter[1]] ?? null;
            if ($id === null) {
                problem("nie ma cechy „{$filter[1]}” (import cech: scraper/importer/features.py)");
            }

            return $id === null ? null : "layered_selection_feat_$id";
        case 'attribute':
            $id = $attributeGroups[$filter[1]] ?? null;
            if ($id === null) {
                problem("nie ma grupy atrybutów „{$filter[1]}”");
            }

            return $id === null ? null : "layered_selection_ag_$id";
    }

    throw new LogicException("Nieznany filtr {$filter[0]}");
}

$module = Module::getInstanceByName('ps_facetedsearch');
if (!$module || !Module::isEnabled('ps_facetedsearch')) {
    fwrite(STDERR, "facets: BLAD: moduł ps_facetedsearch nie jest zainstalowany i włączony\n");
    exit(1);
}

$db = Db::getInstance();
$shopId = (int) Context::getContext()->shop->id;

// Nazwa -> ID; przy powtórzonej nazwie cechy/atrybutu bierzemy pierwszy (jak importer cech)
$shopCategories = array_column(
    $db->executeS('SELECT id_category, name FROM ' . _DB_PREFIX_ . 'category_lang WHERE id_lang = ' . LANGUAGE_ID . ' AND id_shop = ' . $shopId),
    'name',
    'id_category'
);
$features = [];
foreach (Feature::getFeatures(LANGUAGE_ID) as $feature) {
    $features[$feature['name']] ??= (int) $feature['id_feature'];
}
$attributeGroups = [];
foreach (AttributeGroup::getAttributesGroups(LANGUAGE_ID) as $group) {
    $attributeGroups[$group['name']] ??= (int) $group['id_attribute_group'];
}

// Od nowa: bez tego zostałby szablon z instalatora (filtry demo) i szablony z poprzedniego uruchomienia
$db->execute('DELETE FROM ' . _DB_PREFIX_ . 'layered_filter_shop');
$db->execute('DELETE FROM ' . _DB_PREFIX_ . 'layered_filter');

foreach (TEMPLATES as $template) {
    $categories = categoryIds($template['categories'] ?? [], $shopCategories);

    // Ta sama struktura, którą zapisuje panel modułu (ps_facetedsearch::getContent)
    $values = [
        'shop_list' => [$shopId],
        'categories' => $categories,
        'controllers' => $template['controllers'] ?? ['category'],
    ];

    foreach ($template['filters'] as $filter) {
        $key = filterKey($filter, $features, $attributeGroups);

        if ($key !== null) {
            // Rodzaj pola podajemy tylko dla kategorii i producentów; cechy i atrybuty to zawsze pola wyboru.
            // Limit 0 = wszystkie wartości. Limit modułu ukrywa resztę na stałe, a źródło ją zwija
            // („pokaż więcej”) - to robi motyw.
            $type = in_array($filter[0], ['categories', 'manufacturer'], true) ? $filter[1] : CHECKBOX;
            $values[$key] = ['filter_type' => $type, 'filter_show_limit' => 0];
        }
    }

    $db->insert('layered_filter', [
        'name' => pSQL($template['name']),
        'filters' => pSQL(serialize($values)),
        'n_categories' => count($categories),
        'date_add' => date('Y-m-d H:i:s'),
    ]);
    $db->insert('layered_filter_shop', ['id_layered_filter' => (int) $db->Insert_ID(), 'id_shop' => $shopId]);

    echo "facets: {$template['name']}: " . count($categories) . ' kategorii, ' . (count($values) - 3) . " filtrow\n";
}

// Rozpisanie szablonów na kategorie (ps_layered_category) i wyczyszczenie zapamiętanych bloków filtrów
$module->buildLayeredCategories();

// Indeksy, z których moduł liczy wartości filtrów. Bez nich np. Pojemność i Cena pokazują stan sprzed importu.
$module->indexAttributes();
$module->fullPricesIndexProcess(0, false, false);
$module->invalidateLayeredFilterBlockCache();

echo $problems ? "facets: zakonczone z bledami ($problems)\n" : "facets: gotowe\n";
exit($problems ? 1 : 0);
