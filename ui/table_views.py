from __future__ import annotations

import pandas as pd
import streamlit as st


def _height(n_rows: int, base: int = 42, max_height: int = 420) -> int:
    return min(max_height, base * (max(3, n_rows) + 1))


def render_year_stats_table(df: pd.DataFrame):
    if df is None or df.empty:
        st.info("연도별 통계가 없습니다.")
        return
    view = df.rename(
        columns={
            "year": "연도",
            "mean_score": "평균 점수",
            "min_score": "최저 점수",
            "max_score": "최고 점수",
            "samples": "표본 수",
        }
    ).copy()
    st.dataframe(
        view,
        hide_index=True,
        use_container_width=True,
        height=_height(len(view), max_height=360),
        column_config={
            "연도": st.column_config.NumberColumn("연도", format="%d"),
            "평균 점수": st.column_config.NumberColumn("평균 점수", format="%.3f"),
            "최저 점수": st.column_config.NumberColumn("최저 점수", format="%.3f"),
            "최고 점수": st.column_config.NumberColumn("최고 점수", format="%.3f"),
            "표본 수": st.column_config.NumberColumn("표본 수", format="%d"),
        },
    )


def prepare_daily_detail_view(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    view = df.copy()
    view = view.rename(
        columns={
            "hour": "시각",
            "actual": "실측",
            "baseline": "기준",
            "wct": "체감온도",
            "ta": "기온",
            "ws": "풍속",
            "hm": "습도",
            "rn": "강수량",
            "dsnw": "적설",
            "score": "훈련 점수",
        }
    )
    ordered = [c for c in ["시각", "실측", "기준", "체감온도", "기온", "풍속", "습도", "강수량", "적설", "훈련 점수"] if c in view.columns]
    if ordered:
        view = view[ordered]
    return view


def render_daily_detail_table(df: pd.DataFrame, selected_columns: list[str] | None = None, height: int | None = None):
    view = prepare_daily_detail_view(df)
    if view.empty:
        st.info("선택한 날짜의 상세 데이터가 없습니다.")
        return

    if selected_columns:
        available = [c for c in selected_columns if c in view.columns]
        if "시각" in view.columns and "시각" not in available:
            available = ["시각"] + available
        if available:
            view = view[available]

    st.dataframe(
        view,
        hide_index=True,
        use_container_width=True,
        height=height or _height(len(view), max_height=420),
        column_config={
            "시각": st.column_config.NumberColumn("시각", format="%d시"),
            "실측": st.column_config.NumberColumn("실측", format="%.1f°C"),
            "기준": st.column_config.NumberColumn("기준", format="%.1f°C"),
            "체감온도": st.column_config.NumberColumn("체감온도", format="%.1f°C"),
            "기온": st.column_config.NumberColumn("기온", format="%.1f°C"),
            "풍속": st.column_config.NumberColumn("풍속", format="%.1f"),
            "습도": st.column_config.NumberColumn("습도", format="%d"),
            "강수량": st.column_config.NumberColumn("강수량", format="%.1f"),
            "적설": st.column_config.NumberColumn("적설", format="%.1f"),
            "훈련 점수": st.column_config.NumberColumn("훈련 점수", format="%.2f"),
        },
    )


def render_access_logs_table(df: pd.DataFrame):
    if df is None or df.empty:
        st.info("접속 기록이 없습니다.")
        return
    view = df.copy()
    if "user_agent" in view.columns:
        view["브라우저"] = view["user_agent"].astype(str).str.slice(0, 42) + "…"
        view = view.drop(columns=["user_agent"])
    if "session_id" in view.columns:
        view["세션"] = view["session_id"].astype(str).str.slice(0, 16) + "…"
        view = view.drop(columns=["session_id"])
    rename_map = {
        "log_id": "로그ID",
        "service_number": "군번",
        "unit_id": "부대",
        "ip_address": "IP",
        "login_at": "로그인",
        "logout_at": "로그아웃",
        "user_id": "사용자ID",
    }
    view = view.rename(columns=rename_map)
    keep = [c for c in ["로그ID", "사용자ID", "군번", "부대", "IP", "브라우저", "세션", "로그인", "로그아웃"] if c in view.columns]
    view = view[keep]
    st.dataframe(view, hide_index=True, use_container_width=True, height=_height(len(view), max_height=430))


def render_audit_logs_table(df: pd.DataFrame):
    if df is None or df.empty:
        st.info("감사 로그가 없습니다.")
        return
    view = df.copy()
    if "device_info" in view.columns:
        view["기기"] = view["device_info"].astype(str).str.slice(0, 36) + "…"
        view = view.drop(columns=["device_info"])
    if "description" in view.columns:
        view["설명"] = view["description"].astype(str).str.slice(0, 40)
    rename_map = {
        "audit_id": "감사ID",
        "user_id": "사용자ID",
        "service_number": "군번",
        "action_type": "행위",
        "page": "페이지",
        "ip_address": "IP",
        "created_at": "시각",
        "before_data": "이전값",
        "after_data": "이후값",
    }
    view = view.rename(columns=rename_map)
    keep = [c for c in ["감사ID", "사용자ID", "군번", "행위", "페이지", "설명", "IP", "기기", "시각"] if c in view.columns]
    view = view[keep]
    st.dataframe(view, hide_index=True, use_container_width=True, height=_height(len(view), max_height=430))
