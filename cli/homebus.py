from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import click
import httpx

API_URL_DEFAULT = "http://localhost:8080"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "homebus"


def _get_api_url(api_url_override: str | None = None) -> str:
    if api_url_override:
        return api_url_override
    env_url = os.environ.get("HOMEBUS_CLI_URL")
    if env_url:
        return env_url
    config_path = CONFIG_DIR / "config.toml"
    if config_path.exists():
        try:
            import tomllib
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
            cli_url = data.get("cli", {}).get("api_url")
            if cli_url:
                return cli_url
        except Exception:
            pass
    return API_URL_DEFAULT


def _output_json(data: dict) -> None:
    click.echo(json.dumps(data, ensure_ascii=False))


def _output_error(message: str, exit_code: int = 1) -> None:
    click.echo(f"Error: {message}", err=True)
    sys.exit(exit_code)


@click.group()
def cli():
    """HomeBus — 家庭服务总线 CLI"""


@cli.command()
@click.option("--body", type=str, help="Event JSON string")
@click.option("--file", "file_path", type=click.Path(exists=True), help="Path to event JSON file")
@click.option("--api-url", type=str, help="API Server URL")
def publish(body: str | None, file_path: str | None, api_url: str | None) -> None:
    """Submit an event to HomeBus."""
    if not body and not file_path:
        _output_error("必须提供 --body 或 --file 参数")

    if body and file_path:
        _output_error("--body 和 --file 不能同时使用")

    if file_path:
        try:
            body = Path(file_path).read_text(encoding="utf-8")
        except Exception as e:
            _output_error(f"无法读取文件: {e}")

    api = _get_api_url(api_url)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        _output_error("无效的 JSON 参数")

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{api}/v1/events", json=payload)
            if resp.status_code in (200, 201):
                _output_json(resp.json())
            else:
                error_data = resp.json()
                err = error_data.get("error", {})
                _output_error(f"{err.get('code', 'UNKNOWN')} — {err.get('message', resp.text)}")
    except httpx.ConnectError:
        _output_error(f"无法连接到 HomeBus API ({api})")
    except httpx.RequestError as e:
        _output_error(f"请求失败: {e}")


@cli.command()
@click.option("--event-id", required=True, type=str, help="Event ID")
@click.option("--watch", is_flag=True, help="Poll until terminal state")
@click.option("--timeout", type=int, default=60, help="Watch timeout in seconds (default: 60)")
@click.option("--api-url", type=str, help="API Server URL")
def status(event_id: str, watch: bool, timeout: int, api_url: str | None) -> None:
    """Query event execution status."""
    api = _get_api_url(api_url)

    try:
        with httpx.Client(timeout=30.0) as client:
            if watch:
                deadline = time.time() + timeout
                while time.time() < deadline:
                    resp = client.get(f"{api}/v1/events/{event_id}")
                    if resp.status_code != 200:
                        _output_error(f"查询失败: HTTP {resp.status_code}")
                    data = resp.json()
                    if data.get("status") in ("success", "compensated", "failed"):
                        _output_json(data)
                        return
                    time.sleep(0.5)
                _output_error(f"事件 {event_id} 在 {timeout}s 内未达到终态")
            else:
                resp = client.get(f"{api}/v1/events/{event_id}")
                if resp.status_code == 200:
                    _output_json(resp.json())
                else:
                    error_data = resp.json()
                    err = error_data.get("error", {})
                    _output_error(f"{err.get('code', 'UNKNOWN')} — {err.get('message', resp.text)}")
    except httpx.ConnectError:
        _output_error(f"无法连接到 HomeBus API ({api})")


@cli.command()
@click.option("--target", required=True, type=click.Choice(["grocy", "beancount", "homebox"]),
              help="Target backend")
@click.option("--operation", required=True, type=str, help="Operation name")
@click.option("--params", required=True, type=str, help="Query parameters as JSON")
@click.option("--api-url", type=str, help="API Server URL")
def query(target: str, operation: str, params: str, api_url: str | None) -> None:
    """Query a backend through HomeBus."""
    api = _get_api_url(api_url)

    try:
        params_dict = json.loads(params)
    except json.JSONDecodeError:
        _output_error("无效的 --params JSON")

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{api}/v1/query", json={
                "target": target,
                "operation": operation,
                "params": params_dict,
            })
            if resp.status_code == 200:
                _output_json(resp.json())
            else:
                error_data = resp.json()
                err = error_data.get("error", {})
                _output_error(f"{err.get('code', 'UNKNOWN')} — {err.get('message', resp.text)}")
    except httpx.ConnectError:
        _output_error(f"无法连接到 HomeBus API ({api})")


@cli.command()
@click.option("--api-url", type=str, help="API Server URL")
def health(api_url: str | None) -> None:
    """Check HomeBus and adapter health."""
    api = _get_api_url(api_url)

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(f"{api}/v1/health")
            _output_json(resp.json())
    except httpx.ConnectError:
        _output_error(f"无法连接到 HomeBus API ({api})")


@cli.command()
@click.option("--force", is_flag=True, help="Overwrite existing config files")
def init(force: bool) -> None:
    """Initialize HomeBus configuration files."""
    config_dir = CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)

    config_toml = config_dir / "config.toml"
    registry_toml = config_dir / "registry.toml"
    env_example = config_dir / ".env.example"

    config_content = """# HomeBus 主配置文件
# 优先级: TOML < 环境变量 < CLI 参数
# 敏感信息 (API Key / Token) 通过环境变量注入，不出现在此文件

[homebus.api]
host = "0.0.0.0"
port = 8080
debug = false

[homebus.database]
path = "~/.local/share/homebus/data.db"

[homebus.logging]
level = "info"
format = "json"

[adapters.grocy]
base_url = "http://localhost:9283"

[adapters.beancount]
mode = "fava"
ledger_path = "~/ledger"
fava_url = "http://localhost:5000"

[adapters.homebox]
base_url = "http://localhost:7745"

[cli]
api_url = "http://localhost:8080"
timeout = 30
"""

    registry_content = """# HomeBus 路由注册表
# 编辑后重启 HomeBus 生效

[routing.categories]

[routing.categories.consumable]
default_grocy_location = ""
default_beancount_account = "Expenses:Food:Groceries"
homebox_enabled = false

[routing.categories.durable]
default_grocy_location = ""
default_beancount_account = "Expenses:Home:Appliances"
default_homebox_location = ""
homebox_enabled = true

[routing.stores]
# [routing.stores.JD]
# beancount_liability = "Liabilities:CreditCard:JD"
# 在下方按需取消注释并修改
"""

    env_content = """# HomeBus 敏感环境变量
# 从不超过 git，通过 env_file 加载

GROCY_API_KEY=xxx
HOMEBOX_TOKEN=xxx
"""

    files = {
        config_toml: config_content,
        registry_toml: registry_content,
        env_example: env_content,
    }

    for filepath, content in files.items():
        if filepath.exists() and not force:
            click.echo(f"跳过已存在: {filepath}")
            continue
        filepath.write_text(content, encoding="utf-8")
        click.echo(f"已创建: {filepath}")

    click.echo("\n初始化完成。请编辑配置文件后重启 HomeBus。")


def main():
    cli()


if __name__ == "__main__":
    main()
