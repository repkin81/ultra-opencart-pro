<?php
class ControllerExtensionModuleUltraOpenCartApi extends Controller {
    public function health() {
        if (!$this->authorize()) return;
        $this->json(array('ok' => true, 'module' => 'ultra_opencart', 'version' => '0.1.0', 'store' => defined('HTTP_CATALOG') ? HTTP_CATALOG : ''));
    }

    public function products() {
        if (!$this->authorize()) return;
        $this->load->model('extension/module/ultra_opencart_api');
        $limit = isset($this->request->get['limit']) ? min(500, max(1, (int)$this->request->get['limit'])) : 100;
        $offset = isset($this->request->get['offset']) ? max(0, (int)$this->request->get['offset']) : 0;
        $this->json(array('data' => $this->model_extension_module_ultra_opencart_api->getProducts($limit, $offset)));
    }

    public function product() {
        if (!$this->authorize()) return;
        $this->load->model('extension/module/ultra_opencart_api');
        $id = isset($this->request->get['product_id']) ? (int)$this->request->get['product_id'] : 0;
        if (!$id) return $this->json(array('error' => 'product_id is required'), 400);
        if ($this->request->server['REQUEST_METHOD'] === 'GET') {
            $row = $this->model_extension_module_ultra_opencart_api->getProduct($id);
            return $this->json($row ?: array('error' => 'Not found'), $row ? 200 : 404);
        }
        $body = $this->input();
        if ($this->request->server['REQUEST_METHOD'] === 'DELETE') {
            $this->model_extension_module_ultra_opencart_api->deleteProduct($id);
            return $this->json(array('ok' => true));
        }
        $this->model_extension_module_ultra_opencart_api->updateProduct($id, $body);
        $this->json(array('ok' => true, 'product_id' => $id));
    }

    public function createProduct() {
        if (!$this->authorize()) return;
        if ($this->request->server['REQUEST_METHOD'] !== 'POST') return $this->json(array('error' => 'POST required'), 405);
        $this->load->model('extension/module/ultra_opencart_api');
        $id = $this->model_extension_module_ultra_opencart_api->createProduct($this->input());
        $this->json(array('ok' => true, 'product_id' => $id), 201);
    }

    public function categories() {
        if (!$this->authorize()) return;
        $this->load->model('extension/module/ultra_opencart_api');
        $limit = isset($this->request->get['limit']) ? min(500, max(1, (int)$this->request->get['limit'])) : 100;
        $offset = isset($this->request->get['offset']) ? max(0, (int)$this->request->get['offset']) : 0;
        $this->json(array('data' => $this->model_extension_module_ultra_opencart_api->getCategories($limit, $offset)));
    }

    public function category() {
        if (!$this->authorize()) return;
        $this->load->model('extension/module/ultra_opencart_api');
        $id = isset($this->request->get['category_id']) ? (int)$this->request->get['category_id'] : 0;
        if (!$id) return $this->json(array('error' => 'category_id is required'), 400);
        if ($this->request->server['REQUEST_METHOD'] === 'GET') {
            $row = $this->model_extension_module_ultra_opencart_api->getCategory($id);
            return $this->json($row ?: array('error' => 'Not found'), $row ? 200 : 404);
        }
        if ($this->request->server['REQUEST_METHOD'] === 'DELETE') {
            $this->model_extension_module_ultra_opencart_api->deleteCategory($id);
            return $this->json(array('ok' => true));
        }
        $this->model_extension_module_ultra_opencart_api->updateCategory($id, $this->input());
        $this->json(array('ok' => true, 'category_id' => $id));
    }

    public function createCategory() {
        if (!$this->authorize()) return;
        if ($this->request->server['REQUEST_METHOD'] !== 'POST') return $this->json(array('error' => 'POST required'), 405);
        $this->load->model('extension/module/ultra_opencart_api');
        $id = $this->model_extension_module_ultra_opencart_api->createCategory($this->input());
        $this->json(array('ok' => true, 'category_id' => $id), 201);
    }

    public function bulkStockPrice() {
        if (!$this->authorize()) return;
        if ($this->request->server['REQUEST_METHOD'] !== 'POST') return $this->json(array('error' => 'POST required'), 405);
        $this->load->model('extension/module/ultra_opencart_api');
        $body = $this->input();
        $count = $this->model_extension_module_ultra_opencart_api->bulkStockPrice($body);
        $this->json(array('ok' => true, 'updated' => $count));
    }

    private function authorize() {
        if (!$this->config->get('module_ultra_opencart_status')) return $this->json(array('error' => 'Module disabled'), 503, false);
        $expected = (string)$this->config->get('module_ultra_opencart_api_key');
        $provided = '';
        if (isset($this->request->server['HTTP_X_ULTRA_API_KEY'])) $provided = $this->request->server['HTTP_X_ULTRA_API_KEY'];
        if (!$provided && isset($this->request->server['HTTP_AUTHORIZATION']) && preg_match('/Bearer\s+(.+)/i', $this->request->server['HTTP_AUTHORIZATION'], $m)) $provided = trim($m[1]);
        if (!$provided && isset($this->request->get['api_key'])) $provided = $this->request->get['api_key'];
        if (!$expected || !$provided || !hash_equals($expected, $provided)) return $this->json(array('error' => 'Unauthorized'), 401, false);
        return true;
    }

    private function input() {
        $raw = file_get_contents('php://input');
        $data = json_decode($raw, true);
        return is_array($data) ? $data : array();
    }

    private function json($data, $status = 200, $log = true) {
        if ($log) {
            $this->db->query("INSERT INTO `" . DB_PREFIX . "ultra_opencart_log` SET method = '" . $this->db->escape($this->request->server['REQUEST_METHOD']) . "', route = '" . $this->db->escape(isset($this->request->get['route']) ? $this->request->get['route'] : '') . "', status_code = " . (int)$status . ", created_at = NOW()");
        }
        http_response_code($status);
        $this->response->addHeader('Content-Type: application/json; charset=utf-8');
        $this->response->setOutput(json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
        return false;
    }
}
