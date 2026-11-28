<?php
if (!defined('_PS_VERSION_')) {
    exit;
}

class Omnibusprice extends Module
{
    public function __construct()
    {
        $this->name = 'omnibusprice';
        $this->tab = 'pricing_promotion';
        $this->version = '1.0.0';
        $this->author = 'Biznes Elektroniczny Projekt';
        $this->need_instance = 0;
        $this->bootstrap = true;

        parent::__construct();

        $this->displayName = $this->l('Najniższa cena z 30 dni');
        $this->description = $this->l('Przechowuje i wyświetla najniższą cenę produktu z ostatnich 30 dni.');
        $this->ps_versions_compliancy = array('min' => '8.0.0', 'max' => '8.99.99');
    }

    public function install()
    {
        return parent::install()
            && $this->registerHook('displayProductPriceBlock')
            && $this->createTable();
    }

    public function uninstall()
    {
        // Zachowujemy historię cen przy odinstalowaniu modułu.
        return parent::uninstall();
    }

    private function createTable()
    {
        $sql = 'CREATE TABLE IF NOT EXISTS `' . _DB_PREFIX_ . 'omnibusprice` (
            `id_omnibusprice` INT UNSIGNED NOT NULL AUTO_INCREMENT,
            `id_product` INT UNSIGNED NOT NULL,
            `id_product_attribute` INT UNSIGNED NOT NULL DEFAULT 0,
            `source_id` VARCHAR(64) NOT NULL,
            `source_attribute_id` VARCHAR(64) NULL,
            `lowest_price_30d` DECIMAL(20,6) NOT NULL,
            `date_add` DATETIME NOT NULL,
            `date_upd` DATETIME NOT NULL,
            PRIMARY KEY (`id_omnibusprice`),
            UNIQUE KEY `uniq_product_attribute` (`id_product`, `id_product_attribute`),
            KEY `idx_source` (`source_id`)
        ) ENGINE=' . _MYSQL_ENGINE_ . ' DEFAULT CHARSET=utf8mb4';

        return Db::getInstance()->execute($sql);
    }

    /**
     * Wyświetla informację w miejscach, w których motyw wywołuje hook
     * displayProductPriceBlock z typem after_price (custom_price podmienia cenę).
     */
    public function hookDisplayProductPriceBlock($params)
    {
        if (empty($params['type']) || $params['type'] !== 'after_price') {
            return '';
        }

        $product = isset($params['product']) ? $params['product'] : array();
        $idProduct = (int) (is_array($product)
            ? (isset($product['id_product']) ? $product['id_product'] : 0)
            : (isset($product->id_product) ? $product->id_product : 0));
        $idAttribute = (int) (is_array($product)
            ? (isset($product['id_product_attribute']) ? $product['id_product_attribute'] : 0)
            : (isset($product->id_product_attribute) ? $product->id_product_attribute : 0));

        if ($idProduct <= 0) {
            return '';
        }

        $price = $this->getLowestPrice($idProduct, $idAttribute);
        if ($price === null) {
            return '';
        }

        $formattedPrice = Tools::displayPrice($price);
        return '<div class="omnibus-price">'
            . $this->l('Najniższa cena z 30 dni: ')
            . '<span>' . $formattedPrice . '</span></div>';
    }

    private function getLowestPrice($idProduct, $idAttribute)
    {
        $db = Db::getInstance();
        $table = _DB_PREFIX_ . 'omnibusprice';

        if ($idAttribute > 0) {
            $specific = $db->getValue(
                'SELECT `lowest_price_30d` FROM `' . bqSQL($table) . '`'
                . ' WHERE `id_product` = ' . (int) $idProduct
                . ' AND `id_product_attribute` = ' . (int) $idAttribute
            );
            if ($specific !== false && $specific !== null) {
                return (float) $specific;
            }
        }

        $general = $db->getValue(
            'SELECT `lowest_price_30d` FROM `' . bqSQL($table) . '`'
            . ' WHERE `id_product` = ' . (int) $idProduct
            . ' AND `id_product_attribute` = 0'
        );

        return ($general === false || $general === null) ? null : (float) $general;
    }
}
