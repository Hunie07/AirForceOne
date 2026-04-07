"""
연간 훈련가용 판정 히트맵 페이지 
────────────────
디렉터리 구조
  app.py                              ← 메인 앱
  pages/
    best_train_time.py                ← 상세페이지1. 실시간 현황 대시보드 페이지
    heatmap.py                        ← 상세페이지2. 연간 훈련 가용일 히트맵 페이지
    utils/
        best_train/
            config.py                 ← API 키 · 지역 좌표 · 임계값
            weather_api.py            ← 단기예보 API 수집
            training_logic.py         ← 판정 로직 (get_status 등)
            forecast_pipeline.py      ← CSV·DB 저장 파이프라인
        real_time/
            utils.py                  ← 공통 상수 · 판정 유틸리티
            loaders.py                ← DataFrame 빌더 · 특보 수집
            charts.py                 ← Folium 지도 · Altair 차트
        special_report/
            api.py                    ← 특보 API 수집
            preprocess.py             ← 특보 전처리
            storage.py                ← 특보 저장
            query.py                  ← 특보 통계·조회
        heatmap/
            config.py                 ← 설정값 (상수 / 매핑 / 기본값)
            data.py                   ← 데이터 처리 함수
            figures.py                ← Plotly Figure 생성 함수
            ui_components.py          ← Streamlit UI 렌더링 함수
            bar_graph_function_sp.py  ← 기상 데이터 로드 / 등급 산출
"""
import sys
import os

# ── 경로 등록 ────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))   # pages/
_ROOT = os.path.dirname(_HERE)                        # 프로젝트 루트

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── 외부 임포트 ──────────────────────────────────────────────────────────────
import streamlit as st

from services import init_session
from ui import render_sidebar_ui, render_streamlit_base_style
from utils.heatmap.bar_graph_function_sp import CSV_PATH, load_data

from utils.heatmap.config import LOCATION_MAPPING, EXCLUDED_SPLOCS
from utils.heatmap.ui_components import (
    init_session_state,
    render_header,
    render_filter_bar,
    render_yearly_stats,
    render_heatmap,
    render_schedule_panel,
    render_monthly_table,
    render_daily_detail,
)

# ══════════════════════════════════════════════════════════════════════════════
# 페이지 설정
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="W-BOSS · 연간 훈련가용 판정 현황",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_streamlit_base_style()
init_session()
render_sidebar_ui("연간 훈련가용 판정 현황")

# ══════════════════════════════════════════════════════════════════════════════
# 데이터 로드 & 세션 초기화
# ══════════════════════════════════════════════════════════════════════════════
df     = load_data(CSV_PATH)
splocs = sorted([s for s in df["sploc"].unique() if s not in EXCLUDED_SPLOCS])

init_session_state()

# ══════════════════════════════════════════════════════════════════════════════
# UI 렌더링
# ══════════════════════════════════════════════════════════════════════════════

# 헤더
render_header()

# 필터 (지역 / 연도 / 시간)
render_filter_bar(splocs)

st.write("")
disp_name = LOCATION_MAPPING.get(st.session_state.sel_sploc, st.session_state.sel_sploc)

# ── Row 1: 훈련 가용일수 종합 | 히트맵 | 연속 가용 구간 추천 ────────────────
col_stat, col_heatmap, col_schedule = st.columns([3.3, 7.5, 3.4])

with col_stat:
    m_normal, m_total = render_yearly_stats(df)   # Row 2 에서 재사용

with col_heatmap:
    render_heatmap(df, disp_name)

with col_schedule:
    render_schedule_panel(df)

# ── Row 2: 월별 훈련 가용일수 | 일별 기상 상세 조회 ─────────────────────────
st.write("")
col_monthly, col_detail = st.columns([2, 3])

with col_monthly:
    render_monthly_table(m_normal, m_total)

with col_detail:
    render_daily_detail(df)
