<?php
/**
 * Konfiguracja sprzedaży sklepu: metody płatności, przewoźnicy i ograniczenia dostawy (W3 z docs/WYMAGANIA.md).
 *
 * Uruchamiany przy każdym starcie kontenera przez shop/init-scripts/20-configure-sales.sh (jako www-data).
 * Idempotentny: zmienia tylko to, co odbiega od stanu opisanego tutaj - źródłem prawdy jest repo, nie panel
 * (decyzja: docs/adr/0003-konfiguracja-sprzedazy.md).
 *
 * Używa klas PrestaShop (Module, Configuration, OrderState) zamiast surowego SQL, bo np. instalacja modułu
 * rejestruje hooki i restrykcje płatności, a ObjectModel czyści cache przy zapisie.
 */

declare(strict_types=1);

// Ładuje PrestaShop jak każda strona sklepu. W CLI Shop::initialize() wybiera sklep domyślny (PS_SHOP_DEFAULT).
require '/var/www/html/config/config.inc.php';

const LOG_PREFIX = '20-configure-sales';

// --- Płatności ---------------------------------------------------------------------------------------------

// Metody stosowane w Polsce, bez integracji z operatorami płatności (WYMAGANIA.md, W3).
const PAYMENT_MODULES_ENABLED = [
    'ps_wirepayment',    // przelew tradycyjny
    'ps_cashondelivery', // płatność przy odbiorze (za pobraniem)
];

// Instalator PrestaShop instaluje wszystkie moduły z dysku, w tym płatność czekiem - w Polsce niestosowaną.
const PAYMENT_MODULES_REMOVED = [
    'ps_checkpayment',
];

// Dane do przelewu pokazywane po złożeniu zamówienia i w e-mailu. Fikcyjne, jak dane firmy w deploy/init/cms.sql
// (numer konta celowo nieprawidłowy, żeby nikt nie wysłał na niego pieniędzy).
const BANK_WIRE = [
    'BANK_WIRE_OWNER' => 'Luksusowe Alkohole',
    'BANK_WIRE_DETAILS' => "PL00 1234 5678 0000 0000 0000 0000\nBank Przykładowy S.A.",
    'BANK_WIRE_ADDRESS' => "ul. Przykładowa 1\n00-001 Warszawa",
    // Po tylu dniach anulujemy nieopłacone zamówienie (tak jak na stronie CMS „Płatności”).
    'BANK_WIRE_RESERVATION_DAYS' => 7,
];

function info(string $message): void
{
    echo LOG_PREFIX . ': ' . $message . PHP_EOL;
}

function fail(string $message): never
{
    throw new RuntimeException($message);
}

function loadModule(string $name): Module
{
    $module = Module::getInstanceByName($name);
    if (!$module instanceof Module) {
        fail("brak modulu $name w katalogu modules/");
    }

    return $module;
}

function ensureModuleEnabled(string $name): void
{
    $module = loadModule($name);

    if (!Module::isInstalled($name)) {
        $module->install() || fail("nie udalo sie zainstalowac $name");
        info("zainstalowano $name");
    } elseif (!Module::isEnabled($name)) {
        $module->enable() || fail("nie udalo sie wlaczyc $name");
        info("wlaczono $name");
    }
}

function ensureModuleUninstalled(string $name): void
{
    if (!Module::isInstalled($name)) {
        return;
    }

    // PaymentModule::uninstall() usuwa też restrykcje modułu (kraje, waluty, przewoźnicy).
    loadModule($name)->uninstall() || fail("nie udalo sie odinstalowac $name");
    info("odinstalowano $name");
}

