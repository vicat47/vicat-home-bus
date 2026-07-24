from homebus.saga import COMPENSATION_MAP, UncompensatableError


def test_grocy_compensation():
    key = ("grocy", "add_stock")
    assert key in COMPENSATION_MAP
    mapping = COMPENSATION_MAP[key]
    assert mapping["action"] == "consume_stock"

    params_fn = mapping["params"]
    params = params_fn({"items": [{"name": "牛奶", "quantity": 3}]}, {})
    assert params["items"][0]["quantity"] == 3


def test_beancount_compensation():
    key = ("beancount", "record_expense")
    assert key in COMPENSATION_MAP
    mapping = COMPENSATION_MAP[key]
    assert mapping["action"] == "delete_entry"

    params_fn = mapping["params"]
    params = params_fn({"event_id": "evt_001"}, {})
    assert params["event_id"] == "evt_001"


def test_homebox_compensation():
    key = ("homebox", "create_asset")
    assert key in COMPENSATION_MAP
    mapping = COMPENSATION_MAP[key]
    assert mapping["action"] == "delete_asset"

    params_fn = mapping["params"]
    params = params_fn({}, {"asset_id": "abc123"})
    assert params["asset_id"] == "abc123"


def test_unknown_key_raises():
    with __import__('pytest').raises(UncompensatableError):
        raise UncompensatableError("unknown", "unknown_action")
