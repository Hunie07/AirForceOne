from __future__ import annotations

import logging
import re
import secrets
from typing import Optional

import streamlit as st

from core.db import get_cursor
from services.audit_service import (
    audit_account_delete,
    audit_login,
    audit_logout,
    audit_password_change,
    audit_profile_update,
    audit_register,
)
from services.session_service import init_session

logger = logging.getLogger(__name__)
_SERVICE_RE = re.compile(r"^\d{2}-(?:\d{5}|\d{6}|\d{8})$")
_PW_MIN = 8


def _row_get(row, key, default=None):
    if row is None:
        return default
    if isinstance(row, dict):
        return row.get(key, default)
    return default


def _password_column_name() -> str:
    try:
        with get_cursor() as (cur, _):
            cur.execute("SHOW COLUMNS FROM users")
            rows = cur.fetchall() or []

        cols = []
        for r in rows:
            if isinstance(r, dict):
                cols.append(str(r.get("Field", "")).lower())

        if "password_hash" in cols:
            return "password_hash"
        if "password" in cols:
            return "password"
    except Exception:
        pass

    return "password"


def validate_service_number(sn: str) -> tuple[bool, str]:
    sn = sn.strip()
    if not sn:
        return False, "군번을 입력하세요."
    if not _SERVICE_RE.match(sn):
        return False, "군번 형식은 YY-NNNNN / YY-NNNNNN / YY-NNNNNNNN 이어야 합니다."
    return True, "OK"


def get_role_by_sn(sn: str) -> str:
    tail = sn.strip().split("-", 1)[-1]
    if len(tail) == 5:
        return "officer"
    if len(tail) == 6:
        return "nco"
    return "soldier"


def generate_session_id() -> str:
    return secrets.token_hex(32)


def get_client_ip() -> str:
    try:
        hdrs = st.context.headers
        ip = (
            hdrs.get("X-Forwarded-For", "").split(",")[0].strip()
            or hdrs.get("X-Real-Ip", "")
            or hdrs.get("Remote-Addr", "")
        )
        return ip or "127.0.0.1"
    except Exception:
        return "127.0.0.1"


def get_user_agent() -> str:
    try:
        return st.context.headers.get("User-Agent", "")[:255]
    except Exception:
        return ""


def _verify_password(plain: str, stored: str) -> bool:
    return plain == (stored or "")


def _load_user_by_service_number(sn: str) -> Optional[dict]:
    pw_col = _password_column_name()
    with get_cursor() as (cur, _):
        cur.execute(
            f"""
            SELECT user_id, username, service_number, unit_id, role, military_rank, {pw_col} AS password_value
            FROM users
            WHERE service_number = %s AND deleted_at IS NULL
            LIMIT 1
            """,
            (sn,),
        )
        return cur.fetchone()


def _set_authenticated(user: dict) -> None:
    sid = generate_session_id()
    log_id = log_access(user, sid)
    st.session_state["authenticated"] = True
    st.session_state["user"] = user
    st.session_state["session_id"] = sid
    st.session_state["log_id"] = log_id
    try:
        audit_login(user.get("user_id"), user.get("service_number"))
    except Exception:
        pass


def login_user(service_number: str, password: str):
    init_session()
    sn = service_number.strip()
    valid, msg = validate_service_number(sn)
    if not valid:
        return False, msg
    if not password:
        return False, "비밀번호를 입력하세요."

    try:
        user = _load_user_by_service_number(sn)
    except Exception as exc:
        logger.exception("login_user failed: %s", exc)
        return False, "DB 연결 또는 조회 중 오류가 발생했습니다."

    if not user:
        return False, "등록되지 않은 군번입니다."

    if not _verify_password(password, _row_get(user, "password_value", "")):
        return False, "비밀번호가 일치하지 않습니다."

    if isinstance(user, dict):
        user.pop("password_value", None)

    _set_authenticated(user)
    return True, "로그인 성공"


def logout_user():
    try:
        audit_logout()
    except Exception:
        pass

    update_logout_time(st.session_state.get("log_id"))

    for key in ("authenticated", "user", "session_id", "log_id"):
        st.session_state.pop(key, None)

    return True, "로그아웃되었습니다."


def log_access(user: dict, session_id: str):
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                INSERT INTO access_log
                    (user_id, service_number, unit_id, ip_address, user_agent, session_id, login_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    user["user_id"],
                    user["service_number"],
                    user["unit_id"],
                    get_client_ip(),
                    get_user_agent(),
                    session_id,
                ),
            )
            return cur.lastrowid
    except Exception as exc:
        logger.warning("log_access failed: %s", exc)
        return None


def update_logout_time(log_id: int | None) -> None:
    if not log_id:
        return
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                "UPDATE access_log SET logout_at = NOW() WHERE log_id = %s",
                (log_id,),
            )
    except Exception as exc:
        logger.warning("update_logout_time failed: %s", exc)