function payments(): void
{
    foreach (PAYMENT_MODULES_ENABLED as $name) {
        ensureModuleEnabled($name);
    }
    foreach (PAYMENT_MODULES_REMOVED as $name) {
        ensureModuleUninstalled($name);
    }

    foreach (BANK_WIRE as $key => $value) {
        Configuration::updateValue($key, $value);
    }

    // Faktura przy płatności przy odbiorze (krok 10 testów E2E).
    // Klient widzi link do faktury tylko wtedy, gdy BIEŻĄCY stan zamówienia ma flagę invoice
    // (OrderState::invoiceAvailable). Zamówienie za pobraniem zaczyna w stanie „Oczekiwanie na płatność przy
    // odbiorze”, który po instalacji ma invoice = 0. Z flagą = 1 PrestaShop nadaje numer faktury już przy
    // złożeniu zamówienia (OrderHistory::changeIdOrderState).
    Configuration::updateValue('PS_INVOICE', 1);
    $codState = new OrderState((int) Configuration::get('PS_OS_COD_VALIDATION'));
    if (!Validate::isLoadedObject($codState)) {
        fail('brak stanu zamowienia PS_OS_COD_VALIDATION');
    }
    if (!$codState->invoice) {
        $codState->invoice = true;
        $codState->update() || fail('nie udalo sie wlaczyc faktury dla stanu PS_OS_COD_VALIDATION');
        info('wlaczono fakture dla stanu „Oczekiwanie na platnosc przy odbiorze”');
    }

    info('platnosci: ' . implode(', ', PAYMENT_MODULES_ENABLED));
}

// --- Przewoźnicy -------------------------------------------------------------------------------------------

// Dwóch nowych przewoźników o różnych opłatach (WYMAGANIA.md, W3). Opisy zgodne ze stroną CMS „Dostawa”.
// Klucz tablicy to nazwa wpisu w ps_configuration (SALES_CARRIER_REF_<klucz>), pod którym zapamiętujemy
// id_reference przewoźnika. Po edycji w panelu PrestaShop tworzy nowy rekord z nowym id_carrier, ale tym samym
// id_reference - dlatego po nim szukamy przewoźnika przy kolejnych startach.
const CARRIERS = [
    'STANDARD' => [
        'name' => 'Przesyłka kurierska',
        'delay' => 'Doręczenie w 1-2 dni robocze',
        'price_gross' => 19.99,
        'grade' => 3, // szybkość dostawy w skali 0-9, PrestaShop pokazuje ją tylko w panelu
    ],
    'EXPRESS' => [
        'name' => 'Przesyłka kurierska ekspresowa',
        'delay' => 'Doręczenie następnego dnia roboczego (zamówienie do 12:00)',
        'price_gross' => 29.99,
        'grade' => 8,
    ],
];

// Dostawa jest opodatkowana jak sprzedawany towar. Grupa pochodzi z polskiego pakietu lokalizacyjnego
// (wymaga PS_COUNTRY=pl w compose.yaml). PrestaShop trzyma ceny dostawy netto, więc netto = brutto / 1,23.
const CARRIER_TAX_RULES_GROUP = 'PL Standard Rate (23%)';
const CARRIER_VAT_RATE = 23;

// Cena zależy od wagi, z jednym przedziałem obejmującym każdą realną wagę zamówienia.
// Limit wagi zamówienia ustawia osobno max_weight przewoźnika (limits()), a nie górna granica tego przedziału.
const CARRIER_WEIGHT_RANGE = [0, 10000]; // kg, przedział [od, do)

function carrierConfigKey(string $key): string
{
    return 'SALES_CARRIER_REF_' . $key;
}

/**
 * Zwraca istniejącego przewoźnika albo nowy obiekt. Szuka po id_reference zapamiętanym w konfiguracji, a gdy go
 * brak (np. wpis usunięty z bazy) - po nazwie, żeby nie utworzyć drugiego przewoźnika o tej samej nazwie.
 */
function findCarrier(string $key, string $name): Carrier
{
    $reference = (int) Configuration::get(carrierConfigKey($key));
    if ($reference > 0) {
        $carrier = Carrier::getCarrierByReference($reference);
        if ($carrier instanceof Carrier) {
            return $carrier;
        }
    }

    $idCarrier = (int) Db::getInstance()->getValue(
        'SELECT `id_carrier` FROM `' . _DB_PREFIX_ . 'carrier`
        WHERE `deleted` = 0 AND `name` = \'' . pSQL($name) . '\' ORDER BY `id_carrier` DESC'
    );

    return new Carrier($idCarrier ?: null);
}

