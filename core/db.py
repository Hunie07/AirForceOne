from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Dict, Generator, Tuple

import pymysql
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_ENGINE: Engine | None = None


def _read_db_config() -> Dict[str, Any]:
    """
    DB 설정을 읽는다.

    우선순위
    1) Streamlit secrets 의 [mysql]
    2) 환경변수
       - WBOSS_DB_HOST
       - WBOSS_DB_PORT
       - WBOSS_DB_NAME
       - WBOSS_DB_USER
       - WBOSS_DB_PASSWORD
       - WBOSS_DB_CHARSET
    """
    try:
        if "mysql" in st.secrets:
            cfg = st.secrets["mysql"]
            return {
                "host": cfg["host"],
                "port": int(cfg.get("port", 3306)),
                "database": cfg["database"],
                "user": cfg["user"],
                "password": cfg["password"],
                "charset": cfg.get("charset", "utf8mb4"),
            }
    except Exception:
        pass

    return {
        "host": os.getenv("WBOSS_DB_HOST", "localhost"),
        "port": int(os.getenv("WBOSS_DB_PORT", "3306")),
        "database": os.getenv("WBOSS_DB_NAME", "weather_db"),
        "user": os.getenv("WBOSS_DB_USER", "root"),
        "password": os.getenv("WBOSS_DB_PASSWORD", ""),
        "charset": os.getenv("WBOSS_DB_CHARSET", "utf8mb4"),
    }


def _build_sqlalchemy_url(cfg: Dict[str, Any]) -> str:
    user = cfg["user"]
    password = cfg["password"]
    host = cfg["host"]
    port = cfg["port"]
    database = cfg["database"]
    charset = cfg["charset"]

    return (
        f"mysql+pymysql://{user}:{password}"
        f"@{host}:{port}/{database}?charset={charset}"
    )


def get_engine() -> Engine:
    """
    SQLAlchemy Engine 싱글톤 반환.
    Streamlit 재실행 시에도 불필요한 엔진 재생성을 줄인다.
    """
    global _ENGINE

    if _ENGINE is None:
        cfg = _read_db_config()
        url = _build_sqlalchemy_url(cfg)

        _ENGINE = create_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=3600,
            future=True,
        )

    return _ENGINE


def get_connection():
    """
    raw DBAPI connection 반환.
    기존 코드에서 conn.cursor() 패턴을 유지할 수 있게 한다.
    """
    return get_engine().raw_connection()


@contextmanager
def get_cursor() -> Generator[Tuple[pymysql.cursors.DictCursor, Any], None, None]:
    """
    DictCursor + connection 컨텍스트 매니저.

    사용 예:
        with get_cursor() as (cur, conn):
            cur.execute("SELECT * FROM users")
            rows = cur.fetchall()
            conn.commit()
    """
    conn = get_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    try:
        yield cur, conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            cur.close()
        finally:
            conn.close()


def test_connection() -> bool:
    """
    간단한 DB 연결 테스트.
    """
    with get_cursor() as (cur, _):
        cur.execute("SELECT 1 AS ok")
        row = cur.fetchone()
        return bool(row and row.get("ok") == 1)