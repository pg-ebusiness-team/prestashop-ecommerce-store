<?php
class OmnibuspriceSyncModuleFrontController extends ModuleFrontController
{
    public $ajax = true;

    public function postProcess()
    {
        header('Content-Type: application/json; charset=utf-8');

        if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
            $this->respond(405, array('error' => 'Method not allowed'));
        }

        if (!$this->isAuthorized()) {
            header('WWW-Authenticate: Basic realm="PrestaShop Omnibus sync"');
            $this->respond(401, array('error' => 'Unauthorized'));
        }

        $raw = file_get_contents('php://input');
        $payload = json_decode($raw, true);
        if (!is_array($payload) || empty($payload['prices']) || !is_array($payload['prices'])) {
            $this->respond(400, array('error' => 'Expected JSON body with prices array'));
        }

        if (count($payload['prices']) > 500) {
            $this->respond(413, array('error' => 'Too many price rows'));
        }

        $db = Db::getInstance();
        $table = _DB_PREFIX_ . 'omnibusprice';
        $now = date('Y-m-d H:i:s');
        $saved = 0;

        foreach ($payload['prices'] as $row) {
            if (!is_array($row)) {
                $this->respond(400, array('error' => 'Invalid price row'));
            }

            $idProduct = isset($row['id_product']) ? (int) $row['id_product'] : 0;
            $idAttribute = isset($row['id_product_attribute']) ? (int) $row['id_product_attribute'] : 0;
            $sourceId = isset($row['source_id']) ? trim((string) $row['source_id']) : '';
            $sourceAttributeId = isset($row['source_attribute_id'])
                && $row['source_attribute_id'] !== null
                ? trim((string) $row['source_attribute_id'])
                : null;
            $priceRaw = isset($row['lowest_price_30d']) ? $row['lowest_price_30d'] : null;

            if ($idProduct <= 0 || $idAttribute < 0 || $sourceId === ''
                || !is_numeric($priceRaw) || (float) $priceRaw <= 0
                || (float) $priceRaw > 999999999999.999999
            ) {
                $this->respond(400, array('error' => 'Invalid product, source ID or price'));
            }

            if (!Product::existsInDatabase($idProduct, 'product')) {
                $this->respond(400, array('error' => 'Product does not exist', 'id_product' => $idProduct));
            }

            if ($idAttribute > 0) {
                $combination = new Combination($idAttribute);
                if (!Validate::isLoadedObject($combination) || (int) $combination->id_product !== $idProduct) {
                    $this->respond(400, array('error' => 'Combination does not belong to product'));
                }
            }

            $price = number_format((float) $priceRaw, 6, '.', '');
            $sourceIdSql = pSQL(substr($sourceId, 0, 64));
            $sourceAttributeSql = $sourceAttributeId === null
                ? 'NULL'
                : "'" . pSQL(substr($sourceAttributeId, 0, 64)) . "'";

            $sql = "INSERT INTO `" . bqSQL($table) . "`"
                . " (`id_product`, `id_product_attribute`, `source_id`, `source_attribute_id`, `lowest_price_30d`, `date_add`, `date_upd`) VALUES ("
                . (int) $idProduct . ", "
                . (int) $idAttribute . ", "
                . "'" . $sourceIdSql . "', "
                . $sourceAttributeSql . ", "
                . "'" . pSQL($price) . "', "
                . "'" . pSQL($now) . "', "
                . "'" . pSQL($now) . "')"
                . " ON DUPLICATE KEY UPDATE "
                . "`source_id` = VALUES(`source_id`), "
                . "`source_attribute_id` = VALUES(`source_attribute_id`), "
                . "`lowest_price_30d` = VALUES(`lowest_price_30d`), "
                . "`date_upd` = VALUES(`date_upd`)";

            if (!$db->execute($sql)) {
                $this->respond(500, array('error' => 'Could not save price'));
            }
            $saved++;
        }

        $this->respond(200, array('success' => true, 'saved' => $saved));
    }

    private function isAuthorized()
    {
        $apiKey = isset($_SERVER['PHP_AUTH_USER']) ? (string) $_SERVER['PHP_AUTH_USER'] : '';
        if ($apiKey === '' && isset($_SERVER['HTTP_AUTHORIZATION'])) {
            $header = trim($_SERVER['HTTP_AUTHORIZATION']);
            if (stripos($header, 'Basic ') === 0) {
                $decoded = base64_decode(substr($header, 6), true);
                if ($decoded !== false) {
                    $parts = explode(':', $decoded, 2);
                    $apiKey = isset($parts[0]) ? $parts[0] : '';
                }
            }
        }

        if ($apiKey === '') {
            return false;
        }

        return (bool) Db::getInstance()->getValue(
            'SELECT `id_webservice_account` FROM `' . _DB_PREFIX_ . 'webservice_account`'
            . ' WHERE `key` = "' . pSQL($apiKey) . '" AND `active` = 1'
        );
    }

    private function respond($statusCode, array $body)
    {
        http_response_code((int) $statusCode);
        die(json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
    }
}
