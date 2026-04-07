from __future__ import annotations

import streamlit as st

from services import init_session, is_authenticated
from ui import render_login_page, render_mypage_page, render_sidebar_ui, render_streamlit_base_style

st.set_page_config(page_title="마이페이지", page_icon="🪪", layout="wide")
render_streamlit_base_style()
init_session()
render_sidebar_ui("마이페이지")

if is_authenticated():
    render_mypage_page()
else:
    st.warning("로그인이 필요합니다.")
    render_login_page()
