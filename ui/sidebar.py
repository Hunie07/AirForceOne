from __future__ import annotations

import streamlit as st

from services import get_current_user, logout_user

TOP_MENU = [
    ("메인 페이지", "app.py", "🏠"),
    ("실시간 현황 대시보드", "pages/best_train_time.py", "🛡️"),
    ("연간 훈련가용 판정 현황", "pages/heatmap.py", "🌡️"),
]


def _operator_box(authenticated: bool, user: dict | None) -> None:
    if authenticated and user:
        name = user.get("username", "operator")
        service_number = user.get("service_number", "-")
        role = user.get("role", "-")
        rank = user.get("military_rank") or "미설정"
        status = "작전 대기 중"
    else:
        name = "Guest"
        service_number = "로그인 필요"
        role = "visitor"
        rank = "-"
        status = "비인증 세션"

    st.markdown(
        f"""
        <div class="wb-operator-box">
            <div class="wb-operator-top">
                <div class="wb-operator-badge">OPERATOR</div>
                <div class="wb-operator-state">{status}</div>
            </div>
            <div class="wb-operator-name">{name}</div>
            <div class="wb-operator-meta">군번 {service_number}</div>
            <div class="wb-operator-grid">
                <div class="wb-operator-chip"><span>권한</span><strong>{role}</strong></div>
                <div class="wb-operator-chip"><span>계급</span><strong>{rank}</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_primary_menu() -> None:
    st.markdown(
        '<div class="section-title" style="margin:.25rem 0 .55rem 0;">메뉴</div>',
        unsafe_allow_html=True,
    )
    for label, target, icon in TOP_MENU:
        st.page_link(target, label=label, icon=icon)


def _render_account_dropdown(authenticated: bool) -> None:
    options = ["선택하세요"]
    if authenticated:
        options += ["마이페이지", "로그아웃"]
    else:
        options += ["로그인하기", "가입하기"]

    st.markdown(
        '<div class="section-title" style="margin: .95rem 0 .45rem 0;">계정 메뉴</div>',
        unsafe_allow_html=True,
    )
    choice = st.selectbox(
        "계정 메뉴",
        options,
        label_visibility="collapsed",
        key="sidebar_account_menu",
    )
    if st.button("이동", key="sidebar_account_go", use_container_width=True):
        if choice == "로그인하기":
            st.switch_page("app.py")
        elif choice == "가입하기":
            st.switch_page("pages/register_page.py")
        elif choice == "마이페이지":
            st.switch_page("pages/my_page.py")
        elif choice == "로그아웃":
            logout_user()
            st.switch_page("app.py")


def render_sidebar_ui(current_menu: str | None = None):
    user = get_current_user()

    # ✅ 세션키 안전 처리 (둘 다 대응)
    authenticated = bool(
        st.session_state.get("authenticated")
        or st.session_state.get("is_authenticated")
    )

    with st.sidebar:
        st.markdown('<div class="wb-brand">🌤️ W-BOSS</div>', unsafe_allow_html=True)
        st.caption("기상 기반 훈련 지원")
        st.markdown("---")

        # ✅ 로그인 시에만 메뉴 표시
        if authenticated:
            _render_primary_menu()
            st.markdown("---")

        # 항상 표시
        _operator_box(authenticated, user)
        st.markdown("---")
        _render_account_dropdown(authenticated)

    return None


def route_guest_menu(menu: str | None):
    return "login"