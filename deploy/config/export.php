<?php
/**
 * Eksport ustawień sklepu (tabele ps_configuration i ps_configuration_lang) do JSON na stdout
 * (WYMAGANIA.md, D4: „Eksport ustawień w repo pozwala przywrócić konfigurację; bez danych osobowych i sekretów”).
 *
 * make config-export zapisuje wynik w deploy/config/configuration.json, a make config-import (import.php) go wgrywa.
 * Uruchamiany przez stdin w kontenerze shop jako www-data, jak deploy/init/facets.php - bez przebudowy obrazu.
 *
 * Klucze są posortowane, a wartości językowe zapisane po kodzie ISO języka, więc plik jest stabilny między
 * instancjami i zmiana ustawienia w panelu daje w PR jednolinijkowy diff.
 * Komunikaty idą na stderr, żeby nie trafiły do pliku JSON.
 */

declare(strict_types=1);

require '/var/www/html/config/config.inc.php';

// --- Wykluczenia ---------------------------------------------------------------------------------------------

// Sekrety: nazwy z tymi słowami (np. NW_SALT, PS_SMARTY_CONSOLE_KEY, PS_MAIL_PASSWD, MB_SECRET_WORD) ...
const SECRET_PATTERN = '/KEY|TOKEN|PASSWD|PASSWORD|SECRET|SALT/';
// ... poza ustawieniami, które tylko zawierają te słowa w nazwie (polityka haseł, ochrona tokenem w panelu)
const SECRET_PATTERN_EXCEPTIONS = [
    'PS_PASSWD_RESET_VALIDITY',
    'PS_PASSWD_TIME_BACK',
    'PS_PASSWD_TIME_FRONT',
    'PS_SECURITY_PASSWORD_POLICY_MAXIMUM_LENGTH',
    'PS_SECURITY_PASSWORD_POLICY_MINIMUM_LENGTH',
    'PS_SECURITY_PASSWORD_POLICY_MINIMUM_SCORE',
    'PS_TOKEN_ENABLE',
];

const EXCLUDED = [
    // Dane osobowe: adres e-mail administratora (ADMIN_MAIL) jako odbiorca powiadomień i logów.
    // Wartości zawierające ADMIN_MAIL są dodatkowo odrzucane niżej, niezależnie od nazwy.
    'MA_MERCHANT_MAILS' => 'e-mail administratora',
    'PS_LOGS_EMAIL_RECEIVERS' => 'e-mail administratora',
    'PS_MAIL_USER' => 'login SMTP',
    // Środowisko: ustawia przy każdym starcie shop/init-scripts/02-sync-env.sh i 10-configure-mail.sh ze zmiennych
    'PS_SHOP_DOMAIN' => 'srodowisko (02-sync-env)',
    'PS_SHOP_DOMAIN_SSL' => 'srodowisko (02-sync-env)',
    'PS_SSL_ENABLED' => 'srodowisko (02-sync-env)',
    'PS_SSL_ENABLED_EVERYWHERE' => 'srodowisko (02-sync-env)',
    'PS_MAIL_METHOD' => 'srodowisko (10-configure-mail)',
    'PS_MAIL_SERVER' => 'srodowisko (10-configure-mail)',
    'PS_MAIL_SMTP_PORT' => 'srodowisko (10-configure-mail)',
    'PS_MAIL_SMTP_ENCRYPTION' => 'srodowisko (10-configure-mail)',
    // ID rekordów zależne od instancji, ustawiane przez skrypty: przewoźnicy (configure-sales.php rozpoznaje
    // swoich przewoźników po SALES_CARRIER_REF_* - cudze ID wskazałyby inne rekordy), górne menu z ID kategorii
    // z importu (theme.sql)
    'PS_CARRIER_DEFAULT' => 'ID z instancji (configure-sales.php)',
    'SALES_CARRIER_REF_STANDARD' => 'ID z instancji (configure-sales.php)',
    'SALES_CARRIER_REF_EXPRESS' => 'ID z instancji (configure-sales.php)',
    'MOD_BLOCKTOPMENU_ITEMS' => 'ID z instancji (theme.sql)',
    // Wersje, znaczniki czasu i stan wewnętrzny - nie są ustawieniami
    'PS_VERSION_DB' => 'wersja',
    'PS_INSTALL_VERSION' => 'wersja',
    'PS_INSTALL_XML_LOADERS_ID' => 'stan instalatora',
    'PS_1_3_UPDATE_DATE' => 'znacznik czasu',
    'PS_1_3_2_UPDATE_DATE' => 'znacznik czasu',
    'PS_IMG_UPDATE_TIME' => 'znacznik czasu',
    'GSITEMAP_LAST_EXPORT' => 'znacznik czasu',
    'PS_DASHGOALS_CURRENT_YEAR' => 'stan panelu',
    'PS_LAYERED_INDEXED' => 'stan indeksu filtrow',
    'PS_NEWSLETTER_RAND' => 'wartosc losowa instancji',
    'UPGRADER_BACKUPDB_FILENAME' => 'stan aktualizatora',
    'UPGRADER_BACKUPFILES_FILENAME' => 'stan aktualizatora',
];

