from __future__ import annotations

import html
import pandas as pd
import streamlit as st

from services import load_data
from ui.summary_cards import render_summary_cards


def _module_card(
    title: str,
    subtitle: str,
    bullets: list[str],
    button_label: str,
    target: str,
    emoji: str,
    tone: str,
) -> None:
    bullet_html = "".join(f"<li>{html.escape(item)}</li>" for item in bullets)
    st.markdown(
        f"""
        <div class="wb-module-card wb-module-card-strong">
            <div class="wb-module-head">
                <div class="wb-module-icon" style="background:{tone};">{emoji}</div>
                <div>
                    <div class="section-title" style="margin-bottom:.15rem;">{html.escape(title)}</div>
                    <div class="page-subtitle">{html.escape(subtitle)}</div>
                </div>
            </div>
            <ul class="wb-module-list">{bullet_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(button_label, key=f"open::{target}", use_container_width=True):
        st.switch_page(target)


def _brief_card(title: str, value: str, desc: str) -> None:
    st.markdown(
        f"""
        <div class="wb-brief-card">
            <div class="wb-brief-label">{html.escape(title)}</div>
            <div class="wb-brief-value">{html.escape(str(value))}</div>
            <div class="wb-brief-desc">{html.escape(desc)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_main_dashboard() -> None:
    heatmap_df = load_data()
    recent_year = int(heatmap_df["year"].max()) if not heatmap_df.empty else None
    recent_year_df = heatmap_df[heatmap_df["year"] == recent_year].copy() if recent_year is not None else pd.DataFrame()
    total_samples = int(len(recent_year_df)) if not recent_year_df.empty else 0

    st.markdown(
        """<div class="hero-card">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:18px;flex-wrap:wrap;">
                <div style="max-width:780px;">
                    <div class="page-eyebrow">MISSION CONTROL</div>
                    <div class="page-title" style="margin-bottom:.28rem;">메인 페이지</div>
                    <div class="page-subtitle">실시간 기상 영향 확인과 연간 훈련가용 분석 화면으로 빠르게 진입하는 통합 운용 허브입니다.</div>
                </div>
                <div class="wb-hero-chip-wrap">
                    <div class="wb-hero-chip">실시간 현황 대시보드</div>
                    <div class="wb-hero-chip">연간 훈련가용 판정 현황</div>
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    render_summary_cards(
        [
            ("데이터 기준", "2020~2025"),
            ("기상 데이터 기준", "운용 데이터"),
            ("적재 상태", f"{total_samples:,}건" if total_samples else "정상"),
            ("지원 지역 수", 5),
        ]
    )

    st.markdown('<div class="section-title" style="margin-top:.95rem;">바로가기</div>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")

    with left:
        _module_card(
            "실시간 현황 대시보드",
            "지역별 실시간 기상 영향, 특보 현황, 시간대별 훈련 가능 상태를 한 화면에서 확인합니다.",
            ["작전지역 기상현황 지도", "우리부대 훈련 제한 시간대", "인접부대·시간대별 상세 기상"],
            "실시간 현황 대시보드 열기",
            "pages/best_train_time.py",
            "🛡️",
            "linear-gradient(135deg, #2563eb 0%, #38bdf8 100%)",
        )

    with right:
        _module_card(
            "연간 훈련가용 판정 현황",
            "연간 분포, 연속 가용 구간, 월별·일별 상세를 기준으로 훈련 가용 패턴을 분석합니다.",
            ["연간 훈련 가용일수 종합", "히트맵 기반 패턴 분석", "월별/일별 상세 조회"],
            "연간 훈련가용 판정 현황 열기",
            "pages/heatmap.py",
            "🌡️",
            "linear-gradient(135deg, #0f766e 0%, #22c55e 100%)",
        )

    st.markdown('<div class="section-title" style="margin-top:1rem;">운용 브리프</div>', unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3, gap="large")

    with b1:
        _brief_card("실시간 운용", "기상 영향", "현재 지역 기준 기상 영향과 제한 시간대를 빠르게 확인")

    with b2:
        _brief_card("연간 분석", "가용 패턴", "365일 분포와 연속 가용 구간을 한 화면에서 분석")

    with b3:
        _brief_card("데이터 기준", "2020~2025", "기상 데이터 기준")