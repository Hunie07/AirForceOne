import streamlit as st

from services import init_session, is_authenticated
from ui import render_login_page, render_sidebar_ui, render_streamlit_base_style
from ui.home import render_main_dashboard


st.set_page_config(page_title="W-BOSS", page_icon="🌩️", layout="wide")
render_streamlit_base_style()
init_session()
render_sidebar_ui("메인 페이지")

if is_authenticated():
    render_main_dashboard()
else:
    render_login_page()
