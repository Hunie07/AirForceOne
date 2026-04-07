"""
W-BOSS 데이터 로더 및 DataFrame 빌더
────────────────────────────────────
- 훈련 판정 DataFrame 생성 (요약·타임라인·상세)
- 특보 데이터 수집·저장·변환
"""
import pandas as pd
import streamlit as st

from utils.best_train.config import AREA_INFO, ALL_HOURS
from utils.best_train.training_logic import get_status
from utils.realtime.utils import (
    STATUS_EMOJI, DUTY_CUR, DUTY_NEXT, DAY_LABELS,
    ALERT_TRAINING_TYPES, MARITIME_KEYWORDS,
    apply_alert_to_status,
)

# ── 지역 목록 (AREA_INFO 삽입 순서 = 표시 순서) ────────────────────────────────
REGIONS: list[str] = list(AREA_INFO.keys())
_REGION_TO_GUN: dict[str, str] = {r: r + "군" for r in REGIONS}

# ── 특보 영향 테이블 컬럼 순서 ────────────────────────────────────────────────
IMPACT_REPORT_TYPES: list[str] = ["폭염", "한파", "호우", "태풍", "건조", "강풍", "황사", "대설"]

# ── 특보 모듈 임포트 (실패 시 비활성화) ──────────────────────────────────────
try:
    from utils.special_report.api import (
        get_auth_key, fetch_alert_zones, fetch_alert_data,
        REGIONS as ALERT_REGIONS,
        REGION_PARENT_MAP,
    )
    from utils.special_report.preprocess import enrich_alerts, filter_active, format_dt
    from utils.special_report.storage import save_to_csv, save_to_db
    from utils.special_report.query import get_stats
    SPECIAL_AVAILABLE = True
    SPECIAL_ERROR = ""
except Exception as _e:
    SPECIAL_AVAILABLE = False
    SPECIAL_ERROR = str(_e)
    ALERT_REGIONS: list = []
    REGION_PARENT_MAP: dict = {}

    def format_dt(raw: str) -> str:  # noqa: F811
        return str(raw)


# ══════════════════════════════════════════════════════════════════════════════
# 셀 값 생성
# ══════════════════════════════════════════════════════════════════════════════

def cell(
    val: float,
    month: int,
    alert_level: str | None = None,
    alert_type:  str | None = None,  # noqa: ARG001
) -> str:
    """온도값 + 특보 오버라이드 → '13.3 🟢 가능' 형태 문자열."""
    base, _ = get_status(val, month)
    final   = apply_alert_to_status(base, alert_level)
    return f"{val:.1f}  {STATUS_EMOJI[final]} {final}"


# ══════════════════════════════════════════════════════════════════════════════
# 훈련 가능 DataFrame 빌더
# ══════════════════════════════════════════════════════════════════════════════

def build_area_df(
    df: pd.DataFrame,
    date: str,
    next_date: str | None,
    month: int,
    target_col: str,
    alert_map: dict | None = None,
) -> pd.DataFrame:
    """인접 지역 × D일 06시~D+1일 05시 훈련 가능 여부 DataFrame.

    alert_map: {지역명: (alert_level, alert_type)} — 오늘 날짜 선택 시에만 전달
    """
    alert_map = alert_map or {}
    rows = []
    for region in REGIONS:
        al, at   = alert_map.get(region, (None, None))
        row      = {"지역": region}
        rdf_cur  = df[(df["지역"] == region) & (df["날짜"] == date)]
        rdf_next = (
            df[(df["지역"] == region) & (df["날짜"] == next_date)]
            if next_date else pd.DataFrame()
        )
        for hr in DUTY_CUR:
            sub      = rdf_cur[rdf_cur["시간"] == hr]
            col_name = f"{int(hr):02d}시"
            row[col_name] = (
                cell(sub.iloc[0][target_col], month, al, at)
                if not sub.empty and pd.notna(sub.iloc[0][target_col])
                else "-"
            )
        for hr in DUTY_NEXT:
            col_name = f"익일 {int(hr):02d}시"
            if rdf_next.empty:
                row[col_name] = "-"
            else:
                sub = rdf_next[rdf_next["시간"] == hr]
                row[col_name] = (
                    cell(sub.iloc[0][target_col], month, al, at)
                    if not sub.empty and pd.notna(sub.iloc[0][target_col])
                    else "-"
                )
        rows.append(row)
    return pd.DataFrame(rows).set_index("지역")


