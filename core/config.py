
from __future__ import annotations

import os
from pathlib import Path
import streamlit as st

APP_NAME = "W-BOSS"
APP_TITLE = "W-BOSS · 기상 작전 지원 시스템"
ROOT_DIR = Path(__file__).resolve().parents[1]


def _get_secret(path: str, default=None):
    try:
        cur = st.secrets
        for key in path.split("."):
            cur = cur[key]
        return cur
    except Exception:
        return default


def get_data_dir() -> Path:
    raw = (
        _get_secret("paths.data_dir")
        or _get_secret("data_dir")
        or os.getenv("WBOSS_DATA_DIR")
        or "data"
    )
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def _to_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def get_db_config() -> dict:
    return {
        "host": _get_secret("database.host", os.getenv("WBOSS_DB_HOST", "localhost")),
        "port": int(_get_secret("database.port", os.getenv("WBOSS_DB_PORT", "3306"))),
        "user": _get_secret("database.user", os.getenv("WBOSS_DB_USER", "root")),
        "password": _get_secret("database.password", os.getenv("WBOSS_DB_PASSWORD", "")),
        "database": _get_secret("database.database", os.getenv("WBOSS_DB_NAME", "weather_db")),
        "charset": _get_secret("database.charset", os.getenv("WBOSS_DB_CHARSET", "utf8mb4")),
        "connect_timeout": int(_get_secret("database.connect_timeout", os.getenv("WBOSS_DB_CONNECT_TIMEOUT", "10"))),
        "ssl_enabled": _to_bool(_get_secret("database.ssl_enabled", os.getenv("WBOSS_DB_SSL_ENABLED", "")), False),
        "ssl_ca": _get_secret("database.ssl_ca", os.getenv("WBOSS_DB_SSL_CA", "")),
    }


DATA_DIR = get_data_dir()
DB_CONFIG = get_db_config()


def get_api_config() -> dict:
    return {
        "short_term_forecast_api_key": _get_secret("api.SHORT_TERM_FORECAST_API_KEY", os.getenv("SHORT_TERM_FORECAST_API_KEY", "")),
        "report_data_api_service_key": _get_secret("api.REPORT_DATA_API_SERVICE_KEY", os.getenv("REPORT_DATA_API_SERVICE_KEY", "")),
    }


API_CONFIG = get_api_config()
