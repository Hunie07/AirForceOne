"""
기상청 특보 저장/조회 모듈

저장 정책
  weather_alert : API 원데이터 컬럼만 저장 (wrn·lvl·cmd 등 원본 코드 값)
                  alert_type·alert_level·rlvt_zone 등 파생 컬럼은 저장하지 않음
                  → 조회 시 load_enriched_from_db()로 Python에서 파생 컬럼 추가
  region_alert  : 5개 접경 군 연결 관계 (region_id ↔ alert_id)
"""
import pandas as pd
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text

_ACTIVE_CMDS = {"1", "2", "5", "6"}

# KMA 구역코드 → region 테이블 region_id 매핑 (5개 군)
_REG_ID_TO_REGION = {
    "L1011200": 1,  # 연천군
    "L1021300": 2,  # 철원군
    "L1021400": 3,  # 화천군
    "L1021710": 4,  # 양구군내륙
    "L1020610": 5,  # 고성군동해안 (강원)
}


def get_mysql_engine():
    """secrets.toml [mysql] 섹션에서 MySQL 접속 정보를 읽어 SQLAlchemy 엔진을 반환합니다."""
    try:
        import streamlit as st
        cfg = st.secrets["mysql"]
    except Exception:
        import tomllib
        secrets_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
        with open(secrets_path, "rb") as f:
            cfg = tomllib.load(f)["mysql"]
    url = (
        f"mysql+pymysql://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
        f"?charset={cfg.get('charset', 'utf8mb4')}"
    )
    return create_engine(url)


# ── CSV ───────────────────────────────────────────────────────────────────────

def save_to_csv(df: pd.DataFrame, data_dir: str = "data/special_report") -> None:
    """오늘 날짜 파일(YYYYMMDD.csv)에 전체 특보 데이터를 저장합니다. (덮어쓰기)"""
    if df.empty:
        return
    dir_path = Path(data_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    df.to_csv(dir_path / f"{today}.csv", index=False, encoding="utf-8-sig")


def load_snapshot(data_dir: str = "data/special_report") -> pd.DataFrame:
    """오늘 날짜 CSV를 로드합니다. 없으면 빈 DataFrame."""
    today = datetime.now().strftime("%Y%m%d")
    file_path = Path(data_dir) / f"{today}.csv"
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_csv(file_path, encoding="utf-8-sig", dtype=str)


# ── DB 저장 ───────────────────────────────────────────────────────────────────

def save_to_db(df: pd.DataFrame) -> None:
    """특보 원데이터를 DB에 저장합니다.

    weather_alert에는 API 응답 원본 컬럼(wrn·lvl·cmd·prsntn_tm 등)만 저장합니다.
    alert_type·alert_level·rlvt_zone 등 파생 컬럼은 저장하지 않으며,
    조회 시 load_enriched_from_db()로 Python에서 추가합니다.
    """
    if df.empty:
        return

    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    engine = get_mysql_engine()

    with engine.connect() as conn:
        for _, row in df.iterrows():
            reg_id = row.get("REG_ID")

            # ── 원데이터 저장 ────────────────────────────────────────────────
            result = conn.execute(text("""
                INSERT INTO weather_alert
                    (brnch, wrn, lvl, cmd, ttl, prsntn_tm, frmnt_tm, tm_in, reg_id, status, collected_at)
                VALUES
                    (:brnch, :wrn, :lvl, :cmd, :ttl, :prsntn_tm, :frmnt_tm, :tm_in, :reg_id, :status, :collected_at)
                ON DUPLICATE KEY UPDATE
                    status=VALUES(status), collected_at=VALUES(collected_at)
            """), {
                "brnch":        row.get("REGION_NAME"),
                "wrn":          row.get("WRN"),
                "lvl":          row.get("LVL"),
                "cmd":          row.get("CMD"),
                "ttl":          row.get("TTL", ""),
                "prsntn_tm":    row.get("TM_FC"),
                "frmnt_tm":     row.get("TM_EF"),
                "tm_in":        row.get("TM_IN"),
                "reg_id":       reg_id,
                "status":       "ACTIVE" if row.get("CMD") in _ACTIVE_CMDS else "INACTIVE",
                "collected_at": collected_at,
            })

            # ── 5개 군 연결 저장 ─────────────────────────────────────────────
            alert_id = result.lastrowid or conn.execute(text(
                "SELECT id FROM weather_alert WHERE reg_id=:r AND wrn=:w AND prsntn_tm=:t AND cmd=:c"
            ), {"r": reg_id, "w": row.get("WRN"), "t": row.get("TM_FC"), "c": row.get("CMD")}).scalar()
        conn.commit()


# ── DB 조회 ───────────────────────────────────────────────────────────────────

def load_raw_from_db(status: str = None) -> pd.DataFrame:
    """DB에서 원데이터 컬럼만 조회합니다.

    반환 컬럼: id, brnch, wrn, lvl, cmd, ttl, prsntn_tm, frmnt_tm, reg_id, status, collected_at
    status 인자로 'ACTIVE'/'INACTIVE' 필터 가능
    """
    engine = get_mysql_engine()
    where  = "WHERE status = :status" if status else ""
    with engine.connect() as conn:
        return pd.read_sql(text(f"""
            SELECT id, brnch, wrn, lvl, cmd, ttl, prsntn_tm, frmnt_tm, reg_id, status, collected_at
            FROM weather_alert {where}
            ORDER BY collected_at DESC
        """), conn, params={"status": status} if status else {})


def load_enriched_from_db(status: str = None) -> pd.DataFrame:
    """DB 원데이터를 조회한 뒤 파생 컬럼(alert_type·alert_level·cmd_label)을 Python에서 추가합니다.

    반환 컬럼: 원데이터 컬럼 + REGION_NAME, WRN, LVL, CMD, TM_FC, TM_EF, REG_ID,
               alert_type, alert_level, cmd_label
    """
    from utils.special_report.api import WRN_CODE_MAP, LVL_MAP, CMD_MAP

    df = load_raw_from_db(status=status)
    if df.empty:
        return df

    # 원본 API 컬럼명으로 별칭 추가 (다른 모듈과 호환)
    df["REGION_NAME"] = df["brnch"]
    df["WRN"]         = df["wrn"]
    df["LVL"]         = df["lvl"]
    df["CMD"]         = df["cmd"]
    df["TM_FC"]       = df["prsntn_tm"]
    df["TM_EF"]       = df["frmnt_tm"]
    df["REG_ID"]      = df["reg_id"]

    # 파생 컬럼 계산
    df["alert_type"]  = df["wrn"].map(WRN_CODE_MAP).fillna(df["wrn"])
    df["alert_level"] = df["lvl"].map(LVL_MAP).fillna(df["lvl"])
    df["cmd_label"]   = df["cmd"].map(CMD_MAP).fillna(df["cmd"])
    return df
