"""
훈련 가능 여부 판정 로직.
Streamlit 에 의존하지 않으므로 pytest 로 단독 테스트 가능.
"""
import numpy as np
import pandas as pd

from utils.best_train.config import (
    SUMMER_MONTHS,
    SUMMER_THRESHOLDS,
    WINTER_THRESHOLDS,
    DAY_HOURS,
)


# ── 체감온도 / 온도지수 계산 ───────────────────────────────────────────────

def compute_apparent_temperatures(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame 에 '체감온도', '온도지수' 컬럼을 추가해 반환.

    Parameters
    ----------
    df : 기온(TMP), 풍속(WSD), 습도(REH) 컬럼을 포함한 DataFrame
    """
    df = df.copy()
    T = df['기온']
    W = df['풍속']
    H = df['습도']
    months = df['날짜'].str.split('/').str[0].astype(int)

    # ── 여름: 온도지수 (WBGT 추정) ──────────────────────────────────────
    tw = (
        T * np.arctan(0.151977 * (H + 8.313659) ** 0.5)
        + np.arctan(T + H)
        - np.arctan(H - 1.676331)
        + 0.00391838 * (H ** 1.5) * np.arctan(0.023101 * H)
        - 4.686035
    )
    summer_val = -0.2442 + 0.55399 * tw + 0.45535 * T - 0.0022 * (tw ** 2) + 0.00278 * tw * T + 3.0

    # ── 겨울: 풍속 냉각 지수 ────────────────────────────────────────────
    V_kmh  = W * 3.6
    V_safe = V_kmh.replace(0, 0.1)
    winter_val = 13.12 + 0.6215 * T - 11.37 * (V_safe ** 0.16) + 0.3965 * T * (V_safe ** 0.16)

    df['체감온도'] = np.where(months.isin(SUMMER_MONTHS), summer_val, winter_val).round(1)
    df['온도지수']  = (df['체감온도'] - 3).round(1)
    return df


# ── 판정 ──────────────────────────────────────────────────────────────────

def get_status(val: float, month: int) -> tuple[str, str]:
    """
    온도 값과 월로 훈련 판정을 반환.

    Returns
    -------
    (판정 텍스트, 색상 키)  예: ('제한', 'restrict')
    """
    thresholds = SUMMER_THRESHOLDS if month in SUMMER_MONTHS else WINTER_THRESHOLDS
    for threshold, label, key in thresholds:
        if month in SUMMER_MONTHS:
            if val >= threshold:
                return label, key
        else:
            if val <= threshold:
                return label, key
    return '가능', 'go'


# ── 연속 구간 계산 ─────────────────────────────────────────────────────────

def get_continuous_ranges(
    today_vals: list[tuple[int, float, str]],
    target_statuses: list[str],
) -> list[tuple[int, int]]:
    """
    (시각, 온도값, 판정) 리스트에서 target_statuses 에 해당하는
    연속 시간 구간을 추출.

    Returns
    -------
    [(시작시각, 종료시각), ...] — 길이 내림차순 정렬
    """
    ranges: list[tuple[int, int]] = []
    start: int | None = None

    for h, _, status in today_vals:
        if status in target_statuses:
            if start is None:
                start = h
        else:
            if start is not None:
                ranges.append((start, h - 1))
                start = None

    if start is not None and today_vals:
        ranges.append((start, today_vals[-1][0]))

    return sorted(ranges, key=lambda x: x[1] - x[0], reverse=True)


def build_today_vals(
    pivot: pd.DataFrame,
    today: str,
    month: int,
) -> list[tuple[int, float, str]]:
    """
    날짜별 pivot 에서 오늘(주간) 시간대의 (시각, 값, 판정) 리스트 생성.
    """
    today_vals: list[tuple[int, float, str]] = []
    for hr in DAY_HOURS:
        if hr in pivot.columns and today in pivot.index:
            val = pivot.loc[today, hr]
            if pd.notna(val):
                today_vals.append((int(hr), val, get_status(val, month)[0]))
    return today_vals


