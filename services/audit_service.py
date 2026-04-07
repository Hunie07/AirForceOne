from __future__ import annotations

import json
import streamlit as st

from core.db import get_cursor


def _get_client_ip() -> str:
    try:
        hdrs = st.context.headers
        ip = (
            hdrs.get('X-Forwarded-For', '').split(',')[0].strip()
            or hdrs.get('X-Real-Ip', '')
            or hdrs.get('Remote-Addr', '')
        )
        return ip or '127.0.0.1'
    except Exception:
        return '127.0.0.1'


def _get_user_agent() -> str:
    try:
        return st.context.headers.get('User-Agent', '')[:255]
    except Exception:
        return ''


def _insert(action_type: str, page: str = '', description: str = '', before_data=None, after_data=None, user_id=None, service_number=None):
    current_user = st.session_state.get('user') or {}
    uid = user_id if user_id is not None else current_user.get('user_id')
    sn = service_number if service_number is not None else current_user.get('service_number')
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                INSERT INTO audit_log
                    (user_id, service_number, action_type, page, before_data, after_data, description, ip_address, device_info, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    uid,
                    sn,
                    action_type,
                    page,
                    json.dumps(before_data, ensure_ascii=False) if before_data is not None else None,
                    json.dumps(after_data, ensure_ascii=False) if after_data is not None else None,
                    description,
                    _get_client_ip(),
                    _get_user_agent(),
                ),
            )
    except Exception:
        pass


def audit_page_access(page: str):
    _insert('PAGE_ACCESS', page=page, description=f'{page} 접근')


def audit_login(user_id=None, service_number=None, page: str = 'login'):
    _insert('LOGIN', page=page, description='로그인 성공', user_id=user_id, service_number=service_number)


def audit_logout(page: str = 'logout'):
    _insert('LOGOUT', page=page, description='로그아웃')


def audit_register(user_id=None, service_number=None, page: str = 'register'):
    _insert('REGISTER', page=page, description='회원가입', user_id=user_id, service_number=service_number)


def audit_account_delete(user_id=None, service_number=None, page: str = 'delete'):
    _insert('ACCOUNT_DELETE', page=page, description='계정 삭제', user_id=user_id, service_number=service_number)


def audit_password_change(page: str = 'mypage'):
    _insert('PASSWORD_CHANGE', page=page, description='비밀번호 변경')


def audit_profile_update(before_data=None, after_data=None, page: str = 'mypage'):
    _insert('PROFILE_UPDATE', page=page, description='프로필 수정', before_data=before_data, after_data=after_data)


def audit_data_export(page: str = 'export'):
    _insert('DATA_EXPORT', page=page, description='데이터 내보내기')


def get_my_audit_logs(limit: int = 50):
    user = st.session_state.get('user') or {}
    if not user.get('service_number'):
        return []
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                SELECT audit_id, action_type, page, description, before_data, after_data, ip_address, device_info, created_at
                FROM audit_log
                WHERE service_number = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user['service_number'], limit),
            )
            return cur.fetchall() or []
    except Exception:
        return []


def get_all_audit_logs(limit: int = 200):
    try:
        with get_cursor() as (cur, _):
            cur.execute(
                """
                SELECT audit_id, user_id, service_number, action_type, page, description, ip_address, device_info, created_at
                FROM audit_log
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall() or []
    except Exception:
        return []