def build_summary_df(
    df: pd.DataFrame,
    region: str,
    dates: list,
    month: int,
    target_col: str,
    alert_level: str | None = None,
    alert_type:  str | None = None,
) -> pd.DataFrame:
    """선택 지역 오늘/내일/모레 × D일 06시~D+1일 05시 훈련 가능 여부 DataFrame.

    alert_level/alert_type: 오늘(i==0) 행에만 적용, 내일·모레는 온도 기준만 사용.
    """
    rows = []
    for i, date in enumerate(dates[:3]):
        label     = f"{DAY_LABELS[i]} ({date})"
        row       = {"날짜": label}
        next_date = dates[i + 1] if i + 1 < len(dates) else None
        rdf_cur   = df[(df["지역"] == region) & (df["날짜"] == date)]
        rdf_next  = (
            df[(df["지역"] == region) & (df["날짜"] == next_date)]
            if next_date else pd.DataFrame()
        )
        al = alert_level if i == 0 else None
        at = alert_type  if i == 0 else None
        for hr in DUTY_CUR:
            sub      = rdf_cur[rdf_cur["시간"] == hr]
            col_name = f"{int(hr):02d}시"
            row[col_name] = (
                cell(sub.iloc[0][target_col], month, al, at)
                if not sub.empty and pd.notna(sub.iloc[0][target_col])
                else "-"
            )
        for hr in DUTY_NEXT:
            col_name = f"익일 {int(hr):02d}시"
            if rdf_next.empty:
                row[col_name] = "-"
            else:
                sub = rdf_next[rdf_next["시간"] == hr]
                row[col_name] = (
                    cell(sub.iloc[0][target_col], month, al, at)
                    if not sub.empty and pd.notna(sub.iloc[0][target_col])
                    else "-"
                )
        rows.append(row)
    return pd.DataFrame(rows).set_index("날짜")


def build_detail_df(df: pd.DataFrame, region: str, date: str) -> pd.DataFrame:
    """상세 기상 현황 (6개 지표 × 전시간대) DataFrame."""
    metrics = [
        ("기온",     "℃"),
        ("풍속",     "m/s"),
        ("습도",     "%"),
        ("강수량",   "mm"),
        ("체감온도", "℃"),
        ("온도지수", "℃"),
    ]
    rdf  = df[(df["지역"] == region) & (df["날짜"] == date)]
    rows = []
    for metric, unit in metrics:
        row = {"항목": f"{metric}({unit})"}
        for hr in ALL_HOURS:
            sub      = rdf[rdf["시간"] == hr]
            col_name = f"{int(hr):02d}시"
            if sub.empty or metric not in sub.columns:
                row[col_name] = "-"
            else:
                val           = sub.iloc[0][metric]
                row[col_name] = f"{val:.1f}" if pd.notna(val) else "-"
        rows.append(row)
    return pd.DataFrame(rows).set_index("항목")


# ══════════════════════════════════════════════════════════════════════════════
# 특보 관련 헬퍼
# ══════════════════════════════════════════════════════════════════════════════

def get_region_worst_alert(
    region: str,
    active_df: pd.DataFrame,
) -> tuple[str | None, str | None]:
    """발효중 특보 중 훈련 영향 최고 수준 반환 → (alert_level, alert_type)."""
    if active_df.empty or not SPECIAL_AVAILABLE:
        return None, None
    gun      = _REGION_TO_GUN.get(region, region + "군")
    parents  = REGION_PARENT_MAP.get(gun, [])
    priority = {"경보": 3, "주의보": 2, "예비": 1}
    best_prio, best_level, best_type = 0, None, None
    for _, row in active_df.iterrows():
        rname  = row.get("REGION_NAME", "")
        atype  = row.get("alert_type",  "")
        alevel = row.get("alert_level", "")
        if atype not in ALERT_TRAINING_TYPES:
            continue
        if any(kw in rname for kw in MARITIME_KEYWORDS):
            continue
        if gun in rname or any(p in rname for p in parents) or "전국" in rname:
            prio = priority.get(alevel, 0)
            if prio > best_prio:
                best_prio, best_level, best_type = prio, alevel, atype
    return best_level, best_type


