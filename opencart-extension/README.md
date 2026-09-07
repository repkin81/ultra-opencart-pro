# Ultra OpenCart PRO — OpenCart 3 connector

Настоящий модуль для OpenCart 3.x. Модуль устанавливается через админ-панель OpenCart как обычное расширение **Modules** и открывает защищённый JSON API для связи магазина с Python-ядром Ultra OpenCart PRO.

## Что умеет v0.1

- health-check;
- чтение товаров;
- создание/обновление/удаление товаров;
- чтение категорий;
- создание/обновление/удаление категорий;
- массовое изменение цены и остатка;
- API key с Bearer/X-Ultra-Api-Key;
- журнал последних API-вызовов в настройках модуля.

## Совместимость

Целевая версия: **OpenCart 3.x** (включая ocStore на базе OpenCart 3).

OpenCart 4 будет отдельным адаптером, потому что структура расширений и namespaces отличаются.

## Установка

1. Соберите ZIP из содержимого каталога `opencart-extension` так, чтобы внутри архива находился каталог `upload`.
2. В OpenCart: Extensions → Installer → Upload.
3. После загрузки: Extensions → Extensions → выберите `Modules`.
4. Установите `Ultra OpenCart PRO Connector`.
5. Откройте настройки модуля и включите его.
6. Скопируйте API key в конфигурацию Python-ядра.

API endpoint:

`/index.php?route=extension/module/ultra_opencart_api/health`

Авторизация:

`Authorization: Bearer <API_KEY>`

или

`X-Ultra-Api-Key: <API_KEY>`

## Важно

Не публикуйте API key в GitHub, JavaScript или HTML. Для production используйте HTTPS.
