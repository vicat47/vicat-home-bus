from __future__ import annotations

from homebus.models import CreateEventRequest, SubTask
from homebus.registry import Registry


class DispatchEngine:

    def __init__(self, registry: Registry):
        self.registry = registry

    def derive_subtasks(self, event: CreateEventRequest) -> list[SubTask]:
        if event.intent == "purchase":
            return self._derive_purchase(event)
        elif event.intent == "consume":
            return self._derive_consume(event)
        else:
            return []

    def _derive_purchase(self, event: CreateEventRequest) -> list[SubTask]:
        subtasks: list[SubTask] = []

        consumables = [i for i in event.items if i.category == "consumable"]
        durables = [i for i in event.items if i.category == "durable"]

        if not consumables and not durables:
            return []

        cat_route = self.registry.get_category_route(
            event.items[0].category
        )
        store_route = None
        if event.store:
            store_route = self.registry.get_store_route(event.store)

        grocy_items = []
        beancount_items = []
        homebox_items = []

        for item in event.items:
            item_dict = item.model_dump()
            beancount_items.append(item_dict)

            grocy_items.append({
                "name": item.name,
                "quantity": item.quantity,
                "unit": item.unit,
                "grocy_product_id": item.grocy_product_id,
                "price": item.price,
            })

            if item.category == "durable":
                item_route = self.registry.get_category_route("durable")
                homebox_items.append({
                    "name": item.name,
                    "category": "durable",
                    "location": item_route.default_homebox_location,
                    "price": item.price,
                    "quantity": item.quantity,
                    "purchased_at": (
                        event.purchased_at.isoformat()
                        if event.purchased_at else None
                    ),
                    "note": event.note,
                })

        seq = 0

        if grocy_items:
            location = cat_route.default_grocy_location
            subtasks.append(SubTask(
                seq=seq,
                service="grocy",
                action="add_stock",
                params={"items": grocy_items, "location": location},
                depends_on=[],
            ))
            grocy_seq = seq
            seq += 1
        else:
            grocy_seq = None

        beancount_deps = [grocy_seq] if grocy_seq is not None else []

        total_price = event.total_price or sum(
            i.price * i.quantity for i in event.items
        )

        subtasks.append(SubTask(
            seq=seq,
            service="beancount",
            action="record_expense",
            params={
                "event_id": event.event_id or "",
                "date": (
                    event.purchased_at.strftime("%Y-%m-%d")
                    if event.purchased_at else None
                ),
                "items": beancount_items,
                "total_price": total_price,
                "store": event.store,
                "account": cat_route.default_beancount_account or "Expenses:Unknown",
                "liability": (
                    store_route.beancount_liability
                    if store_route else None
                ),
                "note": event.note,
            },
            depends_on=beancount_deps,
        ))
        seq += 1

        if homebox_items:
            subtasks.append(SubTask(
                seq=seq,
                service="homebox",
                action="create_asset",
                params={"items": homebox_items},
                depends_on=beancount_deps,
            ))
            seq += 1

        return subtasks

    def _derive_consume(self, event: CreateEventRequest) -> list[SubTask]:
        grocy_items = []
        for item in event.items:
            grocy_items.append({
                "name": item.name,
                "quantity": item.quantity,
                "unit": item.unit,
                "grocy_product_id": item.grocy_product_id,
            })

        return [
            SubTask(
                seq=0,
                service="grocy",
                action="consume_stock",
                params={"items": grocy_items},
                depends_on=[],
            )
        ]
