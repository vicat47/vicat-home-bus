from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(default=8080, ge=1024, le=65535)
    debug: bool = False


class DatabaseConfig(BaseModel):
    path: str = "~/.local/share/homebus/data.db"


class GrocyConfig(BaseModel):
    base_url: str = "http://localhost:9283"


class BeancountConfig(BaseModel):
    mode: str = "fava"
    ledger_path: str = "~/ledger"
    fava_url: str | None = "http://localhost:5000"


class HomeboxConfig(BaseModel):
    base_url: str = "http://localhost:7745"


class AdaptersConfig(BaseModel):
    grocy: GrocyConfig = Field(default_factory=GrocyConfig)
    beancount: BeancountConfig = Field(default_factory=BeancountConfig)
    homebox: HomeboxConfig = Field(default_factory=HomeboxConfig)


class CliConfig(BaseModel):
    api_url: str = "http://localhost:8080"
    timeout: float = 30.0


class HomeBusConfig(BaseModel):
    api: ApiConfig = Field(default_factory=ApiConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    adapters: AdaptersConfig = Field(default_factory=AdaptersConfig)
    cli: CliConfig = Field(default_factory=CliConfig)


def _expand_path(path: str) -> str:
    return os.path.expanduser(path)


def discover_config_path() -> Path:
    xdg_config_home = os.environ.get(
        "XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config")
    )
    config_dir = Path(xdg_config_home) / "homebus"
    config_path = config_dir / "config.toml"
    return config_path


def _env_str(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    val = os.environ.get(key)
    if val is not None:
        try:
            return int(val)
        except ValueError:
            pass
    return default


def _env_bool(key: str, default: bool) -> bool:
    val = os.environ.get(key)
    if val is not None:
        return val.lower() in ("1", "true", "yes")
    return default


def _env_float(key: str, default: float) -> float:
    val = os.environ.get(key)
    if val is not None:
        try:
            return float(val)
        except ValueError:
            pass
    return default


def load_config(
    config_path: Optional[Path] = None,
    cli_overrides: Optional[dict] = None,
) -> HomeBusConfig:
    config = HomeBusConfig()

    if config_path is None:
        config_path = discover_config_path()

    if config_path.exists():
        with open(config_path, "rb") as f:
            toml_data = tomllib.load(f)

        homebus_section = toml_data.get("homebus", {})
        adapters_section = toml_data.get("adapters", {})
        cli_section = toml_data.get("cli", {})

        config.api = ApiConfig(**homebus_section.get("api", {}))
        config.database = DatabaseConfig(**homebus_section.get("database", {}))
        config.adapters = AdaptersConfig(
            grocy=GrocyConfig(**adapters_section.get("grocy", {})),
            beancount=BeancountConfig(**adapters_section.get("beancount", {})),
            homebox=HomeboxConfig(**adapters_section.get("homebox", {})),
        )
        config.cli = CliConfig(**cli_section)

    config.api.host = _env_str("HOMEBUS_HOST", config.api.host)
    config.api.port = _env_int("HOMEBUS_PORT", config.api.port)
    config.api.debug = _env_bool("HOMEBUS_DEBUG", config.api.debug)
    config.database.path = _env_str("HOMEBUS_DB_PATH", config.database.path)
    config.adapters.grocy.base_url = _env_str(
        "GROCY_API_URL", config.adapters.grocy.base_url
    )
    config.adapters.homebox.base_url = _env_str(
        "HOMEBOX_API_URL", config.adapters.homebox.base_url
    )
    config.adapters.beancount.fava_url = _env_str(
        "BEANCOUNT_FAVA_URL", config.adapters.beancount.fava_url or ""
    ) or None
    config.adapters.beancount.ledger_path = _env_str(
        "BEANCOUNT_LEDGER_PATH", config.adapters.beancount.ledger_path
    )
    config.cli.api_url = _env_str("HOMEBUS_CLI_URL", config.cli.api_url)
    config.cli.timeout = _env_float("HOMEBUS_CLI_TIMEOUT", config.cli.timeout)

    if cli_overrides:
        for key, value in cli_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
            elif hasattr(config.cli, key):
                setattr(config.cli, key, value)

    return config
