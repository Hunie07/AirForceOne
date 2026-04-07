from __future__ import annotations

import streamlit as st

from services import delete_user, get_all_units, init_session, login_user, register_user
from ui.auth_ui import render_auth_header, render_auth_card, render_auth_footer
from ui.mypage import render_mypage_dashboard


def render_login_page():
    init_session()
    render_auth_header('◈ SECURE ACCESS PORTAL ◈', '시스템', '로그인', '인가된 사용자만 접근할 수 있습니다.')
    with render_auth_card():
        sn = st.text_input('군번')
        pw = st.text_input('비밀번호', type='password')
        if st.button('로그인', use_container_width=True):
            ok, msg = login_user(sn, pw)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
    render_auth_footer()


def render_register_page():
    render_auth_header('◈ ACCOUNT ENROLLMENT ◈', '신규 계정', '등록', '권한(admin 포함)은 직접 선택할 수 없고 군번 형식으로 자동 판정됩니다.', show_status=False)
    with render_auth_card():
        with st.form('register_form'):
            units = get_all_units()
            if units:
                options = {f"{u['unit_name']} ({u['unit_id']})": u['unit_id'] for u in units}
                selected = st.selectbox('부대', list(options.keys()))
                unit_id = options[selected]
            else:
                st.caption('부대 목록을 불러오지 못해 직접 입력 모드로 전환되었습니다.')
                unit_id = st.text_input('부대 코드')
            username = st.text_input('이름')
            service_number = st.text_input('군번', placeholder='장교 25-12345 / 부사관 22-123456 / 병 26-12345678')
            password = st.text_input('비밀번호', type='password')
            st.caption('권한은 선택하지 않습니다. 군번 뒷자리 길이로 자동 판정됩니다.')
            submit = st.form_submit_button('회원가입', use_container_width=True)
            if submit:
                ok, msg = register_user(unit_id, username, service_number, password)
                (st.success if ok else st.error)(msg)
    render_auth_footer()


def render_delete_page():
    st.header('계정 삭제')
    current = st.session_state.get('user') or {}
    with st.form('delete_form'):
        service_number = st.text_input('군번', value=current.get('service_number', ''))
        password = st.text_input('비밀번호', type='password')
        submit = st.form_submit_button('계정 삭제')
        if submit:
            ok, msg = delete_user(service_number, password)
            (st.success if ok else st.error)(msg)


def render_mypage_page():
    render_mypage_dashboard()
