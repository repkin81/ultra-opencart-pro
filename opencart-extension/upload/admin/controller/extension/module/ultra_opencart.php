<?php
class ControllerExtensionModuleUltraOpenCart extends Controller {
    private $error = array();

    public function index() {
        $this->load->language('extension/module/ultra_opencart');
        $this->document->setTitle($this->language->get('heading_title'));

        if (($this->request->server['REQUEST_METHOD'] == 'POST') && $this->validate()) {
            $this->load->model('setting/setting');
            $this->model_setting_setting->editSetting('module_ultra_opencart', $this->request->post);
            $this->session->data['success'] = $this->language->get('text_success');
            $this->response->redirect($this->url->link('extension/extension', 'user_token=' . $this->session->data['user_token'] . '&type=module', true));
        }

        $data['heading_title'] = $this->language->get('heading_title');
        $data['text_edit'] = $this->language->get('text_edit');
        $data['entry_status'] = $this->language->get('entry_status');
        $data['entry_api_key'] = $this->language->get('entry_api_key');
        $data['entry_log_limit'] = $this->language->get('entry_log_limit');
        $data['help_api_key'] = $this->language->get('help_api_key');
        $data['button_save'] = $this->language->get('button_save');
        $data['button_cancel'] = $this->language->get('button_cancel');

        $data['error_warning'] = isset($this->error['warning']) ? $this->error['warning'] : '';
        $data['success'] = isset($this->session->data['success']) ? $this->session->data['success'] : '';
        unset($this->session->data['success']);

        $data['action'] = $this->url->link('extension/module/ultra_opencart', 'user_token=' . $this->session->data['user_token'], true);
        $data['cancel'] = $this->url->link('extension/extension', 'user_token=' . $this->session->data['user_token'] . '&type=module', true);
        $data['module_ultra_opencart_status'] = isset($this->request->post['module_ultra_opencart_status']) ? $this->request->post['module_ultra_opencart_status'] : $this->config->get('module_ultra_opencart_status');
        $data['module_ultra_opencart_api_key'] = isset($this->request->post['module_ultra_opencart_api_key']) ? $this->request->post['module_ultra_opencart_api_key'] : $this->config->get('module_ultra_opencart_api_key');
        $data['module_ultra_opencart_log_limit'] = isset($this->request->post['module_ultra_opencart_log_limit']) ? $this->request->post['module_ultra_opencart_log_limit'] : ($this->config->get('module_ultra_opencart_log_limit') ?: 100);
        $data['api_endpoint'] = HTTPS_CATALOG . 'index.php?route=extension/module/ultra_opencart_api';

        $data['header'] = $this->load->controller('common/header');
        $data['column_left'] = $this->load->controller('common/column_left');
        $data['footer'] = $this->load->controller('common/footer');
        $this->response->setOutput($this->load->view('extension/module/ultra_opencart', $data));
    }

    protected function validate() {
        if (!$this->user->hasPermission('modify', 'extension/module/ultra_opencart')) {
            $this->error['warning'] = $this->language->get('error_permission');
        }
        if (empty($this->request->post['module_ultra_opencart_api_key']) || strlen($this->request->post['module_ultra_opencart_api_key']) < 32) {
            $this->error['warning'] = $this->language->get('error_api_key');
        }
        return !$this->error;
    }

    public function install() {
        if (!$this->user->hasPermission('modify', 'extension/extension')) return;
        $this->load->model('setting/setting');
        $key = bin2hex(function_exists('random_bytes') ? random_bytes(32) : openssl_random_pseudo_bytes(32));
        $this->model_setting_setting->editSetting('module_ultra_opencart', array(
            'module_ultra_opencart_status' => 1,
            'module_ultra_opencart_api_key' => $key,
            'module_ultra_opencart_log_limit' => 100
        ));
        $this->db->query("CREATE TABLE IF NOT EXISTS `" . DB_PREFIX . "ultra_opencart_log` (`id` int(11) NOT NULL AUTO_INCREMENT, `method` varchar(10) NOT NULL, `route` varchar(255) NOT NULL, `status_code` int(11) NOT NULL DEFAULT 200, `created_at` datetime NOT NULL, PRIMARY KEY (`id`), KEY `created_at` (`created_at`)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");
    }

    public function uninstall() {
        if (!$this->user->hasPermission('modify', 'extension/extension')) return;
        $this->load->model('setting/setting');
        $this->model_setting_setting->deleteSetting('module_ultra_opencart');
        $this->db->query("DROP TABLE IF EXISTS `" . DB_PREFIX . "ultra_opencart_log`");
    }
}
