"""
utils/heatmap_bar_graph_function_sp.py
───────────────────────────────────────
체감온도 분석 순수 함수 모듈 - 1년 365일 히트맵 전용 버전
원본 훈련 통제 기준표 기반 8단 등급 산출 및 통계 로직 (🚀최적화 적용)

위치: utils/
CSV 경로 기준: 프로젝트 루트 기준 data/날씨/체감온도(...).csv
  프로젝트 루트
  ├── data/
  │   └── 날씨/
  │       └── 체감온도(2020~2025, 시간별AOS).csv
  ├── pages/
  │   └── heatmap.py
  └── utils/
      └── heatmap_bar_graph_function_sp.py
"""
from __future__ import annotations

import os as _os
import pandas as pd
import streamlit as st
import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
# 1. 경로 · 상수
# ═══════════════════════════════════════════════════════════════════════════════
_HEATMAP_DIR  = _os.path.dirname(_os.path.abspath(__file__))   # utils/heatmap/
_UTILS_DIR    = _os.path.dirname(_HEATMAP_DIR)                  # utils/
_PROJECT_ROOT = _os.path.dirname(_UTILS_DIR)                    # AirForceOne/

CSV_PATH = _os.path.join(_PROJECT_ROOT, "data", "날씨", "체감온도(2020~2025, 시간별AOS).csv")

ALL_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]
ALL_MONTHS = list(range(1, 13))


def _read_csv_with_fallback(path: str, **kwargs) -> pd.DataFrame:
    last_error = None
    for enc in ("utf-8", "utf-8-sig", "cp949"):
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError as e:
            last_error = e
            continue
        except TypeError:
            return pd.read_csv(path, **kwargs)
    if last_error is not None:
        raise last_error
    return pd.read_csv(path, **kwargs)

# ═══════════════════════════════════════════════════════════════════════════════
# 2. 데이터 로드 / 전처리 (캐싱)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner="📂 데이터 로드 중…")
def load_data(path: str = CSV_PATH) -> pd.DataFrame:
    df = _read_csv_with_fallback(
        path,
        usecols=["year", "month", "day", "hour", "region", "sploc",
                 "ta", "ws", "hm", "WCT", "rn", "dsnw"],
    )
    df["rn"]   = df["rn"].fillna(0)
    df["dsnw"] = df["dsnw"].fillna(0)

    # 5월~9월 체감온도: 의복 보정치(+3.0) 제거
    df.loc[df["month"].isin([5, 6, 7, 8, 9]), "WCT"] -= 3.0

    return df

# ═══════════════════════════════════════════════════════════════════════════════
# 3. 8단 등급 산출 (벡터화)
# ═══════════════════════════════════════════════════════════════════════════════

def get_unified_grade_and_color_vectorized(df: pd.DataFrame) -> pd.DataFrame:
    """
    WCT(체감온도) 값을 기준으로 훈련 가부 8단 등급을 산출합니다.

    등급 매핑
    ─────────
    7 : 고온 중지     (WCT ≥ 32.0)
    6 : 고온 제한     (31.0 ≤ WCT < 32.0)
    5 : 고온 부분제한 (29.5 ≤ WCT < 31.0)
    4 : 고온 주의     (26.5 ≤ WCT < 29.5)
    3 : 정상 가용     (그 외 구간)
    2 : 한랭 주의     (-18.0 < WCT ≤ -10.0)
    1 : 한랭 제한     (-24.0 < WCT ≤ -18.0)
    0 : 한랭 중지     (WCT ≤ -24.0)
    """
    wct    = df["WCT"]
    grades = pd.Series(np.nan, index=df.index, dtype="float")

    # 고온 기준
    cond7 = (wct >= 32.0)
    cond6 = (wct >= 31.0) & (wct < 32.0)
    cond5 = (wct >= 29.5) & (wct < 31.0)
    cond4 = (wct >= 26.5) & (wct < 29.5)

    # 한랭 기준
    cond0 = (wct <= -24.0)
    cond1 = (wct > -24.0) & (wct <= -18.0)
    cond2 = (wct > -18.0) & (wct <= -10.0)

    # 정상
    cond3 = ~(cond7 | cond6 | cond5 | cond4 | cond0 | cond1 | cond2 | pd.isna(wct))

    grades[cond7] = 7; grades[cond6] = 6; grades[cond5] = 5; grades[cond4] = 4
    grades[cond3] = 3
    grades[cond2] = 2; grades[cond1] = 1; grades[cond0] = 0

    status_map = {
        7.0: "고온 중지", 6.0: "고온 제한", 5.0: "고온 부분제한", 4.0: "고온 주의",
        3.0: "정상 가용",
        2.0: "한랭 주의",  1.0: "한랭 제한",  0.0: "한랭 중지",
    }

    df["unified_grade"]  = grades
    df["unified_status"] = grades.map(status_map)
    return df

