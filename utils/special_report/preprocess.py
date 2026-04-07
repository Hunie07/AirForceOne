"""
기상청 특보 전처리 모듈
- REG_ID → 지역명 매핑
- 코드 → 한글 레이블 변환
- 발효중 필터, 지역 필터
- 시간 포맷
"""
import pandas as pd
from datetime import datetime
from utils.special_report.api import WRN_CODE_MAP, LVL_MAP, CMD_MAP, ACTIVE_CMDS


def enrich_alerts(df: pd.DataFrame, zones_df: pd.DataFrame) -> pd.DataFrame:
    """
    특보 DataFrame에 한글 레이블 컬럼을 추가합니다.
    추가 컬럼: REGION_NAME, alert_type, alert_level, cmd_label, TTL
    """
    if df.empty:
        return df
    df = df.copy()

    # REG_ID → 지역명 매핑
    zone_map = (
        zones_df.set_index("REG_ID")["REG_NAME"].to_dict()
        if not zones_df.empty else {}
    )
    df["REGION_NAME"] = df["REG_ID"].map(zone_map).fillna(df["REG_ID"])

    # 코드 → 한글
    df["alert_type"]  = df["WRN"].map(WRN_CODE_MAP).fillna(df["WRN"])
    df["alert_level"] = df["LVL"].map(LVL_MAP).fillna(df["LVL"])
    df["cmd_label"]   = df["CMD"].map(CMD_MAP).fillna(df["CMD"])

    # TTL: 타임라인 표시용 제목
    df["TTL"] = df["alert_type"] + " " + df["alert_level"]

    return df


def filter_active(df: pd.DataFrame) -> pd.DataFrame:
    """발효 중인 특보만 반환 (해제/대치해제/변경해제 제외)."""
    if df.empty:
        return df
    return df[df["CMD"].isin(ACTIVE_CMDS)].copy()


def filter_pre(df: pd.DataFrame) -> pd.DataFrame:
    """예비특보만 반환 (LVL=1)."""
    if df.empty:
        return df
    return df[df["LVL"] == "1"].copy()


def format_dt(raw: str) -> str:
    """'202603270600' → '2026-03-27 06:00'"""
    try:
        return datetime.strptime(str(raw).strip(), "%Y%m%d%H%M").strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(raw)


def format_time(raw: str) -> str:
    """'202603270600' → '06:00'"""
    try:
        return datetime.strptime(str(raw).strip(), "%Y%m%d%H%M").strftime("%H:%M")
    except Exception:
        return str(raw)
