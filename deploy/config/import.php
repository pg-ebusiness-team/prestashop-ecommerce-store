<?php
/**
 * Wgrywa ustawienia z deploy/config/configuration.json (eksport: export.php, make config-export).
 * make config-import kopiuje plik do kontenera shop jako /tmp/configuration.json i uruchamia ten skrypt
 * przez stdin jako www-data, a potem czyści cache.
 *
 * Idempotentny: zapisuje tylko wartości różne od bieżących, ponowne uruchomienie nic nie zmienia.
 * Nie usuwa ustawień nieobecnych w pliku (wykluczone w eksporcie zostają takie, jakie są w sklepie).
 * Ustawienia, które przy każdym starcie kontenera nadpisują init-scripts (np. configure-sales.php), i tak
 * wrócą do wersji z repo przy następnym restarcie.
 */

declare(strict_types=1);

require '/var/www/html/config/config.inc.php';

const INPUT = '/tmp/configuration.json';

try {
    $data = json_decode((string) file_get_contents(INPUT), true, 512, JSON_THROW_ON_ERROR);
    if (!isset($data['configuration'], $data['configuration_lang'])) {
        throw new RuntimeException(INPUT . ' nie zawiera sekcji configuration i configuration_lang');
    }

    $changed = [];

    foreach ($data['configuration'] as $name => $value) {
        $current = Configuration::getGlobalValue($name);
        if ($current === false || (string) $current !== (string) $value) {
            // html=true: wartości pochodzą z bazy sklepu, bez tego PrestaShop usunąłby z nich znaczniki
            Configuration::updateGlobalValue($name, $value, true);
            $changed[] = $name;
        }
    }

    // Wartości językowe są zapisane po kodzie ISO; języka, którego sklep nie ma, nie da się wgrać
    $skippedLang = [];
    foreach ($data['configuration_lang'] as $name => $byIso) {
        $values = [];
        foreach ($byIso as $iso => $value) {
            $idLang = (int) Language::getIdByIso($iso);
            if ($idLang === 0) {
                $skippedLang[$iso] = true;
                continue;
            }
            if ((string) Configuration::get($name, $idLang, 0, 0) !== (string) $value) {
                $values[$idLang] = $value;
            }
        }
        if ($values !== []) {
            // Pozostałe języki zostają bez zmian: updateValue zapisuje tylko podane id_lang
            Configuration::updateGlobalValue($name, $values, true);
            $changed[] = $name;
        }
    }

    foreach (array_keys($skippedLang) as $iso) {
        echo "config-import: UWAGA: sklep nie ma jezyka '$iso', jego wartosci pominieto" . PHP_EOL;
    }
    echo 'config-import: zmienione ustawienia: ' . count($changed)
        . ($changed === [] ? '' : ' (' . implode(', ', $changed) . ')') . PHP_EOL;
} catch (Throwable $e) {
    echo 'config-import: BLAD: ' . $e->getMessage() . PHP_EOL;
    exit(1);
}
