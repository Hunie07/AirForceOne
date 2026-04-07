from __future__ import annotations

import re
from datetime import datetime
import pandas as pd


MODULE3_REGIONS = ["연천군", "철원군", "화천군", "양구군", "고성군"]


def format_report_datetime(raw: str) -> str:
    if raw is None or pd.isna(raw):
        return "-"
    raw = str(raw).strip()
    for fmt in ("%Y%m%d%H%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass
    return raw


def classify_alert_type(title: str) -> str:
    title = str(title or "")
    if "해제" in title:
        return "해제"
    if "예비" in title:
        return "예비"
    if "경보" in title:
        return "경보"
    return "주의보"


def get_processed_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["BRNCH", "TTL", "PRSNTN_TM", "SPNE_FRMNT_PRCON_CN", "RLVT_ZONE", "유형", "발표시각"])
    out = df.copy()
    out["유형"] = out["TTL"].astype(str).map(classify_alert_type)
    out["발표시각"] = out["PRSNTN_TM"].map(format_report_datetime)
    return out


def filter_active_reports(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=getattr(df, "columns", []))
    if "유형" not in df.columns:
        df = get_processed_df(df)
    return df[df["유형"].isin(["경보", "주의보"])].copy()


def extract_cancellation_time(content: str) -> str:
    if not content:
        return "미정"
    m = re.search(r"(\d{1,2}일\s*\d{1,2}시)\s*해제\s*예정", str(content))
    return m.group(1) if m else "미정"


def summarize_alerts(df_active: pd.DataFrame) -> dict:
    if df_active is None or df_active.empty:
        return {"warning": 0, "advisory": 0, "regions": 0}
    if "유형" not in df_active.columns:
        df_active = get_processed_df(df_active)
    return {
        "warning": int((df_active["유형"] == "경보").sum()),
        "advisory": int((df_active["유형"] == "주의보").sum()),
        "regions": int(df_active["RLVT_ZONE"].fillna("").astype(str).nunique()),
    }
