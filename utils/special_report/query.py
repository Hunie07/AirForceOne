"""
기상청 특보 조회/통계 모듈
- 통계 집계
"""
import pandas as pd
from utils.special_report.preprocess import filter_active, filter_pre

KEY_COLS = ["REG_ID", "WRN", "TM_FC"]


def get_stats(df: pd.DataFrame) -> dict:
    """전체·발효·예비·경보·주의보 건수 및 유형별 건수 반환."""
    if df.empty:
        return {"total": 0, "active": 0, "pre": 0, "warning": 0, "advisory": 0, "by_type": {}}
    active  = filter_active(df)
    pre     = filter_pre(active)
    by_type = active["alert_type"].value_counts().to_dict() if not active.empty else {}
    return {
        "total":    len(df),
        "active":   len(active),
        "pre":      len(pre),
        "warning":  int((active["LVL"] == "3").sum()) if not active.empty else 0,
        "advisory": int((active["LVL"] == "2").sum()) if not active.empty else 0,
        "by_type":  by_type,
    }
