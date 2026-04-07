from __future__ import annotations

import streamlit as st

from services import init_session
from ui import render_register_page, render_sidebar_ui, render_streamlit_base_style

st.set_page_config(page_title="가입하기", page_icon="📝", layout="wide")
render_streamlit_base_style()
init_session()
render_sidebar_ui("가입하기")
render_register_page()