def register_user(unit_id: str, username: str, service_number: str, password: str):
    init_session()

    sn = service_number.strip()
    username = username.strip()

    valid, msg = validate_service_number(sn)
    if not valid:
        return False, msg

    if len(username) < 2 or len(username) > 20:
        return False, "이름은 2~20자여야 합니다."
    if len(password) < _PW_MIN:
        return False, f"비밀번호는 {_PW_MIN}자 이상이어야 합니다."
    if not unit_id:
        return False, "부대를 선택하세요."

    role = get_role_by_sn(sn)
    pw_col = _password_column_name()

    try:
        with get_cursor() as (cur, _):
            cur.execute("SELECT unit_id FROM unit WHERE unit_id = %s", (unit_id,))
            if not cur.fetchone():
                return False, "존재하지 않는 부대 ID입니다."

            cur.execute(
                "SELECT user_id, deleted_at FROM users WHERE service_number = %s",
                (sn,),
            )
            row = cur.fetchone()

            if row and _row_get(row, "deleted_at") is None:
                return False, "이미 등록된 군번입니다."

            if row and _row_get(row, "deleted_at") is not None:
                cur.execute(
                    f"""
                    UPDATE users
                    SET unit_id=%s, username=%s, {pw_col}=%s, role=%s, military_rank=%s, deleted_at=NULL
                    WHERE service_number=%s
                    """,
                    (unit_id, username, password, role, "미설정", sn),
                )
                user_id = _row_get(row, "user_id")
            else:
                cur.execute(
                    f"""
                    INSERT INTO users (unit_id, username, service_number, {pw_col}, role, military_rank)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (unit_id, username, sn, password, role, "미설정"),
                )
                user_id = cur.lastrowid

        audit_register(user_id=user_id, service_number=sn)
        return True, f"회원가입이 완료되었습니다. 권한은 {role} 로 자동 설정되었습니다."
    except Exception as exc:
        logger.exception("register_user failed: %s", exc)
        return False, "DB 저장 중 오류가 발생했습니다."


def delete_user(service_number: str, password: str):
    sn = service_number.strip()
    pw_col = _password_column_name()

    try:
        with get_cursor() as (cur, _):
            cur.execute(
                f"""
                SELECT user_id, service_number, {pw_col} AS password_value
                FROM users
                WHERE service_number = %s AND deleted_at IS NULL
                LIMIT 1
                """,
                (sn,),
            )
            row = cur.fetchone()

            if not row:
                return False, "사용자를 찾을 수 없습니다."
            if not _verify_password(password, _row_get(row, "password_value", "")):
                return False, "비밀번호가 일치하지 않습니다."

            cur.execute(
                "UPDATE users SET deleted_at = NOW() WHERE user_id = %s",
                (_row_get(row, "user_id"),),
            )

        audit_account_delete(
            user_id=_row_get(row, "user_id"),
            service_number=_row_get(row, "service_number"),
        )

        current = st.session_state.get("user") or {}
        if current.get("service_number") == _row_get(row, "service_number"):
            logout_user()

        return True, "탈퇴 처리가 완료되었습니다."
    except Exception as exc:
        logger.exception("delete_user failed: %s", exc)
        return False, "DB 처리 중 오류가 발생했습니다."


def change_password(service_number: str, current_password: str, new_password: str):
    if len(new_password or "") < _PW_MIN:
        return False, f"새 비밀번호는 {_PW_MIN}자 이상이어야 합니다."

    pw_col = _password_column_name()

    try:
        with get_cursor() as (cur, _):
            cur.execute(
                f"""
                SELECT user_id, {pw_col} AS password_value
                FROM users
                WHERE service_number = %s AND deleted_at IS NULL
                LIMIT 1
                """,
                (service_number,),
            )
            row = cur.fetchone()

            if not row:
                return False, "계정을 찾을 수 없습니다."
            if not _verify_password(current_password, _row_get(row, "password_value", "")):
                return False, "현재 비밀번호가 일치하지 않습니다."

            cur.execute(
                f"UPDATE users SET {pw_col} = %s WHERE service_number = %s",
                (new_password, service_number),
            )

        audit_password_change()
        return True, "비밀번호가 변경되었습니다."
    except Exception as exc:
        logger.exception("change_password failed: %s", exc)
        return False, "DB 처리 중 오류가 발생했습니다."


def update_rank(service_number: str, military_rank: str):
    try:
        before = get_user_fresh(service_number)
        if not before:
            return False, "계정을 찾을 수 없습니다."

        with get_cursor() as (cur, _):
            cur.execute(
                "UPDATE users SET military_rank = %s WHERE service_number = %s AND deleted_at IS NULL",
                (military_rank, service_number),
            )

        after = get_user_fresh(service_number)
        current = st.session_state.get("user") or {}

        if current.get("service_number") == service_number and after:
            if isinstance(after, dict):
                after.pop("password_value", None)
            st.session_state["user"] = {
                k: v for k, v in after.items() if k != "password_value"
            }

        audit_profile_update(
            before_data={"military_rank": before.get("military_rank")},
            after_data={"military_rank": after.get("military_rank") if after else military_rank},
        )
        return True, "계급이 변경되었습니다."
    except Exception as exc:
        logger.exception("update_rank failed: %s", exc)
        return False, "DB 처리 중 오류가 발생했습니다."


def get_user_fresh(service_number: str):
    pw_col = _password_column_name()
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                f"""
                SELECT user_id, username, service_number, unit_id, role, military_rank, {pw_col} AS password_value
                FROM users
                WHERE service_number = %s AND deleted_at IS NULL
                LIMIT 1
                """,
                (service_number,),
            )
            return cur.fetchone()
    except Exception:
        return None


def get_all_units() -> list[dict]:
    try:
        with get_cursor() as (cur, _):
            cur.execute("SELECT unit_id, unit_name FROM unit ORDER BY unit_id")
            return cur.fetchall() or []
    except Exception:
        return []


def get_recent_access_logs(user_id: int, limit: int = 10) -> list[dict]:
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                SELECT log_id, ip_address, login_at, logout_at, session_id
                FROM access_log
                WHERE user_id = %s
                ORDER BY login_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            return cur.fetchall() or []
    except Exception:
        return []
