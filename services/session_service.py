from __future__ import annotations

import streamlit as st


def init_session() -> None:
    st.session_state.setdefault('authenticated', False)
    st.session_state.setdefault('user', None)
    st.session_state.setdefault('session_id', None)
    st.session_state.setdefault('log_id', None)
    st.session_state.setdefault('prefs', {'regions': []})
    st.session_state.setdefault('theme_mode', '라이트 모드')


def is_authenticated() -> bool:
    return bool(st.session_state.get('authenticated'))


def get_current_user():
    return st.session_state.get('user')
