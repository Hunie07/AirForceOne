
from __future__ import annotations

import streamlit as st

from services import (
    fetch_reports,
    get_report_source_label,
    get_latest,
    extract_active,
    summarize_alerts,
    filter_by_regions,
    load_prefs,
    save_prefs,
)
from ui.module3_panel import render_module3_panel
from ui.summary_cards import render_summary_cards


def render_report_dashboard():
    st.markdown(
        '''
        <div class="hero-card">
            <div class="page-eyebrow">WEATHER ALERTS</div>
            <div class="page-title" style="font-size:1.8rem;">실시간 기상 특보 현황</div>
            <div class="page-subtitle">관심 지역 기준으로 최신 특보를 빠르게 확인합니다.</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    df = fetch_reports()
    options = sorted(set(df["SPNE_FRMNT_PRCON_CN"]).union(set(df["RLVT_ZONE"])))
    regions = st.multiselect("관심 지역", options, default=load_prefs(), placeholder="지역을 선택하세요")
    save_prefs(regions)

    base = filter_by_regions(df, regions) if regions else df
    latest = get_latest(base)
    active = extract_active(latest)
    stats = summarize_alerts(active)

    render_summary_cards([
        ("발효 중", len(active)),
        ("경보", stats["warning"]),
        ("주의보", stats["advisory"]),
        ("영향 지역", stats["regions"]),
    ])
    render_module3_panel(active, stats)
    st.caption(f"특보 소스: {get_report_source_label()}")