function upsertCarrier(string $key, array $definition, int $idZone, int $idTaxRulesGroup): Carrier
{
    $carrier = findCarrier($key, $definition['name']);
    $isNew = !Validate::isLoadedObject($carrier);

    $carrier->name = $definition['name'];
    $carrier->delay = array_fill_keys(Language::getIDs(false), $definition['delay']); // pole wielojęzyczne
    $carrier->grade = $definition['grade'];
    $carrier->active = true;
    $carrier->deleted = false;
    $carrier->is_free = false;
    $carrier->shipping_handling = false; // bez dodatkowej opłaty manipulacyjnej PS_SHIPPING_HANDLING
    $carrier->shipping_external = false;
    $carrier->need_range = false;
    $carrier->shipping_method = Carrier::SHIPPING_METHOD_WEIGHT;
    $carrier->range_behavior = false; // poza przedziałem wag: najwyższa cena (przedział i tak obejmuje każdą wagę)

    if ($isNew) {
        // Carrier::add() ustawia id_reference = id_carrier i wiąże przewoźnika z aktywnymi modułami płatności.
        $carrier->add() || fail("nie udalo sie utworzyc przewoznika {$definition['name']}");
        // add() zapisuje id_reference w bazie osobnym UPDATE, ale nie ustawia go w obiekcie - bez tej linii
        // id_reference byłoby puste, a disableOtherCarriers() wyłączyłoby także naszych przewoźników.
        $carrier->id_reference = (int) $carrier->id;
        info("utworzono przewoznika {$definition['name']} (id {$carrier->id})");
    } else {
        $carrier->update() || fail("nie udalo sie zaktualizowac przewoznika {$definition['name']}");
    }
    (int) $carrier->id_reference > 0 || fail("przewoznik {$definition['name']} nie ma id_reference");
    // Zapisywane przy każdym starcie, także dla przewoźnika znalezionego po nazwie.
    Configuration::updateValue(carrierConfigKey($key), (int) $carrier->id_reference);

    // Strefa: przewoźnik obsługuje tylko strefę, do której należy Polska.
    if (!$carrier->getZone($idZone)) {
        $carrier->addZone($idZone) || fail("nie udalo sie przypisac strefy do {$definition['name']}");
    }

    // Wszystkie grupy klientów (odwiedzający, gość, klient). setGroups() usuwa stare przypisania i wstawia nowe.
    $carrier->setGroups(array_column(Group::getGroups((int) Configuration::get('PS_LANG_DEFAULT')), 'id_group'));

    $carrier->setTaxRulesGroup($idTaxRulesGroup, true);

    setCarrierPrice($carrier, $idZone, (float) $definition['price_gross']);

    return $carrier;
}

/**
 * Ustawia jeden przedział wagi i cenę dostawy. Przy każdym starcie kasuje ceny przewoźnika i wstawia je od nowa,
 * dzięki czemu zmiana ceny w CARRIERS zawsze trafia do bazy i nie powstają duplikaty.
 */
function setCarrierPrice(Carrier $carrier, int $idZone, float $priceGross): void
{
    [$from, $to] = CARRIER_WEIGHT_RANGE;

    $ranges = RangeWeight::getRanges($carrier->id);
    $range = null;
    foreach ($ranges as $row) {
        $candidate = new RangeWeight((int) $row['id_range_weight']);
        if ((float) $candidate->delimiter1 === (float) $from && (float) $candidate->delimiter2 === (float) $to) {
            $range = $candidate;
        } else {
            $candidate->delete(); // przedziały spoza konfiguracji (np. dodane w panelu)
        }
    }
    if ($range === null) {
        $range = new RangeWeight();
        $range->id_carrier = $carrier->id;
        $range->delimiter1 = $from;
        $range->delimiter2 = $to;
        $range->add() || fail("nie udalo sie utworzyc przedzialu wagi dla {$carrier->name}");
    }

    Db::getInstance()->delete('delivery', 'id_carrier = ' . (int) $carrier->id);
    $carrier->addDeliveryPrice([[
        'id_range_price' => null,
        'id_range_weight' => (int) $range->id,
        'id_carrier' => (int) $carrier->id,
        'id_zone' => $idZone,
        // Netto z 6 miejscami po przecinku, żeby brutto po doliczeniu 23% VAT dało dokładnie price_gross.
        'price' => round($priceGross / (1 + CARRIER_VAT_RATE / 100), 6),
        // id_shop i id_shop_group uzupełnia addDeliveryPrice() z kontekstu - w CLI to sklep domyślny.
    ]]) || fail("nie udalo sie ustawic ceny dla {$carrier->name}");
}

