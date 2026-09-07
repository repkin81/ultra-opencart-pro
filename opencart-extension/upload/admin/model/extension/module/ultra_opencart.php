<?php
class ModelExtensionModuleUltraOpenCart extends Model {
    public function getLogs($limit = 100) {
        $limit = (int)$limit;
        if ($limit < 1) $limit = 100;
        return $this->db->query("SELECT * FROM `" . DB_PREFIX . "ultra_opencart_log` ORDER BY id DESC LIMIT " . $limit)->rows;
    }
}