# ═══════════════════════════════════════════════════════════════════════════════
# 4. 연간 피벗 통합 캐싱 (🚀 8배 속도 향상)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def get_all_yearly_pivots(
    df: pd.DataFrame, sploc: str, year: int, hour: int
) -> dict:
    """
    8개 컬럼의 피벗 연산을 한 번에 묶어 캐싱합니다.

    Returns
    -------
    dict 키: unified_grade, unified_status, WCT, ta, ws, hm, rn, dsnw
    """
    filtered = df[
        (df["sploc"] == sploc) & (df["year"] == year) & (df["hour"] == hour)
    ].copy()
    filtered = get_unified_grade_and_color_vectorized(filtered)

    cols_to_pivot = ["unified_grade", "unified_status", "WCT", "ta", "ws", "hm", "rn", "dsnw"]
    pivots: dict = {}

    for col in cols_to_pivot:
        pivot = pd.pivot_table(
            filtered, values=col, index="month", columns="day", aggfunc="first"
        )
        pivot = pivot.reindex(index=ALL_MONTHS, columns=list(range(1, 32)))
        pivots[col] = pivot

    return pivots


def prepare_heatmap_pivot_data_yearly(
    df: pd.DataFrame, sploc: str, year: int, hour: int, value_col: str
) -> pd.DataFrame:
    """하위 호환성 유지용 단일 피벗 래퍼."""
    return get_all_yearly_pivots(df, sploc, year, hour)[value_col]

# ═══════════════════════════════════════════════════════════════════════════════
# 5. 연간 통계 계산 (🚀 캐싱 적용)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def calculate_yearly_statistics(
    df: pd.DataFrame, sploc: str, year: int, hour: int
) -> tuple[dict, dict, dict]:
    """
    월별 / 연간 훈련 가용일수 통계를 계산합니다.

    Returns
    -------
    monthly_normal : {월: 정상일수}
    monthly_total  : {월: 전체일수}
    yearly_stats   : {total, normal, caution, limit, stop}
    """
    filtered = df[
        (df["sploc"] == sploc) & (df["year"] == year) & (df["hour"] == hour)
    ].copy()
    filtered = get_unified_grade_and_color_vectorized(filtered)

    monthly_normal: dict = {}
    monthly_total:  dict = {}
    for m in range(1, 13):
        m_data = filtered[filtered["month"] == m]["unified_grade"].dropna()
        monthly_normal[m] = int(sum(m_data == 3))
        monthly_total[m]  = len(m_data)

    y_valid = filtered["unified_grade"].dropna()
    yearly_stats = {
        "total":   len(y_valid),
        "normal":  int(sum(y_valid == 3)),
        "caution": int(sum((y_valid == 2) | (y_valid == 4))),
        "limit":   int(sum((y_valid == 1) | (y_valid == 5) | (y_valid == 6))),
        "stop":    int(sum((y_valid == 0) | (y_valid == 7))),
    }
    return monthly_normal, monthly_total, yearly_stats
