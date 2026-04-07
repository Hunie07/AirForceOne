"""
utils/heatmap_data.py
─────────────────────
히트맵 페이지 데이터 처리 함수 모음
Streamlit 의존성 없음 — 순수 pandas/datetime 로직만 포함
"""
from __future__ import annotations

import datetime
import pandas as pd

from utils.heatmap.bar_graph_function_sp import get_unified_grade_and_color_vectorized


# ══════════════════════════════════════════════════════════════════════════════
# 연속 훈련 가용 구간 탐색
# ══════════════════════════════════════════════════════════════════════════════

def find_consecutive_available_periods(
    df: pd.DataFrame,
    sploc: str,
    year: int,
    hour: int,
    min_days: int,
    top_n: int = 5,
    blocked_dates: frozenset = frozenset(),
) -> list[dict]:
    """
    정상(grade==3) 날짜가 min_days일 이상 연속되는 구간을 탐색해
    길이 내림차순으로 top_n개 반환합니다.

    Parameters
    ----------
    df            : 전체 원본 DataFrame (load_data 반환값)
    sploc         : 지점 코드
    year          : 연도
    hour          : 시각 정수 (6 / 12 / 18)
    min_days      : 최소 연속 가용일수
    top_n         : 반환할 최대 구간 수
    blocked_dates : 이미 훈련이 예정된 날짜 집합 (frozenset[datetime.date])

    Returns
    -------
    [{"시작": "M월 D일", "종료": "M월 D일", "연속일수": N, "시작월": M}, ...]
    """
    filtered = df[
        (df["sploc"] == sploc) & (df["year"] == year) & (df["hour"] == hour)
    ].copy()
    filtered = get_unified_grade_and_color_vectorized(filtered)
    filtered["date"] = pd.to_datetime(
        dict(year=filtered["year"], month=filtered["month"], day=filtered["day"])
    )
    daily = (
        filtered.groupby("date")["unified_grade"]
        .first().sort_index().reset_index()
    )
    daily["is_normal"] = daily.apply(
        lambda r: (r["unified_grade"] == 3) and (r["date"].date() not in blocked_dates),
        axis=1,
    )

    periods: list[dict] = []
    start_idx = None

    for i, row in daily.iterrows():
        if row["is_normal"]:
            if start_idx is None:
                start_idx = i
        else:
            if start_idx is not None:
                length = i - start_idx
                if length >= min_days:
                    s = daily.loc[start_idx, "date"]
                    e = daily.loc[i - 1, "date"]
                    periods.append(_make_period(s, e, length))
                start_idx = None

    # 마지막 구간 처리
    if start_idx is not None:
        length = len(daily) - start_idx
        if length >= min_days:
            s = daily.loc[start_idx, "date"]
            e = daily.iloc[-1]["date"]
            periods.append(_make_period(s, e, length))

    periods.sort(key=lambda x: x["연속일수"], reverse=True)
    return periods[:top_n]


def _make_period(s: pd.Timestamp, e: pd.Timestamp, length: int) -> dict:
    return {
        "시작":    f"{s.month}월 {s.day}일",
        "종료":    f"{e.month}월 {e.day}일",
        "연속일수": length,
        "시작월":  s.month,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 차단 날짜 집합 생성
# ══════════════════════════════════════════════════════════════════════════════

def build_blocked_dates(blocked_schedules: list[dict]) -> frozenset:
    """
    session_state.blocked_schedules 리스트를 받아
    frozenset[datetime.date] 로 변환합니다.
    """
    dates: set[datetime.date] = set()
    for sched in blocked_schedules:
        d = sched["start"]
        while d <= sched["end"]:
            dates.add(d)
            d += datetime.timedelta(days=1)
    return frozenset(dates)


# ══════════════════════════════════════════════════════════════════════════════
# 월별 가용일수 테이블 행 생성
# ══════════════════════════════════════════════════════════════════════════════

def build_monthly_rows(m_normal: dict, m_total: dict) -> list[dict]:
    """
    월별 가용일수 딕셔너리를 st.dataframe 용 행 리스트로 변환합니다.
    """
    rows = []
    for i in range(1, 13):
        m_n = m_normal.get(i, 0)
        m_t = m_total.get(i, 0)
        m_p = f"{m_n / m_t * 100:.0f}%" if m_t > 0 else "-"
        rows.append({"월": f"{i}월", "가용일수": f"{m_n}일", "비율": m_p})
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# 24시간 테이블용 DataFrame 가공
# ══════════════════════════════════════════════════════════════════════════════

def build_daily_table_df(day_df: pd.DataFrame) -> pd.DataFrame:
    """
    하루치 원본 DataFrame을 st.dataframe 표시용으로 가공합니다.
    """
    table_df = day_df[["hour", "WCT", "ta", "ws", "hm", "rn", "dsnw"]].copy()
    table_df["hour"] = table_df["hour"].apply(lambda h: f"{int(h):02d}시")
    return table_df.rename(columns={
        "hour": "시간", "WCT": "체감(°C)", "ta": "기온",
        "ws":   "풍속", "hm":  "습도",    "rn": "강수", "dsnw": "적설",
    })
