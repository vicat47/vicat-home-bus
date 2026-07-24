from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CategoryRoute:
    default_grocy_location: str = ""
    default_beancount_account: str = ""
    default_homebox_location: str = ""
    homebox_enabled: bool = False


@dataclass
class StoreRoute:
    beancount_liability: str = "Liabilities:Unknown"


@dataclass
class Registry:
    categories: dict[str, CategoryRoute] = field(default_factory=dict)
    stores: dict[str, StoreRoute] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | None = None) -> Registry:
        if path is None:
            xdg_config = os.environ.get(
                "XDG_CONFIG_HOME",
                os.path.join(os.path.expanduser("~"), ".config"),
            )
            path = os.path.join(xdg_config, "homebus", "registry.toml")

        registry_path = Path(path)
        if not registry_path.exists():
            return cls()

        try:
            with open(registry_path, "rb") as f:
                data = tomllib.load(f)
        except (tomllib.TOMLDecodeError, OSError):
            return cls()

        routing = data.get("routing", {})

        categories: dict[str, CategoryRoute] = {}
        cats_section = routing.get("categories", {})
        for name, cfg in cats_section.items():
            categories[name] = CategoryRoute(
                default_grocy_location=cfg.get("default_grocy_location", ""),
                default_beancount_account=cfg.get("default_beancount_account", ""),
                default_homebox_location=cfg.get("default_homebox_location", ""),
                homebox_enabled=cfg.get("homebox_enabled", False),
            )

        stores: dict[str, StoreRoute] = {}
        stores_section = routing.get("stores", {})
        for name, cfg in stores_section.items():
            stores[name] = StoreRoute(
                beancount_liability=cfg.get(
                    "beancount_liability", "Liabilities:Unknown"
                ),
            )

        return cls(categories=categories, stores=stores)

    def get_category_route(self, category: str) -> CategoryRoute:
        return self.categories.get(category, CategoryRoute())

    def get_store_route(self, store: str) -> StoreRoute | None:
        if store is None:
            return None
        return self.stores.get(store)
