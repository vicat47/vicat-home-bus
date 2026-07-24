from __future__ import annotations

import os
from pathlib import Path

import httpx
import yaml

from homebus.adapters.base import ActionMeta, AdapterBase

_GROCY_CACHE_PATH = Path(
    os.environ.get(
        "GROCY_CACHE_PATH",
        os.path.join(os.path.expanduser("~"), ".config", "grocy", "cache.yaml"),
    )
)


def _load_cache() -> dict:
    if not _GROCY_CACHE_PATH.exists():
        return {"products": {}}
    with open(_GROCY_CACHE_PATH, "r") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {"products": {}}
    return data


def _save_cache(cache: dict) -> None:
    _GROCY_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_GROCY_CACHE_PATH, "w") as f:
        yaml.safe_dump(cache, f, allow_unicode=True)


class GrocyAdapter(AdapterBase):

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "GROCY-API-KEY": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def _resolve_product_id(self, name: str) -> tuple[int | None, str | None]:
        cache = _load_cache()
        products_cache = cache.get("products", {})

        if name in products_cache:
            return products_cache[name], None

        client = await self._get_client()
        try:
            resp = await client.get(
                f"{self.base_url}/api/objects/products",
                params={"query": name},
            )
            if resp.status_code == 200:
                products = resp.json()
                for p in products:
                    if p.get("name") == name:
                        pid = p["id"]
                        products_cache[name] = pid
                        cache["products"] = products_cache
                        _save_cache(cache)
                        return pid, None

            return None, f"产品'{name}'在 Grocy 中不存在"
        except httpx.TimeoutException:
            return None, f"Grocy API 超时: {self.base_url}"
        except httpx.RequestError as e:
            return None, f"Grocy API 不可达: {e}"

    async def _resolve_product_ids(
        self, items: list[dict]
    ) -> tuple[list[dict], str | None]:
        resolved = []
        for item in items:
            name = item.get("name", "")
            if item.get("grocy_product_id"):
                resolved.append({**item, "product_id": item["grocy_product_id"]})
                continue

            pid, error = await self._resolve_product_id(name)
            if pid is None:
                return [], error
            resolved.append({**item, "product_id": pid})
        return resolved, None

    async def execute(self, action: str, params: dict) -> dict:
        if action == "add_stock":
            return await self._add_stock(params)
        elif action == "consume_stock":
            return await self._consume_stock(params)
        elif action == "stock_query":
            return await self._stock_query(params)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def _add_stock(self, params: dict) -> dict:
        items = params.get("items", [])
        resolved_items, error = await self._resolve_product_ids(items)
        if error:
            return {"success": False, "error": error}

        client = await self._get_client()
        added = []

        for item, resolved in zip(items, resolved_items):
            payload = {
                "product_id": resolved["product_id"],
                "amount": item.get("quantity", 1),
                "transaction_type": "purchase",
                "price": item.get("price"),
            }
            location = params.get("location") or item.get("location")
            if location:
                payload["location_name"] = location

            try:
                resp = await client.post(
                    f"{self.base_url}/api/stock/products/{resolved['product_id']}/add",
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    added.append({
                        "name": item["name"],
                        "product_id": resolved["product_id"],
                        "quantity": item.get("quantity", 1),
                    })
                else:
                    return {
                        "success": False,
                        "error": f"Grocy add_stock 失败: HTTP {resp.status_code}",
                    }
            except httpx.TimeoutException:
                return {"success": False, "error": "Grocy API 超时"}
            except httpx.RequestError as e:
                return {"success": False, "error": f"Grocy API 不可达: {e}"}

        return {"success": True, "data": {"added": added}}

    async def _consume_stock(self, params: dict) -> dict:
        items = params.get("items", [])
        resolved_items, error = await self._resolve_product_ids(items)
        if error:
            return {"success": False, "error": error}

        client = await self._get_client()

        for item, resolved in zip(items, resolved_items):
            payload = {
                "product_id": resolved["product_id"],
                "amount": abs(item.get("quantity", 1)),
                "transaction_type": "consume",
            }
            try:
                resp = await client.post(
                    f"{self.base_url}/api/stock/products/{resolved['product_id']}/consume",
                    json=payload,
                )
                if resp.status_code not in (200, 201):
                    return {
                        "success": False,
                        "error": f"Grocy consume_stock 失败: HTTP {resp.status_code}",
                    }
            except httpx.TimeoutException:
                return {"success": False, "error": "Grocy API 超时"}
            except httpx.RequestError as e:
                return {"success": False, "error": f"Grocy API 不可达: {e}"}

        return {"success": True, "data": {"consumed": True}}

    async def _stock_query(self, params: dict) -> dict:
        product_name = params.get("product_name", "")
        product_id = params.get("product_id")

        if product_id is None:
            pid, error = await self._resolve_product_id(product_name)
            if pid is None:
                return {"success": False, "error": error}
            product_id = pid

        client = await self._get_client()
        try:
            resp = await client.get(
                f"{self.base_url}/api/stock/products/{product_id}",
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "data": {
                        "product_name": data.get("product", {}).get("name", product_name),
                        "product_id": product_id,
                        "stock": data.get("stock_amount", 0),
                        "unit": data.get("product", {}).get("qu_name_purchase", ""),
                    },
                }
            return {
                "success": False,
                "error": f"Grocy stock_query 失败: HTTP {resp.status_code}",
            }
        except httpx.TimeoutException:
            return {"success": False, "error": "Grocy API 超时"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Grocy API 不可达: {e}"}

    async def health_check(self) -> dict:
        client = await self._get_client()
        try:
            resp = await client.get(
                f"{self.base_url}/api/system/info", timeout=5.0
            )
            if resp.status_code == 200:
                return {"healthy": True, "detail": "ok"}
            return {"healthy": False, "detail": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"healthy": False, "detail": str(e)}

    def list_actions(self) -> list[ActionMeta]:
        return [
            ActionMeta(
                name="add_stock",
                description="增加库存",
                params_schema={
                    "type": "object",
                    "properties": {
                        "items": {"type": "array"},
                        "location": {"type": "string"},
                    },
                    "required": ["items"],
                },
                returns_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {"type": "object"},
                    },
                },
            ),
            ActionMeta(
                name="consume_stock",
                description="消耗库存",
                params_schema={
                    "type": "object",
                    "properties": {
                        "items": {"type": "array"},
                    },
                    "required": ["items"],
                },
                returns_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {"type": "object"},
                    },
                },
            ),
            ActionMeta(
                name="stock_query",
                description="查询库存",
                params_schema={
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string"},
                        "product_id": {"type": "integer"},
                    },
                },
                returns_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {"type": "object"},
                    },
                },
            ),
        ]

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
