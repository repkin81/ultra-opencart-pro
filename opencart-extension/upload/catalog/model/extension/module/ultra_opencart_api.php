<?php
class ModelExtensionModuleUltraOpenCartApi extends Model {
    public function getProducts($limit, $offset) {
        $q = $this->db->query("SELECT p.product_id, p.model, p.sku, p.price, p.quantity, p.status, pd.name, pd.description, p.image, p.date_modified FROM `" . DB_PREFIX . "product` p LEFT JOIN `" . DB_PREFIX . "product_description` pd ON (p.product_id = pd.product_id AND pd.language_id = " . (int)$this->config->get('config_language_id') . ") ORDER BY p.product_id ASC LIMIT " . (int)$offset . "," . (int)$limit);
        return $q->rows;
    }

    public function getProduct($id) {
        $q = $this->db->query("SELECT p.product_id, p.model, p.sku, p.price, p.quantity, p.status, p.image, pd.name, pd.description, p.meta_title, p.meta_description, p.meta_keyword, p.date_modified FROM `" . DB_PREFIX . "product` p LEFT JOIN `" . DB_PREFIX . "product_description` pd ON (p.product_id = pd.product_id AND pd.language_id = " . (int)$this->config->get('config_language_id') . ") WHERE p.product_id = " . (int)$id . " LIMIT 1");
        return $q->num_rows ? $q->row : null;
    }

    public function createProduct($data) {
        $this->db->query("INSERT INTO `" . DB_PREFIX . "product` SET model = '" . $this->db->escape(isset($data['model']) ? $data['model'] : '') . "', sku = '" . $this->db->escape(isset($data['sku']) ? $data['sku'] : '') . "', price = '" . (float)(isset($data['price']) ? $data['price'] : 0) . "', quantity = '" . (int)(isset($data['quantity']) ? $data['quantity'] : 0) . "', status = '" . (int)(!empty($data['status'])) . "', image = '" . $this->db->escape(isset($data['image']) ? $data['image'] : '') . "', date_added = NOW(), date_modified = NOW()");
        $id = $this->db->getLastId();
        $name = isset($data['name']) ? $data['name'] : '';
        $description = isset($data['description']) ? $data['description'] : '';
        $this->db->query("INSERT INTO `" . DB_PREFIX . "product_description` SET product_id = " . (int)$id . ", language_id = " . (int)$this->config->get('config_language_id') . ", name = '" . $this->db->escape($name) . "', description = '" . $this->db->escape($description) . "', meta_title = '" . $this->db->escape(isset($data['meta_title']) ? $data['meta_title'] : '') . "', meta_description = '" . $this->db->escape(isset($data['meta_description']) ? $data['meta_description'] : '') . "', meta_keyword = '" . $this->db->escape(isset($data['meta_keyword']) ? $data['meta_keyword'] : '') . "'");
        return $id;
    }

    public function updateProduct($id, $data) {
        $fields = array();
        foreach (array('model','sku','image') as $key) if (array_key_exists($key, $data)) $fields[] = $key . " = '" . $this->db->escape($data[$key]) . "'";
        foreach (array('price','tax_class_id','quantity','minimum','subtract','stock_status_id','status') as $key) if (array_key_exists($key, $data)) $fields[] = $key . " = '" . (float)$data[$key] . "'";
        if ($fields) $this->db->query("UPDATE `" . DB_PREFIX . "product` SET " . implode(', ', $fields) . ", date_modified = NOW() WHERE product_id = " . (int)$id);
        $lang = (int)$this->config->get('config_language_id');
        $desc = array();
        foreach (array('name','description','meta_title','meta_description','meta_keyword') as $key) if (array_key_exists($key, $data)) $desc[] = $key . " = '" . $this->db->escape($data[$key]) . "'";
        if ($desc) $this->db->query("UPDATE `" . DB_PREFIX . "product_description` SET " . implode(', ', $desc) . " WHERE product_id = " . (int)$id . " AND language_id = " . $lang);
    }

    public function deleteProduct($id) {
        $this->db->query("DELETE FROM `" . DB_PREFIX . "product` WHERE product_id = " . (int)$id);
        $this->db->query("DELETE FROM `" . DB_PREFIX . "product_description` WHERE product_id = " . (int)$id);
        $this->db->query("DELETE FROM `" . DB_PREFIX . "product_to_category` WHERE product_id = " . (int)$id);
        $this->db->query("DELETE FROM `" . DB_PREFIX . "product_to_store` WHERE product_id = " . (int)$id);
    }