function excludedReason(string $name, ?string $value, string $adminMail): ?string
{
    if (isset(EXCLUDED[$name])) {
        return EXCLUDED[$name];
    }
    if (preg_match(SECRET_PATTERN, $name) && !in_array($name, SECRET_PATTERN_EXCEPTIONS, true)) {
        return 'sekret';
    }
    if ($adminMail !== '' && $value !== null && stripos($value, $adminMail) !== false) {
        return 'e-mail administratora';
    }

    return null;
}

// Stała STDERR nie istnieje, gdy PHP czyta skrypt ze stdin (php < export.php). Uchwyt otwieramy raz:
// file_put_contents('php://stderr') przy zamknięciu zamyka deskryptor 2 i kolejne zapisy przerywają skrypt.
function stderr(string $message): void
{
    static $handle = null;
    $handle ??= fopen('php://stderr', 'w');
    fwrite($handle, $message);
}

// --- Eksport -------------------------------------------------------------------------------------------------

try {
    $adminMail = (string) getenv('ADMIN_MAIL');
    $db = Db::getInstance();

    // Sklep ma tylko wartości globalne (id_shop i id_shop_group = NULL); wartości per sklep oznaczałyby
    // multistore, którego eksport nie obsługuje
    $scoped = (int) $db->getValue('SELECT COUNT(*) FROM `' . _DB_PREFIX_ . 'configuration`
        WHERE id_shop IS NOT NULL OR id_shop_group IS NOT NULL');
    if ($scoped > 0) {
        throw new RuntimeException("$scoped ustawien przypisanych do sklepu lub grupy sklepow - eksport obsluguje tylko wartosci globalne");
    }

    $configuration = [];
    $excluded = [];
    foreach ($db->executeS('SELECT name, value FROM `' . _DB_PREFIX_ . 'configuration` ORDER BY name') as $row) {
        $reason = excludedReason($row['name'], $row['value'], $adminMail);
        if ($reason !== null) {
            $excluded[$row['name']] = $reason;
            continue;
        }
        $configuration[$row['name']] = $row['value'];
    }

    $configurationLang = [];
    $rows = $db->executeS('SELECT c.name, l.iso_code, cl.value
        FROM `' . _DB_PREFIX_ . 'configuration_lang` cl
        JOIN `' . _DB_PREFIX_ . 'configuration` c ON c.id_configuration = cl.id_configuration
        JOIN `' . _DB_PREFIX_ . 'lang` l ON l.id_lang = cl.id_lang
        ORDER BY c.name, l.iso_code');
    foreach ($rows as $row) {
        $reason = excludedReason($row['name'], $row['value'], $adminMail);
        if ($reason !== null) {
            $excluded[$row['name']] = $reason;
            continue;
        }
        // Wartość językowa zastępuje wartość z ps_configuration (zwykle NULL)
        unset($configuration[$row['name']]);
        $configurationLang[$row['name']][$row['iso_code']] = $row['value'];
    }

    ksort($excluded);
    $result = [
        'opis' => 'Ustawienia sklepu z ps_configuration (make config-export). Wgranie: make config-import. '
            . 'Wykluczenia i ich powody: deploy/config/export.php.',
        'configuration' => $configuration,
        'configuration_lang' => $configurationLang,
    ];
    echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR),
        PHP_EOL;

    stderr(sprintf("config-export: %d ustawien, %d jezykowych, %d wykluczonych:\n",
        count($configuration), count($configurationLang), count($excluded)));
    foreach ($excluded as $name => $reason) {
        stderr("  $name ($reason)\n");
    }
} catch (Throwable $e) {
    stderr('config-export: BLAD: ' . $e->getMessage() . PHP_EOL);
    exit(1);
}
