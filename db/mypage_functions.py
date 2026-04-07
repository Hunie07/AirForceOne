"""
functions/mypage_functions.py
W-BOSS 마이페이지 전용 DB 헬퍼 함수
────────────────────────────────────────────────────────────
• change_password()    : 비밀번호 변경 (현재 PW 검증 포함)
• update_rank()        : 계급 수정 (세션 갱신 포함)
• get_user_fresh()     : DB에서 최신 사용자 정보 조회
• get_my_access_logs() : 본인 접속 로그 조회
• get_all_access_logs(): 전체 접속 로그 조회 (관리자 전용)
"""

from __future__ import annotations

import streamlit as st

try:
    from db_connection import get_cursor
    from services.auth_functions import verify_password, hash_password
    from audit_logger import audit_password_change, audit_profile_update
except ImportError:
    from db_connection import get_cursor
    from services.auth_functions import verify_password, hash_password
    from audit_logger import audit_password_change, audit_profile_update


# ── 비밀번호 변경 ─────────────────────────────────────────
def change_password(
    user_id: int,
    old_pw: str,
    new_pw: str,
    confirm_pw: str,
) -> tuple[bool, str]:
    """
    현재 비밀번호를 검증한 뒤 새 비밀번호로 변경합니다.

    Returns
    -------
    (True, 성공 메시지) 또는 (False, 오류 메시지)
    """
    if len(new_pw) < 8:
        return False, "새 비밀번호는 8자 이상이어야 합니다."
    if new_pw != confirm_pw:
        return False, "새 비밀번호가 일치하지 않습니다."
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                "SELECT password_hash FROM USERS WHERE user_id = %s AND deleted_at IS NULL",
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return False, "사용자를 찾을 수 없습니다."
            if not verify_password(old_pw, row["password_hash"]):
                return False, "현재 비밀번호가 일치하지 않습니다."
            cur.execute(
                "UPDATE USERS SET password_hash = %s WHERE user_id = %s",
                (hash_password(new_pw), user_id),
            )
        audit_password_change(user_id)
        return True, "비밀번호가 변경되었습니다."
    except Exception as exc:
        return False, f"서버 오류: {exc}"


# ── 계급 수정 ─────────────────────────────────────────────
def update_rank(
    user_id: int,
    old_rank: str | None,
    new_rank: str | None,
) -> tuple[bool, str]:
    """
    계급을 수정하고 Streamlit 세션을 갱신합니다.

    Returns
    -------
    (True, 성공 메시지) 또는 (False, 오류 메시지)
    """
    new_rank = new_rank.strip() if new_rank else None
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                "UPDATE USERS SET military_rank = %s WHERE user_id = %s",
                (new_rank, user_id),
            )
        audit_profile_update(
            user_id,
            before={"military_rank": old_rank},
            after={"military_rank": new_rank},
        )
        st.session_state["user"]["military_rank"] = new_rank
        return True, "계급이 수정되었습니다."
    except Exception as exc:
        return False, f"서버 오류: {exc}"


# ── 최신 사용자 정보 조회 ─────────────────────────────────
def get_user_fresh(user_id: int) -> dict | None:
    """DB에서 최신 사용자 정보를 조회합니다."""
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                SELECT user_id, username, service_number, unit_id,
                       role, military_rank
                FROM   USERS
                WHERE  user_id = %s AND deleted_at IS NULL
                LIMIT  1
                """,
                (user_id,),
            )
            return cur.fetchone()
    except Exception:
        return None


# ── 본인 접속 로그 조회 ───────────────────────────────────
def get_my_access_logs(user_id: int, limit: int = 20) -> list[dict]:
    """본인의 접속 로그를 최근 순으로 조회합니다."""
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                SELECT log_id, ip_address, login_at, logout_at,
                       TIMESTAMPDIFF(MINUTE, login_at, IFNULL(logout_at, NOW())) AS duration_min
                FROM   ACCESS_LOG
                WHERE  user_id = %s
                ORDER  BY login_at DESC
                LIMIT  %s
                """,
                (user_id, limit),
            )
            return cur.fetchall()
    except Exception:
        return []


# ── 전체 접속 로그 조회 (관리자 전용) ────────────────────
def get_all_access_logs(limit: int = 100) -> list[dict]:
    """전체 사용자의 접속 로그를 최근 순으로 조회합니다."""
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                SELECT a.log_id, u.username, a.service_number,
                       a.ip_address, a.login_at, a.logout_at,
                       TIMESTAMPDIFF(MINUTE, a.login_at, IFNULL(a.logout_at, NOW())) AS duration_min
                FROM   ACCESS_LOG a
                LEFT JOIN USERS u ON a.user_id = u.user_id
                ORDER  BY a.login_at DESC
                LIMIT  %s
                """,
                (limit,),
            )
            return cur.fetchall()
    except Exception:
        return []