/**
 * Upewnia się, że obie metody płatności są dostępne u przewoźnika. Carrier::add() robi to przy tworzeniu,
 * ale np. przewoźnik utworzony przed włączeniem modułu nie miałby powiązania i koszyk nie pokazałby płatności.
 */
function linkPaymentModules(Carrier $carrier): void
{
    foreach (PAYMENT_MODULES_ENABLED as $name) {
        $idModule = (int) Module::getModuleIdByName($name);
        foreach (Shop::getShops(true, null, true) as $idShop) {
            // Klucz główny (id_module, id_shop, id_reference) - INSERT IGNORE nie tworzy duplikatów.
            Db::getInstance()->execute(
                'INSERT IGNORE INTO `' . _DB_PREFIX_ . 'module_carrier` (`id_module`, `id_shop`, `id_reference`) VALUES ('
                . $idModule . ', ' . (int) $idShop . ', ' . (int) $carrier->id_reference . ')'
            );
        }
    }
}

/**
 * Wyłącza przewoźników spoza CARRIERS: z instalatora („Click and collect”) i z danych demo („My carrier” itd.).
 * Nie usuwamy ich, bo mogą się do nich odwoływać zamówienia.
 */
function disableOtherCarriers(array $keepReferences): void
{
    // Zabezpieczenie: pusta lub zerowa referencja oznaczałaby wyłączenie wszystkich przewoźników.
    in_array(0, $keepReferences, true) && fail('pusta referencja przewoznika, nie wylaczam pozostalych');

    $rows = Db::getInstance()->executeS(
        'SELECT `id_carrier`, `name` FROM `' . _DB_PREFIX_ . 'carrier`
        WHERE `deleted` = 0 AND `active` = 1 AND `id_reference` NOT IN (' . implode(', ', array_map('intval', $keepReferences)) . ')'
    );
    foreach ($rows as $row) {
        $carrier = new Carrier((int) $row['id_carrier']);
        $carrier->active = false;
        $carrier->update() || fail("nie udalo sie wylaczyc przewoznika {$row['name']}");
        info("wylaczono przewoznika {$row['name']}");
    }
}

function carriers(): void
{
    $idZone = (int) Country::getIdZone((int) Country::getByIso('PL'));
    $idZone > 0 || fail('brak strefy dla Polski');

    $idTaxRulesGroup = (int) TaxRulesGroup::getIdByName(CARRIER_TAX_RULES_GROUP);
    $idTaxRulesGroup > 0 || fail('brak grupy podatkowej „' . CARRIER_TAX_RULES_GROUP . '” (czy PS_COUNTRY=pl?)');

    $references = [];
    $defaultCarrierId = 0;
    foreach (CARRIERS as $key => $definition) {
        $carrier = upsertCarrier($key, $definition, $idZone, $idTaxRulesGroup);
        linkPaymentModules($carrier);
        $references[] = (int) $carrier->id_reference;
        $defaultCarrierId = $defaultCarrierId ?: (int) $carrier->id; // pierwszy z listy (najtańszy) domyślny
    }

    disableOtherCarriers($references);
    Configuration::updateValue('PS_CARRIER_DEFAULT', $defaultCarrierId);

    info('przewoznicy: ' . implode(', ', array_column(CARRIERS, 'name')));
}

// --- Kraje -------------------------------------------------------------------------------------------------

// Sprzedajemy i wysyłamy tylko w Polsce (strona CMS „Dostawa”). Płatności są przypisane wyłącznie do Polski,
// więc adres w innym kraju kończyłby się w koszyku komunikatem o braku metod płatności.
const SHOP_COUNTRY_ISO = 'PL';

