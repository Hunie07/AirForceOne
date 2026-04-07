from __future__ import annotations

import html
import pandas as pd
import streamlit as st

from services import (
    get_station_options,
    get_hour_options,
    get_year_options,
    get_month_options,
    get_day_options,
    build_annual_heatmap,
    summarize_annual_heatmap,
    get_daily_compare_detail,
)
from ui.components import draw_annual_day_heatmap, draw_daily_reference_chart
from ui.table_views import render_daily_detail_table, prepare_daily_detail_view


def _summary_card(label: str, value: int, total: int, color: str):
    pct = round((value / total) * 100) if total else 0
    st.markdown(
        '''<div class="wb-panel" style="padding:.95rem 1rem;margin-bottom:.6rem;">
            <div style="font-size:.9rem;color:var(--wb-text);font-weight:700;">{label}</div>
            <div style="font-size:2rem;font-weight:800;color:{color};margin-top:.35rem;">{value}일</div>
            <div style="font-size:.84rem;color:var(--wb-muted);margin-top:.14rem;">{pct}%</div>
        </div>'''.format(label=html.escape(label), color=color, value=value, pct=pct),
        unsafe_allow_html=True,
    )


def _monthly_summary_html(monthly_rows: list[dict]) -> str:
    rows = []
    for row in monthly_rows:
        rows.append(
            '''<div style="display:flex;justify-content:space-between;gap:.6rem;padding:.32rem 0;border-bottom:1px solid rgba(255,255,255,.04);">
                <div style="color:var(--wb-muted);font-size:.86rem;">{month}월</div>
                <div style="color:var(--wb-text);font-size:.86rem;font-weight:700;">{days}일 <span style="color:var(--wb-muted);font-weight:500;">({pct}%)</span></div>
            </div>'''.format(month=row["month"], days=row["normal_days"], pct=row["percent"])
        )
    return ''.join(rows)


def _pick_hour_control(hours: list[int], default_hour: int):
    labels = {h: f"{int(h):02d}시" for h in hours}
    idx = hours.index(default_hour) if default_hour in hours else 0
    return st.selectbox("기준 시각", hours, index=idx, format_func=lambda x: labels.get(x, str(x)))


def render_heatmap_dashboard():
    st.markdown(
        '''<div class="hero-card">
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                <div style="display:inline-flex;align-items:center;padding:.38rem .78rem;border-radius:999px;background:var(--wb-primary);color:white;font-size:.8rem;font-weight:800;">
                    MODULE · 연간 365일 분석
                </div>
                <div>
                    <div class="page-title" style="font-size:1.82rem;margin-bottom:.22rem;">연간 훈련판정 매핑 히트맵</div>
                    <div class="page-subtitle">연간 분포, 종합 통계, 24시간 비교 그래프, 상세 테이블을 한 화면에서 보기 쉽게 정리했습니다.</div>
                </div>
            </div>
        </div>''',
        unsafe_allow_html=True,
    )

    stations = get_station_options()
    hours = get_hour_options()
    default_hours = [h for h in [6, 12, 18] if h in hours] or hours[:3]
    default_hour = 12 if 12 in default_hours else default_hours[0]

    ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1.15, 0.9, 0.9, 0.95, 0.95], gap="large")
    with ctrl1:
        station = st.selectbox("지역", stations, index=0 if stations else None)
    years = get_year_options(station, default_hour) if stations else []
    with ctrl2:
        year = st.selectbox("연도", years, index=len(years) - 1 if years else None)
    with ctrl3:
        hour = _pick_hour_control(default_hours, default_hour)
    with ctrl4:
        metric_label = st.selectbox("통계기준", ["체감온도", "기온"], index=0)
    with ctrl5:
        formula = st.selectbox("산출식", ["평균", "최대", "최소"], index=0)

    mat = build_annual_heatmap(station, year, hour, metric_label, formula)
    summary = summarize_annual_heatmap(mat, metric_label)

    detail1, detail2 = st.columns([1.0, 1.0], gap="large")
    months = get_month_options(station, hour, year) if years else []
    with detail1:
        detail_month = st.selectbox("24시간 상세 조회 · 월", months, index=0 if months else None)
    days = get_day_options(station, hour, year, detail_month) if months else []
    with detail2:
        detail_day = st.selectbox("24시간 상세 조회 · 일", days, index=0 if days else None)

    detail_df = get_daily_compare_detail(station, year, detail_month, detail_day, metric_label) if days else pd.DataFrame()

    top_left, top_right = st.columns([0.24, 0.76], gap="large")

    with top_left:
        st.markdown('<div class="section-title">연간 종합 통계</div>', unsafe_allow_html=True)
        _summary_card("정상 (훈련 가능)", summary["정상"], summary["total_days"], "#22c55e")
        _summary_card("주의 (고온/한랭)", summary["주의"], summary["total_days"], "#f59e0b")
        _summary_card("부분제한 / 제한", summary["부분제한"], summary["total_days"], "#ef4444")
        _summary_card("전면 중지", summary["전면 중지"], summary["total_days"], "#2563eb")
        st.markdown('<div class="section-title" style="margin-top:.9rem;">월별 가능 합계</div>', unsafe_allow_html=True)
        st.markdown('<div class="wb-panel" style="padding:.95rem 1rem;">' + _monthly_summary_html(summary["monthly"]) + '</div>', unsafe_allow_html=True)

    with top_right:
        st.markdown('<div class="section-title">{}년 {} 365일 분포 ({}시 기준)</div>'.format(year, html.escape(str(station)), int(hour)), unsafe_allow_html=True)
        fig_heat = draw_annual_day_heatmap(mat, f"{year} 연간 {metric_label} 분포", metric_label)
        fig_heat.update_layout(height=610)
        st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown('<div class="section-title" style="margin-top:.4rem;">지휘 통제 도구</div>', unsafe_allow_html=True)
        fig_daily = draw_daily_reference_chart(detail_df, metric_label, f"{detail_month}월 {detail_day}일 24시간 상세 조회")
        fig_daily.update_layout(height=340)
        st.plotly_chart(fig_daily, use_container_width=True)

    st.markdown('<div class="section-title" style="margin-top:.25rem;">상세 테이블</div>', unsafe_allow_html=True)
    prepared = prepare_daily_detail_view(detail_df.copy())
    available_cols = prepared.columns.tolist() if not prepared.empty else []
    selectable_cols = [c for c in available_cols if c != "시각"]
    default_cols = [c for c in ["실측", "기준", "체감온도", "기온", "풍속"] if c in selectable_cols]
    selected_cols = st.multiselect(
        "표시할 항목",
        options=selectable_cols,
        default=default_cols or selectable_cols,
        placeholder="시각은 항상 표시됩니다",
    )
    final_cols = ["시각"] + [c for c in selected_cols if c != "시각"]
    render_daily_detail_table(detail_df, selected_columns=final_cols, height=360)
