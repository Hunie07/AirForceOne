from __future__ import annotations

import pandas as pd
import streamlit as st

from services import (
    fetch_reports,
    get_report_source_label,
    get_latest,
    extract_active,
    summarize_alerts,
    load_data,
    get_all_yearly_pivots,
    calculate_yearly_statistics,
)
from ui.components import draw_bar_chart, draw_heatmap_chart, draw_multi_line_chart
from ui.module3_anomaly_panel import render_module3_anomaly_panel
from ui.summary_cards import render_summary_cards
from ui.alert_feed_panel import render_alert_feed_panel


def render_dashboard():
    st.markdown(
        '''
        <div class="hero-card">
            <div style="display:flex;align-items:center;gap:14px;">
                <div style="width:56px;height:56px;border-radius:18px;background:linear-gradient(135deg,var(--wb-primary),#38bdf8);display:flex;align-items:center;justify-content:center;font-size:26px;color:white;">🌤️</div>
                <div>
                    <div class="page-title" style="font-size:2.1rem;margin-bottom:.16rem;">W-BOSS Dashboard</div>
                    <div class="page-subtitle">실시간 특보와 훈련 가능성 지표를 한 화면에서 확인합니다.</div>
                </div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    reports = fetch_reports()
    latest = get_latest(reports)
    active = extract_active(latest)
    summary_stats = summarize_alerts(active)
    source_label = get_report_source_label()

    heatmap_df = load_data()
    pivot = get_all_yearly_pivots(heatmap_df)
    yearly_stats = calculate_yearly_statistics(heatmap_df)
    summary = (
        heatmap_df.groupby("year", as_index=False)["score"].mean().rename(columns={"score": "평균 점수"})
        if not heatmap_df.empty else pd.DataFrame(columns=["year", "평균 점수"])
    )

    render_summary_cards([
        ("발효 중 특보", len(active)),
        ("경보", summary_stats["warning"]),
        ("주의보", summary_stats["advisory"]),
        ("영향 지역", summary_stats["regions"]),
    ])

    row1_left, row1_right = st.columns([1.35, 1.0], gap="large")
    with row1_left:
        st.markdown('<div class="section-title" style="margin-top:.8rem;">연간 운영 가능성 패턴</div>', unsafe_allow_html=True)
        fig_bar = draw_bar_chart(summary, "year", "평균 점수", "연도별 평균 점수")
        fig_bar.update_layout(height=420)
        st.plotly_chart(fig_bar, use_container_width=True)
    with row1_right:
        st.markdown('<div class="section-title" style="margin-top:.8rem;">모듈 3 · 비정상 감지</div>', unsafe_allow_html=True)
        render_module3_anomaly_panel()

    row2_left, row2_right = st.columns([1.35, 1.0], gap="large")
    with row2_left:
        st.markdown('<div class="section-title" style="margin-top:.2rem;">월별 훈련 가능성 분포</div>', unsafe_allow_html=True)
        fig_heat = draw_heatmap_chart(pivot, "연도별 월간 히트맵")
        fig_heat.update_layout(height=430)
        st.plotly_chart(fig_heat, use_container_width=True)
    with row2_right:
        st.markdown('<div class="section-title" style="margin-top:.2rem;">실시간 특보 요약</div>', unsafe_allow_html=True)
        render_alert_feed_panel(active)

    st.markdown('<div class="section-title" style="margin-top:.15rem;">연도별 통계 추이</div>', unsafe_allow_html=True)
    fig_line = draw_multi_line_chart(
        yearly_stats,
        "year",
        [("mean_score", "평균"), ("min_score", "최저"), ("max_score", "최고")],
        "연도별 통계 추이",
    )
    fig_line.update_layout(height=320)
    st.plotly_chart(fig_line, use_container_width=True)

    st.caption(f"특보 소스: {source_label}")
