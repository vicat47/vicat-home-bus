from __future__ import annotations

import httpx

from homebus.adapters.base import ActionMeta, AdapterBase


class HomeboxAdapter(AdapterBase):

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def execute(self, action: str, params: dict) -> dict:
        if action == "create_asset":
            return await self._create_asset(params)
        elif action == "delete_asset":
            return await self._delete_asset(params)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    async def _create_asset(self, params: dict) -> dict:
        client = await self._get_client()
        payload = {
            "name": params.get("name", ""),
            "category": params.get("category", ""),
            "location": params.get("location", ""),
            "price": params.get("price", 0),
            "purchasedAt": params.get("purchased_at"),
            "notes": params.get("note", ""),
        }

        try:
            resp = await client.post(
                f"{self.base_url}/api/v1/items", json=payload
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "success": True,
                    "data": {
                        "asset_id": data.get("id", ""),
                        "name": data.get("name", params.get("name")),
                    },
                }
            return {
                "success": False,
                "error": f"Homebox create_asset 失败: HTTP {resp.status_code}",
            }
        except httpx.TimeoutException:
            return {"success": False, "error": "Homebox API 超时"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Homebox API 不可达: {e}"}

    async def _delete_asset(self, params: dict) -> dict:
        asset_id = params.get("asset_id", "")
        client = await self._get_client()

        try:
            resp = await client.delete(
                f"{self.base_url}/api/v1/items/{asset_id}"
            )
            if resp.status_code in (200, 204):
                return {"success": True, "data": {"deleted": True}}
            if resp.status_code == 404:
                return {
                    "success": True,
                    "data": {
                        "deleted": False,
                        "note": "asset already deleted",
                    },
                }
            return {
                "success": False,
                "error": f"Homebox delete_asset 失败: HTTP {resp.status_code}",
            }
        except httpx.TimeoutException:
            return {"success": False, "error": "Homebox API 超时"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"Homebox API 不可达: {e}"}

    async def health_check(self) -> dict:
        client = await self._get_client()
        try:
            resp = await client.get(
                f"{self.base_url}/api/v1/status", timeout=5.0
            )
            if resp.status_code == 200:
                return {"healthy": True, "detail": "ok"}
            return {"healthy": False, "detail": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"healthy": False, "detail": str(e)}

    def list_actions(self) -> list[ActionMeta]:
        return [
            ActionMeta(
                name="create_asset",
                description="创建资产记录",
                params_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "category": {"type": "string"},
                        "location": {"type": "string"},
                        "price": {"type": "number"},
                        "purchased_at": {"type": "string"},
                        "note": {"type": "string"},
                    },
                    "required": ["name"],
                },
                returns_schema={"type": "object"},
            ),
            ActionMeta(
                name="delete_asset",
                description="删除资产（补偿）",
                params_schema={
                    "type": "object",
                    "properties": {"asset_id": {"type": "string"}},
                    "required": ["asset_id"],
                },
                returns_schema={"type": "object"},
            ),
        ]

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