/**
 * Zostawia aktywną tylko Polskę. Instalator wyłącza inne kraje, ale dane demo włączają m.in. USA i Francję.
 * Kraje są wyłączane, nie usuwane - istniejące adresy (np. konta demo) zostają w bazie.
 */
function countries(): void
{
    $idCountry = (int) Country::getByIso(SHOP_COUNTRY_ISO);
    $idCountry > 0 || fail('brak kraju ' . SHOP_COUNTRY_ISO);

    $rows = Db::getInstance()->executeS(
        'SELECT `id_country`, `iso_code` FROM `' . _DB_PREFIX_ . 'country`
        WHERE (`active` = 1 AND `id_country` <> ' . $idCountry . ') OR (`active` = 0 AND `id_country` = ' . $idCountry . ')'
    );
    foreach ($rows as $row) {
        $country = new Country((int) $row['id_country']);
        $country->active = ((int) $row['id_country'] === $idCountry);
        $country->update() || fail("nie udalo sie zmienic kraju {$row['iso_code']}");
        info(($country->active ? 'wlaczono' : 'wylaczono') . " kraj {$row['iso_code']}");
    }
}

// --- Ograniczenia dostawy ----------------------------------------------------------------------------------

/**
 * Odczytuje dodatnią liczbę ze zmiennej środowiskowej (ustawianej w deploy/compose.yaml).
 */
function envPositiveNumber(string $name): float
{
    $value = getenv($name);
    if ($value === false || !is_numeric($value) || (float) $value <= 0) {
        fail("zmienna $name musi byc liczba dodatnia (jest: " . var_export($value, true) . ')');
    }

    return (float) $value;
}

/**
 * Darmowa dostawa od progu i limit wagi zamówienia (WYMAGANIA.md, W3). Wartości pochodzą z compose.yaml,
 * żeby zmiana (np. próg 1500 zł na odbiorze) nie wymagała edycji kodu.
 */
function limits(): void
{
    // PrestaShop porównuje próg z wartością koszyka Z VAT, bez kosztu dostawy, po rabatach,
    // i warunkiem >= - dostawa jest darmowa także przy wartości równej progowi (Cart::getPackageShippingCost).
    $freeShippingThreshold = envPositiveNumber('FREE_SHIPPING_THRESHOLD');
    Configuration::updateValue('PS_SHIPPING_FREE_PRICE', $freeShippingThreshold);
    // Instalator ustawia 2 zł opłaty manipulacyjnej. Nasi przewoźnicy jej nie doliczają (shipping_handling = 0),
    // ale zerujemy ją, żeby żaden przewoźnik nie dodawał ukrytej opłaty.
    Configuration::updateValue('PS_SHIPPING_HANDLING', 0);

    // Limit wagi: przewoźnik znika z listy, gdy koszyk waży więcej niż max_weight (Carrier::getAvailableCarrierList).
    // Sprawdzenie jest niezależne od darmowej dostawy, a koszyk ważący dokładnie tyle co limit przechodzi.
    // Bez przewoźnika nie da się przejść do płatności, więc zamówienia powyżej limitu nie da się złożyć.
    $maxWeight = envPositiveNumber('MAX_ORDER_WEIGHT_KG');
    foreach (array_keys(CARRIERS) as $key) {
        $carrier = Carrier::getCarrierByReference((int) Configuration::get(carrierConfigKey($key)));
        $carrier instanceof Carrier || fail("brak przewoznika $key");
        if ((float) $carrier->max_weight !== $maxWeight) {
            $carrier->max_weight = $maxWeight;
            $carrier->update() || fail("nie udalo sie ustawic limitu wagi dla {$carrier->name}");
        }
    }

    info("darmowa dostawa od $freeShippingThreshold zl brutto, limit wagi zamowienia $maxWeight kg");
}

// --- Uruchomienie ------------------------------------------------------------------------------------------

try {
    countries(); // najpierw, żeby kolejne kroki działały już na samej Polsce
    payments();
    carriers();
    limits();
} catch (Throwable $e) {
    info('BLAD: ' . $e->getMessage());
    exit(1);
}

info('konfiguracja sprzedazy zakonczona');
