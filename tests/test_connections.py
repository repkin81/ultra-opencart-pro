from app.sync.connection_models import OpenCartConnection
from app.sync.connection_schemas import ConnectionCreate, ConnectionUpdate


def test_connection_create_defaults_and_secret_is_not_in_output():
    data = ConnectionCreate(name="Store", base_url="https://shop.example.com", api_key="secret")
    assert data.timeout == 30
    assert data.interval_seconds == 60
    assert data.page_size == 100

    connection = OpenCartConnection(
        id=1,
        name=data.name,
        base_url=str(data.base_url),
        api_key=data.api_key,
        timeout=data.timeout,
        enabled=data.enabled,
        interval_seconds=data.interval_seconds,
        page_size=data.page_size,
    )
    assert not hasattr(connection, "has_api_key")
    assert connection.api_key == "secret"


def test_connection_update_allows_partial_changes():
    data = ConnectionUpdate(enabled=False, interval_seconds=300)
    values = data.model_dump(exclude_unset=True)
    assert values == {"enabled": False, "interval_seconds": 300}