def build_timeline_df(active_df: pd.DataFrame) -> pd.DataFrame:
    """발효중 특보를 타임라인 표시용 DataFrame으로 변환."""
    if active_df.empty:
        return pd.DataFrame(columns=["지역", "특보종류", "특보수준", "발효시각", "발표시각"])
    rows = []
    for _, row in active_df.iterrows():
        rows.append({
            "지역":     row.get("REGION_NAME", "-"),
            "특보종류": row.get("alert_type",  "-"),
            "특보수준": row.get("alert_level", "-"),
            "발효시각": format_dt(row.get("TM_EF", "")),
            "발표시각": format_dt(row.get("TM_FC", "")),
        })
    return pd.DataFrame(rows)


def filter_timeline_by_region(active_df: pd.DataFrame, region: str) -> pd.DataFrame:
    """선택 지역에 해당하는 특보만 필터링.

    - 군 이름 직접 포함  → 원래 이름 유지       (예: "연천군")
    - 상위 행정구역 포함 → "{도}도 특보"         (예: "강원도 특보")
    - 전국 단위          → "전국 특보"
    해양 구역(동해안·앞바다 등)은 제외.
    """
    if active_df.empty:
        return pd.DataFrame(columns=active_df.columns if not active_df.empty else [])
    gun     = _REGION_TO_GUN.get(region, region + "군")
    parents = REGION_PARENT_MAP.get(gun, [])
    matched = []
    for _, row in active_df.iterrows():
        name        = row.get("REGION_NAME", "")
        is_maritime = any(kw in name for kw in MARITIME_KEYWORDS)
        new_row     = row.copy()
        if gun in name:
            matched.append(new_row)
        elif not is_maritime:
            parent_hit = next((p for p in parents if p in name), None)
            if parent_hit:
                new_row["REGION_NAME"] = f"{parent_hit}도 특보"
                matched.append(new_row)
            elif "전국" in name:
                new_row["REGION_NAME"] = "전국 특보"
                matched.append(new_row)
    if not matched:
        return pd.DataFrame(columns=active_df.columns)
    return pd.DataFrame(matched).reset_index(drop=True)


def build_impact_df(active_df: pd.DataFrame) -> pd.DataFrame:
    """5개 접경 군 × 특보종류 영향 매핑 DataFrame.

    셀 값: '경보' / '주의보' / '예비' / '-'
    """
    impact   = {g: {t: "-" for t in IMPACT_REPORT_TYPES} for g in ALERT_REGIONS}
    priority = {"경보": 3, "주의보": 2, "예비": 1, "-": 0}

    if not active_df.empty:
        for _, row in active_df.iterrows():
            region_name = row.get("REGION_NAME", "")
            alert_type  = row.get("alert_type",  "")
            alert_level = row.get("alert_level", "")
            if alert_type not in IMPACT_REPORT_TYPES:
                continue
            for gun in ALERT_REGIONS:
                if (
                    gun in region_name
                    or any(p in region_name for p in REGION_PARENT_MAP.get(gun, []))
                    or "전국" in region_name
                ):
                    if priority.get(alert_level, 0) > priority.get(impact[gun][alert_type], 0):
                        impact[gun][alert_type] = alert_level

    rows = [{"지역": g, **impact[g]} for g in ALERT_REGIONS]
    result = pd.DataFrame(rows).set_index("지역")
    result.columns.name = "특보종류"
    return result


# ══════════════════════════════════════════════════════════════════════════════
# 특보 수집·저장
# ══════════════════════════════════════════════════════════════════════════════

def load_special_report() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """특보 수집·전처리 → (enriched_df, active_df, stats)."""
    empty = pd.DataFrame()
    if not SPECIAL_AVAILABLE:
        return empty, empty, {}
    try:
        auth_key = get_auth_key()
        zones_df = fetch_alert_zones(auth_key)
        raw_df   = fetch_alert_data(auth_key)
        if raw_df.empty:
            return empty, empty, {}
        enriched = enrich_alerts(raw_df, zones_df)
        active   = filter_active(enriched)
        stats    = get_stats(enriched)
        return enriched, active, stats
    except Exception as e:
        st.warning(f"⚠️ 특보 데이터 수집 오류: {e}")
        return empty, empty, {}


def save_special_report(enriched_df: pd.DataFrame) -> None:
    """특보 데이터를 CSV 및 DB에 저장."""
    if not SPECIAL_AVAILABLE:
        return
    try:
        save_to_csv(enriched_df)
    except Exception as e:
        st.warning(f"⚠️ 특보 CSV 저장 실패: {e}")
    try:
        save_to_db(enriched_df)
    except Exception as e:
        st.warning(f"⚠️ 특보 DB 저장 실패: {e}")
