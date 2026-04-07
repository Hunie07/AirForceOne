"""
utils/heatmap_figures.py
────────────────────────
히트맵 페이지 Plotly Figure 생성 함수 모음
캐싱(@st.cache_resource / @st.cache_data) 포함
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from utils.heatmap.bar_graph_function_sp import ALL_MONTHS, get_all_yearly_pivots
from utils.heatmap.config import HEATMAP_COLORSCALE


# ══════════════════════════════════════════════════════════════════════════════
# 연간 히트맵 Figure
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def create_heatmap_figure(
    _df,
    sel_sploc: str,
    sel_year: int,
    sel_hour: str,
    disp_name: str,
) -> go.Figure:
    """
    연간 365일 훈련가부 판정 히트맵 Figure를 생성합니다.

    Parameters
    ----------
    _df       : 원본 DataFrame (언더스코어 prefix → 캐시 키 제외)
    sel_sploc : 지점 코드
    sel_year  : 연도
    sel_hour  : 시각 문자열 ("6" / "12" / "18")
    disp_name : 화면 표시용 지역명
    """
    pivots     = get_all_yearly_pivots(_df, sel_sploc, sel_year, int(sel_hour))
    grade_piv  = pivots["unified_grade"]
    status_piv = pivots["unified_status"]
    wct_piv    = pivots["WCT"]
    ta_piv     = pivots["ta"]
    ws_piv     = pivots["ws"]
    hm_piv     = pivots["hm"]
    rn_piv     = pivots["rn"]
    dsnw_piv   = pivots["dsnw"]

    x_days   = list(range(1, 32))
    y_months = ALL_MONTHS

    hover_text: list[list[str]] = []
    annotations: list[dict]     = []

    for i, m in enumerate(y_months):
        row_hover: list[str] = []
        for j, d in enumerate(x_days):
            w = wct_piv.iloc[i, j]
            s = status_piv.iloc[i, j]
            g = grade_piv.iloc[i, j]

            if pd.isna(w):
                row_hover.append(f"{sel_year}년 {m}월 {d}일: 관측 데이터 없음")
            else:
                ta = ta_piv.iloc[i, j]; ws = ws_piv.iloc[i, j]
                hm = hm_piv.iloc[i, j]; rn = rn_piv.iloc[i, j]; sn = dsnw_piv.iloc[i, j]
                row_hover.append(
                    f"<b>{sel_year}년 {m}월 {d}일</b><br>판정: <b>{s}</b><br><br>"
                    f"체감온도: <b>{w:.1f}°C</b><br>기온: {ta:.1f}°C | 풍속: {ws:.1f}m/s<br>"
                    f"습도: {hm:.0f}% | 강수: {rn:.1f}mm | 적설: {sn:.1f}cm"
                )
        hover_text.append(row_hover)

    fig = go.Figure(data=go.Heatmap(
        z=grade_piv.values,
        x=[f"{d}일" for d in x_days],
        y=[f"{m}월" for m in y_months],
        colorscale=HEATMAP_COLORSCALE,
        zmin=0, zmax=7, xgap=2, ygap=2, showscale=False,
        customdata=hover_text,
        hovertemplate="%{customdata}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,1)",
        plot_bgcolor="rgba(255,255,255,1)",
        font=dict(family="sans-serif", color="#57606a", size=11),
        height=650,
        margin=dict(l=40, r=20, t=20, b=20),
    )
    fig.update_yaxes(autorange="reversed", tickfont=dict(color="#24292f"))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 히트맵 PNG 이미지 바이트 생성
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def get_heatmap_image_bytes(
    _df,
    sel_sploc: str,
    sel_year: int,
    sel_hour: str,
    disp_name: str,
) -> bytes:
    """히트맵 Figure를 PNG 바이트로 변환합니다. (kaleido 패키지 필요)"""
    fig = create_heatmap_figure(_df, sel_sploc, sel_year, sel_hour, disp_name)
    return fig.to_image(format="png", width=1200, height=750, scale=2)


# ══════════════════════════════════════════════════════════════════════════════
# 24시간 라인 플롯 Figure
# ══════════════════════════════════════════════════════════════════════════════

def create_daily_line_figure(day_df: pd.DataFrame) -> go.Figure:
    """하루 24시간 체감온도 / 기온 라인 플롯 Figure를 생성합니다."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=day_df["hour"], y=day_df["WCT"],
        name="체감(°C)", mode="lines+markers",
        line=dict(color="#0969da", width=2),
        customdata=day_df[["ta", "ws", "hm", "rn", "dsnw"]],
        hovertemplate=(
            "<b>%{x}시</b><br>체감온도: %{y:.1f}°C<br>"
            "기온: %{customdata[0]:.1f}°C<extra></extra>"
        ),
    ))
    fig.add_trace(go.Scatter(
        x=day_df["hour"], y=day_df["ta"],
        name="기온(°C)", mode="lines",
        line=dict(color="#cf222e", width=1, dash="dot"),
        hoverinfo="skip",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,1)",
        plot_bgcolor="rgba(255,255,255,1)",
        height=200,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(size=10, color="#57606a"),
        ),
        xaxis=dict(
            tickmode="linear", dtick=6,
            color="#57606a", showgrid=True, gridcolor="rgba(208,215,222,0.5)",
        ),
        yaxis=dict(color="#57606a", showgrid=True, gridcolor="rgba(208,215,222,0.5)"),
    )
    return fig
