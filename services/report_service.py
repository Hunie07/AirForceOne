from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import pandas as pd
import streamlit as st

from core.config import API_CONFIG, DATA_DIR
from core.db import get_cursor
from services.module3_service import get_processed_df, filter_active_reports

ALL_REGIONS = ["고성군", "양구군", "철원군", "화천군", "연천군", "포천시", "강화군"]


def load_prefs():
    return st.session_state.get("prefs", {}).get("regions", [])


def save_prefs(regions):
    st.session_state.setdefault("prefs", {})["regions"] = list(regions)


def _sample_reports():
    now = datetime.now()
    rows = []
    for idx, region in enumerate(ALL_REGIONS[:5]):
        rows.append(
            {
                "BRNCH": f"B{idx+1:03d}",
                "TTL": "폭염경보" if idx % 2 == 0 else "폭염주의보",
                "PRSNTN_TM": now.strftime("%Y%m%d%H%M"),
                "SPNE_FRMNT_PRCON_CN": region,
                "RLVT_ZONE": region,
            }
        )
    return pd.DataFrame(rows)


def _normalize_report_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["BRNCH", "TTL", "PRSNTN_TM", "SPNE_FRMNT_PRCON_CN", "RLVT_ZONE"])

    if "REGION_NAME" in df.columns and "RLVT_ZONE" not in df.columns:
        df["RLVT_ZONE"] = df["REGION_NAME"]
    if "TM_IN" in df.columns and "PRSNTN_TM" not in df.columns:
        df["PRSNTN_TM"] = df["TM_IN"]
    if "REG_ID" in df.columns and "BRNCH" not in df.columns:
        df["BRNCH"] = df["REG_ID"]
    if "SPNE_FRMNT_PRCON_CN" not in df.columns:
        df["SPNE_FRMNT_PRCON_CN"] = df.get("REGION_NAME", df.get("RLVT_ZONE", ""))
    if "BRNCH" not in df.columns:
        df["BRNCH"] = df.get("REG_ID", "")
    if "TTL" not in df.columns:
        alert = df.get("alert_type", "").astype(str) if "alert_type" in df.columns else ""
        level = df.get("alert_level", "").astype(str) if "alert_level" in df.columns else ""
        df["TTL"] = (alert + " " + level).str.strip()

    cols = ["BRNCH", "TTL", "PRSNTN_TM", "SPNE_FRMNT_PRCON_CN", "RLVT_ZONE"]
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols].copy()


def _find_special_report_csv() -> Path | None:
    direct = DATA_DIR / "special_report" / "20260331.csv"
    if direct.exists():
        return direct
    special_dir = DATA_DIR / "special_report"
    if special_dir.exists():
        files = sorted(special_dir.glob("*.csv"))
        if files:
            return files[-1]
    for p in DATA_DIR.rglob("*.csv"):
        if "special_report" in str(p).lower():
            return p
    return None


def _fetch_reports_from_db() -> pd.DataFrame:
    query = '''
        SELECT
            COALESCE(brnch, reg_id, '') AS BRNCH,
            COALESCE(ttl, CONCAT(COALESCE(alert_type, ''), ' ', COALESCE(alert_level, ''))) AS TTL,
            COALESCE(prsntn_tm, DATE_FORMAT(collected_at, '%%Y%%m%%d%%H%%i')) AS PRSNTN_TM,
            COALESCE(spne_frmnt_prcon_cn, rlvt_zone, '') AS SPNE_FRMNT_PRCON_CN,
            COALESCE(rlvt_zone, '') AS RLVT_ZONE
        FROM weather_alert
        ORDER BY collected_at DESC, prsntn_tm DESC
    '''
    with get_cursor() as (cur, _):
        cur.execute(query)
        rows = cur.fetchall() or []
    return pd.DataFrame(rows)


def _fetch_reports_from_csv() -> pd.DataFrame:
    path = _find_special_report_csv()
    if path is None:
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="cp949")
    except Exception:
        return pd.DataFrame()
    return _normalize_report_frame(df)


def fetch_reports() -> pd.DataFrame:
    # 1) 실시간 수집 모듈이 DB(weather_alert)에 저장해 둔 데이터를 최우선 사용
    try:
        df_db = _fetch_reports_from_db()
        if not df_db.empty:
            return _normalize_report_frame(df_db)
    except Exception:
        pass

    # 2) DB가 비어 있으면 latest CSV 사용
    df_csv = _fetch_reports_from_csv()
    if not df_csv.empty:
        return df_csv

    # 3) 최후 fallback
    return _sample_reports()


def get_report_source_label() -> str:
    try:
        df_db = _fetch_reports_from_db()
        if not df_db.empty:
            return "DB(weather_alert)"
    except Exception:
        pass
    if _find_special_report_csv() is not None:
        return "CSV(data/special_report)"
    if API_CONFIG.get("report_data_api_service_key"):
        return "API key configured"
    return "sample data"


def classify_report(title: str) -> str:
    if "해제" in str(title):
        return "lifted"
    if "경보" in str(title):
        return "active"
    return "caution"


def badge_html(title: str) -> str:
    return classify_report(title)


def format_time(raw: str) -> str:
    raw = str(raw)
    for fmt in ("%Y%m%d%H%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).strftime("%m/%d %H:%M")
        except Exception:
            pass
    return raw


def format_datetime(raw: str) -> str:
    return format_time(raw)


def filter_by_regions(df: pd.DataFrame, regions: list[str]) -> pd.DataFrame:
    if not regions:
        return df.iloc[0:0]
    pattern = "|".join(map(re.escape, regions))
    mask = (
        df["SPNE_FRMNT_PRCON_CN"].astype(str).str.contains(pattern, na=False)
        | df["RLVT_ZONE"].astype(str).str.contains(pattern, na=False)
    )
    return df.loc[mask].copy()


def get_latest(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return get_processed_df(df).sort_values("PRSNTN_TM", ascending=False).drop_duplicates(subset="BRNCH", keep="first")


def extract_active(df_latest: pd.DataFrame) -> pd.DataFrame:
    return filter_active_reports(df_latest)
