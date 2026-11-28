<?php
/**
 * Dopasowuje zainstalowany sklep do zmiennych środowiskowych kontenera (deploy/compose.yaml, wartości z .env).
 *
 * Instalator PrestaShop zapisuje te ustawienia tylko raz, przy pierwszej instalacji:
 *  1. dane bazy      - app/config/parameters.php       <- DB_SERVER, DB_PORT, DB_NAME, DB_USER, DB_PASSWD
 *  2. katalog admina - nazwa katalogu w /var/www/html  <- PS_FOLDER_ADMIN
 *  3. domena i SSL   - ps_shop_url, PS_SHOP_DOMAIN(_SSL), PS_SSL_ENABLED(_EVERYWHERE), .htaccess <- PS_DOMAIN, PS_ENABLE_SSL
 * Bez tego sklep odtworzony z kopii (make restore) albo po zmianie portu/domeny w .env łączyłby się ze starą bazą,
 * przekierowywał na stary adres i nie pokazywał zdjęć (reguły zdjęć w .htaccess mają warunek na domenę).
 *
 * Uruchamiany przy każdym starcie kontenera przez shop/init-scripts/02-sync-env.sh (jako www-data), przed
 * 05-cache-warmup.sh, który już ładuje PrestaShop. Idempotentny: przy zgodnych wartościach niczego nie zapisuje.
 */

declare(strict_types=1);

const LOG_PREFIX = '02-sync-env';
const ROOT = '/var/www/html';
const PARAMETERS_FILE = ROOT . '/app/config/parameters.php';

function info(string $message): void
{
    echo LOG_PREFIX . ': ' . $message . PHP_EOL;
}

function fail(string $message): never
{
    throw new RuntimeException($message);
}

function env(string $name): string
{
    $value = getenv($name);
    if ($value === false || $value === '') {
        fail("brak zmiennej srodowiskowej $name");
    }

    return $value;
}

// Usuwa cache Symfony. Skompilowany kontener trzyma m.in. dane bazy z parameters.php. Katalogi, bez których
// nie działa import i faktury (purifier, tcpdf), odtworzy zaraz 05-cache-warmup.sh.
function removeSymfonyCache(): void
{
    foreach (['prod', 'dev'] as $env) {
        $dir = ROOT . '/var/cache/' . $env;
        if (is_dir($dir)) {
            exec('rm -rf ' . escapeshellarg($dir), $output, $code);
            if ($code !== 0) {
                fail("nie udalo sie usunac $dir");
            }
        }
    }
}

// --- 1. Dane bazy w parameters.php ------------------------------------------------------------------------
// Bez ładowania PrestaShop: z błędnymi danymi bazy config.inc.php by się nie uruchomił.

function syncDatabaseParameters(): bool
{
    $config = require PARAMETERS_FILE;
    if (!is_array($config) || !isset($config['parameters']) || !is_array($config['parameters'])) {
        fail('nieoczekiwany format ' . PARAMETERS_FILE);
    }

    // DB_PORT ma w obrazie PrestaShop wartość domyślną 3306, pozostałe ustawia compose.yaml
    $expected = [
        'database_host' => env('DB_SERVER'),
        'database_port' => env('DB_PORT'),
        'database_name' => env('DB_NAME'),
        'database_user' => env('DB_USER'),
        'database_password' => env('DB_PASSWD'),
    ];

    $changed = [];
    foreach ($expected as $key => $value) {
        if ((string) ($config['parameters'][$key] ?? '') !== $value) {
            $config['parameters'][$key] = $value;
            $changed[] = $key;
        }
    }
    if ($changed === []) {
        return false;
    }

    // Ten sam format co instalator (var_export). Zapis do pliku obok i zamiana nazwy, żeby nikt nie wczytał
    // połowy pliku.
    $tmp = PARAMETERS_FILE . '.tmp';
    $content = '<?php return ' . var_export($config, true) . ';' . PHP_EOL;
    if (file_put_contents($tmp, $content) === false || !rename($tmp, PARAMETERS_FILE)) {
        @unlink($tmp);
        fail('nie udalo sie zapisac ' . PARAMETERS_FILE);
    }
    // Same nazwy pól, bez wartości (hasło)
    info('dane bazy w parameters.php zaktualizowane: ' . implode(', ', $changed));

    return true;
}

// --- 2. Katalog panelu admina ------------------------------------------------------------------------------
// docker_run.sh zmienia nazwę katalogu tylko przy instalacji (admin -> PS_FOLDER_ADMIN).

