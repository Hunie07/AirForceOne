from __future__ import annotations

from contextlib import contextmanager
import streamlit as st


def render_auth_header(hero_label: str, hero_title_plain: str, hero_title_accent: str, hero_sub: str, show_status: bool = True):
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="page-eyebrow">{hero_label}</div>
            <h1 class="page-title">{hero_title_plain} {hero_title_accent}</h1>
            <p class="page-subtitle">{hero_sub}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if show_status:
        if st.session_state.get("authenticated"):
            st.success(f"접속 중: {(st.session_state.get('user') or {}).get('username', 'operator')}")
        else:
            st.info("인가된 사용자만 접근할 수 있습니다.")


@contextmanager
def render_auth_card():
    with st.container():
        st.markdown('<div class="card-soft">', unsafe_allow_html=True)
        yield
        st.markdown('</div>', unsafe_allow_html=True)


def render_auth_footer():
    st.caption("W-BOSS · Secure Access Portal")


def auth_label(text: str = "OPERATOR"):
    st.markdown(f"**{text}**")


def auth_spacer():
    st.write("")
