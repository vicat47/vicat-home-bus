from homebus.dispatch import DispatchEngine
from homebus.models import CreateEventRequest, SubTask
from homebus.registry import CategoryRoute, Registry, StoreRoute


def _make_registry() -> Registry:
    return Registry(
        categories={
            "consumable": CategoryRoute(
                default_grocy_location="厨房",
                default_beancount_account="Expenses:Food:Groceries",
                homebox_enabled=False,
            ),
            "durable": CategoryRoute(
                default_grocy_location="客厅",
                default_beancount_account="Expenses:Home:Appliances",
                default_homebox_location="客厅",
                homebox_enabled=True,
            ),
        },
        stores={
            "京东": StoreRoute(beancount_liability="Liabilities:CreditCard:JD"),
        },
    )


def test_derive_purchase_consumable():
    registry = _make_registry()
    engine = DispatchEngine(registry)

    event = CreateEventRequest(
        intent="purchase",
        items=[{"name": "牛奶", "category": "consumable", "quantity": 3, "unit": "盒", "price": 20.0}],
        total_price=60.0,
        store="京东",
    )
    subtasks = engine.derive_subtasks(event)
    assert len(subtasks) == 2

    grocy = subtasks[0]
    assert grocy.service == "grocy"
    assert grocy.action == "add_stock"
    assert grocy.depends_on == []

    bc = subtasks[1]
    assert bc.service == "beancount"
    assert bc.action == "record_expense"
    assert bc.depends_on == [0]
    assert bc.params["account"] == "Expenses:Food:Groceries"
    assert bc.params["liability"] == "Liabilities:CreditCard:JD"


def test_derive_purchase_durable():
    registry = _make_registry()
    engine = DispatchEngine(registry)

    event = CreateEventRequest(
        intent="purchase",
        items=[{"name": "洗衣机", "category": "durable", "quantity": 1, "unit": "台", "price": 3000.0}],
        total_price=3000.0,
        store="京东",
    )
    subtasks = engine.derive_subtasks(event)
    assert len(subtasks) == 3

    assert subtasks[0].service == "grocy"
    assert subtasks[1].service == "beancount"
    assert subtasks[2].service == "homebox"
    assert subtasks[2].action == "create_asset"


def test_derive_purchase_mixed():
    registry = _make_registry()
    engine = DispatchEngine(registry)

    event = CreateEventRequest(
        intent="purchase",
        items=[
            {"name": "牛奶", "category": "consumable", "quantity": 3, "unit": "盒", "price": 20.0},
            {"name": "洗衣机", "category": "durable", "quantity": 1, "unit": "台", "price": 3000.0},
        ],
        total_price=3060.0,
        store="京东",
    )
    subtasks = engine.derive_subtasks(event)
    assert len(subtasks) == 3


def test_derive_consume():
    registry = Registry()
    engine = DispatchEngine(registry)

    event = CreateEventRequest(
        intent="consume",
        items=[{"name": "牛奶", "quantity": 1, "unit": "盒"}],
    )
    subtasks = engine.derive_subtasks(event)
    assert len(subtasks) == 1
    assert subtasks[0].service == "grocy"
    assert subtasks[0].action == "consume_stock"
    assert subtasks[0].depends_on == []