function syncAdminFolder(): bool
{
    $folder = env('PS_FOLDER_ADMIN');
    if (is_dir(ROOT . '/' . $folder)) {
        return false;
    }

    // Katalog panelu rozpoznajemy po jego index.php, który jako jedyny definiuje _PS_ADMIN_DIR_
    $candidates = [];
    foreach (glob(ROOT . '/*/index.php') ?: [] as $file) {
        if (str_contains((string) file_get_contents($file), '_PS_ADMIN_DIR_')) {
            $candidates[] = dirname($file);
        }
    }

    // Bez panelu sklep dla klientów działa, więc tylko ostrzeżenie (kontener startuje dalej)
    if (count($candidates) !== 1) {
        info("UWAGA: nie ma katalogu admina $folder, a znaleziono " . count($candidates)
            . ' kandydatow - panel moze byc niedostepny');

        return false;
    }

    if (!rename($candidates[0], ROOT . '/' . $folder)) {
        fail('nie udalo sie zmienic nazwy ' . basename($candidates[0]) . " na $folder");
    }
    info('katalog admina: ' . basename($candidates[0]) . " -> $folder");

    return true;
}

// --- 3. Domena i SSL ---------------------------------------------------------------------------------------

function syncDomain(): bool
{
    $domain = env('PS_DOMAIN');
    $ssl = env('PS_ENABLE_SSL') === '1' ? '1' : '0';
    $changed = false;

    // Główny adres sklepu domyślnego (jedyny sklep, bez multistore)
    $idShop = (int) Configuration::get('PS_SHOP_DEFAULT');
    $idShopUrl = (int) Db::getInstance()->getValue(
        'SELECT id_shop_url FROM `' . _DB_PREFIX_ . 'shop_url` WHERE main = 1 AND id_shop = ' . $idShop
    );
    if ($idShopUrl === 0) {
        fail("brak glownego adresu sklepu (ps_shop_url, id_shop=$idShop)");
    }
    $shopUrl = new ShopUrl($idShopUrl);
    if ($shopUrl->domain !== $domain || $shopUrl->domain_ssl !== $domain) {
        info("domena sklepu: {$shopUrl->domain} -> $domain");
        $shopUrl->domain = $domain;
        $shopUrl->domain_ssl = $domain;
        if (!$shopUrl->update()) {
            fail('nie udalo sie zapisac adresu sklepu (ps_shop_url)');
        }
        ShopUrl::resetMainDomainCache();
        $changed = true;
    }

    // Wartości globalne, tak jak zapisuje je instalator (id_shop i id_shop_group = NULL)
    $values = [
        'PS_SHOP_DOMAIN' => $domain,
        'PS_SHOP_DOMAIN_SSL' => $domain,
        'PS_SSL_ENABLED' => $ssl,
        'PS_SSL_ENABLED_EVERYWHERE' => $ssl,
    ];
    foreach ($values as $key => $value) {
        if ((string) Configuration::getGlobalValue($key) !== $value) {
            Configuration::updateGlobalValue($key, $value);
            info("$key = $value");
            $changed = true;
        }
    }

    // .htaccess ma reguły zdjęć z warunkiem RewriteCond %{HTTP_HOST} ^<domena>$ i komentarz #Domain: <domena>.
    // Sprawdzamy go także przy zgodnej bazie - mógł zostać ze starą domeną po przerwanym starcie.
    $htaccess = ROOT . '/.htaccess';
    $marker = '#Domain: ' . $domain . PHP_EOL;
    if (!is_file($htaccess) || !str_contains((string) file_get_contents($htaccess), $marker)) {
        if (!Tools::generateHtaccess()) {
            fail('nie udalo sie wygenerowac .htaccess');
        }
        clearstatcache();
        if (!str_contains((string) file_get_contents($htaccess), $marker)) {
            fail("wygenerowany .htaccess nie zawiera domeny $domain");
        }
        info('.htaccess wygenerowany dla domeny ' . $domain);
        $changed = true;
    }

    return $changed;
}

try {
    // Kolejność: najpierw pliki, potem PrestaShop - ładuje się dopiero z poprawnymi danymi bazy
    if (syncDatabaseParameters()) {
        removeSymfonyCache();
    }
    $adminChanged = syncAdminFolder();

    require ROOT . '/config/config.inc.php';
    $domainChanged = syncDomain();

    if ($adminChanged || $domainChanged) {
        // Adresy i ścieżki trafiają do skompilowanych szablonów i cache Symfony
        Tools::clearSmartyCache();
        removeSymfonyCache();
    }

    info('sklep zgodny ze zmiennymi srodowiskowymi');
} catch (Throwable $e) {
    info('BLAD: ' . $e->getMessage());
    exit(1);
}
