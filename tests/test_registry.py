import tempfile
from pathlib import Path

from homebus.registry import CategoryRoute, Registry, StoreRoute


def test_load_empty_registry():
    with tempfile.NamedTemporaryFile(suffix=".toml", mode="w", delete=False) as f:
        f.write("")
        path = f.name

    registry = Registry.load(path)
    assert registry.categories == {}
    assert registry.stores == {}
    Path(path).unlink()


def test_load_with_categories():
    content = """[routing.categories.consumable]
default_grocy_location = "厨房"
default_beancount_account = "Expenses:Food:Groceries"
homebox_enabled = false

[routing.categories.durable]
default_grocy_location = "客厅"
default_beancount_account = "Expenses:Home:Appliances"
homebox_enabled = true
"""
    with tempfile.NamedTemporaryFile(suffix=".toml", mode="w", delete=False) as f:
        f.write(content)
        path = f.name

    registry = Registry.load(path)
    assert "consumable" in registry.categories
    assert "durable" in registry.categories

    cat = registry.get_category_route("consumable")
    assert cat.default_grocy_location == "厨房"
    assert cat.default_beancount_account == "Expenses:Food:Groceries"
    assert cat.homebox_enabled is False

    Path(path).unlink()


def test_load_with_stores():
    content = """[routing.stores]
JD = { beancount_liability = "Liabilities:CreditCard:JD" }
"""
    with tempfile.NamedTemporaryFile(suffix=".toml", mode="w", delete=False) as f:
        f.write(content)
        path = f.name

    registry = Registry.load(path)
    store = registry.get_store_route("JD")
    assert store is not None
    assert store.beancount_liability == "Liabilities:CreditCard:JD"

    unknown = registry.get_store_route("unknown")
    assert unknown is None

    Path(path).unlink()


def test_get_category_route_default():
    registry = Registry()
    cat = registry.get_category_route("nonexistent")
    assert cat.default_grocy_location == ""
    assert cat.default_beancount_account == ""
    assert cat.homebox_enabled is False


def test_get_store_route_none():
    registry = Registry()
    assert registry.get_store_route(None) is None


def test_missing_file_returns_empty():
    registry = Registry.load("/non/existent/path.toml")
    assert registry.categories == {}
    assert registry.stores == {}
