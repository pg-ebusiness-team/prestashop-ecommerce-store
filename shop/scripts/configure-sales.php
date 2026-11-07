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

// --- Uruchomienie ------------------------------------------------------------------------------------------

try {
    payments();
} catch (Throwable $e) {
    info('BLAD: ' . $e->getMessage());
    exit(1);
}

info('konfiguracja sprzedazy zakonczona');
