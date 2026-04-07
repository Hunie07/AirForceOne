from __future__ import annotations

import streamlit as st

from core.db import get_cursor


def get_my_access_logs(limit: int = 20):
    user = st.session_state.get('user') or {}
    if not user.get('user_id'):
        return []
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                SELECT log_id, ip_address, user_agent, session_id, login_at, logout_at
                FROM access_log
                WHERE user_id = %s
                ORDER BY login_at DESC
                LIMIT %s
                """,
                (user['user_id'], limit),
            )
            return cur.fetchall() or []
    except Exception:
        return []


def get_all_access_logs(limit: int = 100):
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                SELECT log_id, user_id, service_number, unit_id, ip_address, user_agent, session_id, login_at, logout_at
                FROM access_log
                ORDER BY login_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall() or []
    except Exception:
        return []
