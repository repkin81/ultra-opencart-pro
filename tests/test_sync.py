from app.sync.service import canonical_checksum


def test_checksum_is_deterministic_for_dict_order():
    assert canonical_checksum({"name": "Xerox", "model": "Versant 80"}) == canonical_checksum(
        {"model": "Versant 80", "name": "Xerox"}
    )


def test_checksum_changes_when_payload_changes():
    assert canonical_checksum({"name": "Xerox"}) != canonical_checksum({"name": "Xerox", "price": 100})