    public function getCategories($limit, $offset) {
        return $this->db->query("SELECT c.category_id, c.parent_id, c.status, cd.name, cd.description, cd.meta_title, cd.meta_description, cd.meta_keyword FROM `" . DB_PREFIX . "category` c LEFT JOIN `" . DB_PREFIX . "category_description` cd ON (c.category_id = cd.category_id AND cd.language_id = " . (int)$this->config->get('config_language_id') . ") ORDER BY c.category_id ASC LIMIT " . (int)$offset . "," . (int)$limit)->rows;
    }

    public function getCategory($id) {
        $q = $this->db->query("SELECT c.category_id, c.parent_id, c.status, cd.name, cd.description, cd.meta_title, cd.meta_description, cd.meta_keyword FROM `" . DB_PREFIX . "category` c LEFT JOIN `" . DB_PREFIX . "category_description` cd ON (c.category_id = cd.category_id AND cd.language_id = " . (int)$this->config->get('config_language_id') . ") WHERE c.category_id = " . (int)$id . " LIMIT 1");
        return $q->num_rows ? $q->row : null;
    }

    public function createCategory($data) {
        $this->db->query("INSERT INTO `" . DB_PREFIX . "category` SET parent_id = " . (int)(isset($data['parent_id']) ? $data['parent_id'] : 0) . ", status = " . (int)!empty($data['status']) . ", date_added = NOW(), date_modified = NOW()");
        $id = $this->db->getLastId();
        $this->db->query("INSERT INTO `" . DB_PREFIX . "category_description` SET category_id = " . (int)$id . ", language_id = " . (int)$this->config->get('config_language_id') . ", name = '" . $this->db->escape(isset($data['name']) ? $data['name'] : '') . "', description = '" . $this->db->escape(isset($data['description']) ? $data['description'] : '') . "', meta_title = '" . $this->db->escape(isset($data['meta_title']) ? $data['meta_title'] : '') . "', meta_description = '" . $this->db->escape(isset($data['meta_description']) ? $data['meta_description'] : '') . "', meta_keyword = '" . $this->db->escape(isset($data['meta_keyword']) ? $data['meta_keyword'] : '') . "'");
        return $id;
    }

    public function updateCategory($id, $data) {
        $fields = array();
        if (array_key_exists('parent_id', $data)) $fields[] = 'parent_id = ' . (int)$data['parent_id'];
        if (array_key_exists('status', $data)) $fields[] = 'status = ' . (int)!empty($data['status']);
        if ($fields) $this->db->query("UPDATE `" . DB_PREFIX . "category` SET " . implode(', ', $fields) . ", date_modified = NOW() WHERE category_id = " . (int)$id);
        $desc = array();
        foreach (array('name','description','meta_title','meta_description','meta_keyword') as $key) if (array_key_exists($key, $data)) $desc[] = $key . " = '" . $this->db->escape($data[$key]) . "'";
        if ($desc) $this->db->query("UPDATE `" . DB_PREFIX . "category_description` SET " . implode(', ', $desc) . " WHERE category_id = " . (int)$id . " AND language_id = " . (int)$this->config->get('config_language_id'));
    }

    public function deleteCategory($id) {
        $this->db->query("DELETE FROM `" . DB_PREFIX . "category` WHERE category_id = " . (int)$id);
        $this->db->query("DELETE FROM `" . DB_PREFIX . "category_description` WHERE category_id = " . (int)$id);
    }

    public function bulkStockPrice($data) {
        $items = isset($data['items']) && is_array($data['items']) ? $data['items'] : array();
        $count = 0;
        foreach ($items as $item) {
            if (empty($item['product_id'])) continue;
            $sets = array();
            if (isset($item['price'])) $sets[] = "price = '" . (float)$item['price'] . "'";
            if (isset($item['quantity'])) $sets[] = "quantity = '" . (int)$item['quantity'] . "'";
            if ($sets) { $this->db->query("UPDATE `" . DB_PREFIX . "product` SET " . implode(', ', $sets) . ", date_modified = NOW() WHERE product_id = " . (int)$item['product_id']); $count++; }
        }
        return $count;
    }
}
