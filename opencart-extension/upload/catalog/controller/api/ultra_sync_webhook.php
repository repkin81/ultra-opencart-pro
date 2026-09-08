<?php
class ControllerApiUltraSyncWebhook extends Controller {
    public function index() {
        $connection_id = (int)$this->request->get['connection_id'];
        $event_type = isset($this->request->post['event_type']) ? trim($this->request->post['event_type']) : '';
        $entity_type = isset($this->request->post['entity_type']) ? trim($this->request->post['entity_type']) : '';
        $entity_id = isset($this->request->post['entity_id']) ? trim((string)$this->request->post['entity_id']) : '';
        $payload = isset($this->request->post['payload']) && is_array($this->request->post['payload']) ? $this->request->post['payload'] : $this->request->post;

        if (!$connection_id || !$event_type || !$entity_type || !$entity_id) {
            $this->response->addHeader('HTTP/1.1 400 Bad Request');
            $this->response->setOutput(json_encode(array('error' => 'connection_id, event_type, entity_type and entity_id are required')));
            return;
        }

        $event_id = !empty($this->request->server['HTTP_X_SYNC_EVENT_ID']) ? $this->request->server['HTTP_X_SYNC_EVENT_ID'] : uniqid('oc_', true);
        $core_url = defined('ULTRA_SYNC_CORE_URL') ? rtrim(ULTRA_SYNC_CORE_URL, '/') : '';
        $api_key = defined('ULTRA_SYNC_CORE_API_KEY') ? ULTRA_SYNC_CORE_API_KEY : '';
        if (!$core_url || !$api_key) {
            $this->response->addHeader('HTTP/1.1 503 Service Unavailable');
            $this->response->setOutput(json_encode(array('error' => 'Sync Core is not configured')));
            return;
        }

        $body = json_encode(array(
            'event_id' => $event_id,
            'event_type' => $event_type,
            'entity_type' => $entity_type,
            'entity_id' => $entity_id,
            'payload' => $payload
        ));

        $ch = curl_init($core_url . '/sync/webhooks/' . $connection_id);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
        curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json', 'X-Sync-API-Key: ' . $api_key, 'X-Sync-Event-ID: ' . $event_id));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        $response = curl_exec($ch);
        $http_code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curl_error = curl_error($ch);
        curl_close($ch);

        if ($response === false || $http_code >= 500) {
            $this->response->addHeader('HTTP/1.1 502 Bad Gateway');
            $this->response->setOutput(json_encode(array('error' => $curl_error ?: 'Sync Core unavailable')));
            return;
        }

        $this->response->addHeader('Content-Type: application/json');
        $this->response->setOutput($response);
    }
}
