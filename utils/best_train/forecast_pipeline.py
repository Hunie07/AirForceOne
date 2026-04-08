"""
단기예보 수집 파이프라인 — utils/best_train_forecast_pipeline.py
────────────────────────────────────────────────────────────────
best_train_time.py (Streamlit 앱) 실행 시 자동으로 호출된다.

흐름
  1단계  전처리            preprocess_forecast_df()
           └─ get_weather_data() 결과(DataFrame)를 그대로 받아 사용
           └─ API 이중 호출 없음
  2단계  날짜 범위 통합 CSV  save_to_dated_csv()
           └─ data/forecast/260330_260401_short_term_weather_data.csv
  3단계  MySQL 저장        save_to_db()
           └─ .streamlit/secrets.toml [mysql] 또는 st.secrets 자동 감지
────────────────────────────────────────────────────────────────
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# ── 같은 utils 패키지 내부 모듈 (상대 import) ───────────────────────────────
from utils.best_train.config import AREA_INFO
from utils.best_train.weather_api import _fetch_area
from utils.best_train.training_logic import compute_apparent_temperatures

# CSV 저장 기준 디렉터리 (프로젝트 루트 기준 상대경로 — 실행 위치는 항상 루트)
# DEFAULT_DATA_DIR = "data/forecast"
DEFAULT_DATA_DIR = "/tmp/forecast"  # Streamlit Cloud 전용

# secrets.toml 위치: utils/ 의 두 단계 위 → 프로젝트 루트/.streamlit/
_SECRETS_PATH = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"


# ══════════════════════════════════════════════════════════════════════════════
# 1단계 · 전처리
# ══════════════════════════════════════════════════════════════════════════════

def preprocess_forecast_df(
    df: pd.DataFrame,
    base_date: str,
    base_time: str,
) -> pd.DataFrame:
    """
    DB 저장용 datetime 컬럼 두 개를 추가한다.

    날짜 컬럼 형식
    --------------
    get_weather_data() 가 반환하는 '날짜' 컬럼은 'M/D' 형식.  예) '3/30'
    '시간' 컬럼은 두 자리 문자열.                               예) '06'
    올해 연도와 결합해 datetime 으로 변환한다.

    추가 컬럼
    ---------
    forecast_base_time   : 예보 발표 시각 (어제 23:00)  datetime
    forecast_target_time : 예보 대상 시각 (오늘~모레)   datetime
    """
    if df.empty:
        return df

    df      = df.copy()
    year    = datetime.now().year
    base_dt = datetime.strptime(base_date + base_time, "%Y%m%d%H%M")

    def _to_target_dt(row: pd.Series) -> datetime:
        m, d = row["날짜"].split("/")
        return datetime(year, int(m), int(d), int(row["시간"]))

    df["forecast_base_time"]   = base_dt
    df["forecast_target_time"] = df.apply(_to_target_dt, axis=1)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# 2단계 · 날짜 범위 통합 CSV 저장
# ══════════════════════════════════════════════════════════════════════════════

def _build_csv_filename(target_dates: list[str]) -> str:
    """
    수집 시작일~마지막 예보일을 YYMMDD 형식으로 조합해 파일명을 만든다.

    예) ['20260330', '20260331', '20260401'] → '260330_260401_short_term_weather_data.csv'
    """
    if not target_dates:
        stamp = datetime.now().strftime('%y%m%d')
        return f"{stamp}_short_term_weather_data.csv"

    first = datetime.strptime(target_dates[0],  '%Y%m%d').strftime('%y%m%d')
    last  = datetime.strptime(target_dates[-1], '%Y%m%d').strftime('%y%m%d')
    return f"{first}_{last}_short_term_weather_data.csv"


def save_to_dated_csv(
    df: pd.DataFrame,
    target_dates: list[str],
    data_dir: str = DEFAULT_DATA_DIR,
) -> Path:
    """
    전 지역 데이터를 하나의 날짜 범위 CSV 파일로 저장한다.
    동일 파일이 이미 존재하면 덮어쓴다(재실행 멱등성 보장).

    컬럼 순서
    ---------
    지역 → 날짜 → 시간 → 기온 → 풍속 → 습도 → 강수량
    → 체감온도 → 온도지수 → forecast_base_time → forecast_target_time → collected_at
    """
    if df.empty:
        return Path(data_dir)

    dir_path = Path(data_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    file_path              = dir_path / _build_csv_filename(target_dates)
    out_df                 = df.copy()
    out_df["collected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ordered = [
        "지역", "날짜", "시간",
        "기온", "풍속", "습도", "강수량",
        "체감온도", "온도지수",
        "forecast_base_time", "forecast_target_time",
        "collected_at",
    ]
    ordered   = [c for c in ordered if c in out_df.columns]
    remaining = [c for c in out_df.columns if c not in ordered]
    out_df    = out_df[ordered + remaining]

    out_df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"  ✅ CSV 저장 완료 → {file_path}  ({len(out_df):,}행)")
    return file_path


# ══════════════════════════════════════════════════════════════════════════════
# 3단계 · MySQL 저장
# ══════════════════════════════════════════════════════════════════════════════

def _load_mysql_cfg() -> dict:
    """
    접속 정보 우선순위
    ------------------
    1순위 — Streamlit 환경  st.secrets["mysql"]
    2순위 — 로컬 실행       프로젝트루트/.streamlit/secrets.toml

    secrets.toml 예시
    -----------------
    [mysql]
    host     = "127.0.0.1"
    port     = 3306
    user     = "root"
    password = "yourpassword"
    database = "weather_db"
    charset  = "utf8mb4"   # 생략 가능
    """
    try:
        import streamlit as st
        return dict(st.secrets["mysql"])
    except Exception:
        import tomllib
        with open(_SECRETS_PATH, "rb") as f:
            return tomllib.load(f)["mysql"]


def _ensure_db_and_tables(cfg: dict) -> None:
    """
    DB와 테이블이 없으면 자동으로 생성한다.

    순서
    ----
    1. database 지정 없이 MySQL 서버에 접속
    2. CREATE DATABASE IF NOT EXISTS
    3. 해당 DB에 재접속 후 forecast_data 테이블 생성
    """
    charset = cfg.get("charset", "utf8mb4")
    db_name = cfg["database"]

    # ── 1. DB 없이 서버 접속 ─────────────────────────────────────────────
    root_url = (
        f"mysql+pymysql://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}"
        f"?charset={charset}"
    )
    root_engine = create_engine(root_url, pool_pre_ping=True)
    with root_engine.connect() as conn:
        conn.execute(text(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        ))
        conn.commit()
    root_engine.dispose()
    print(f"  ✅ DB 확인/생성 완료: {db_name}")

    # ── 2. 해당 DB에 접속 후 테이블 생성 ─────────────────────────────────
    db_url = (
        f"mysql+pymysql://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{db_name}"
        f"?charset={charset}"
    )
    db_engine = create_engine(db_url, pool_pre_ping=True)
    with db_engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS forecast_data (
                id                   BIGINT AUTO_INCREMENT PRIMARY KEY,
                region               VARCHAR(50) NOT NULL,
                forecast_base_time   DATETIME    NOT NULL,
                forecast_target_time DATETIME    NOT NULL,
                tmp                  DECIMAL(5,1),
                wsd                  DECIMAL(5,1),
                reh                  DECIMAL(5,1),
                pcp                  DECIMAL(6,1),
                apparent_temp        DECIMAL(5,1),
                heat_index           DECIMAL(5,1),
                UNIQUE KEY uq_region_base_target
                    (region, forecast_base_time, forecast_target_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        conn.commit()
    db_engine.dispose()
    print(f"  ✅ 테이블 확인/생성 완료 (forecast_data)")


def _get_mysql_engine():
    """DB/테이블이 없으면 자동 생성한 뒤 엔진을 반환한다."""
    cfg = _load_mysql_cfg()
    _ensure_db_and_tables(cfg)
    url = (
        f"mysql+pymysql://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
        f"?charset={cfg.get('charset', 'utf8mb4')}"
    )
    return create_engine(url, pool_pre_ping=True)


def save_to_db(df: pd.DataFrame) -> None:
    """
    forecast_data 테이블에 저장한다.
    (region, forecast_base_time, forecast_target_time) 복합 키 중복 시 INSERT 스킵.
    """
    if df.empty:
        return

    engine   = _get_mysql_engine()
    inserted = 0

    with engine.connect() as conn:
        for _, row in df.iterrows():
            result = conn.execute(text("""
                INSERT INTO forecast_data
                    (region, forecast_base_time, forecast_target_time,
                     tmp, wsd, reh, pcp, apparent_temp, heat_index)
                SELECT :region, :base_time, :target_time,
                       :tmp, :wsd, :reh, :pcp, :apparent, :heat
                FROM DUAL
                WHERE NOT EXISTS (
                    SELECT 1 FROM forecast_data
                    WHERE region               = :region
                      AND forecast_base_time   = :base_time
                      AND forecast_target_time = :target_time
                )
            """), {
                "region":      row["지역"],
                "base_time":   row["forecast_base_time"],
                "target_time": row["forecast_target_time"],
                "tmp":         row.get("기온"),
                "wsd":         row.get("풍속"),
                "reh":         row.get("습도"),
                "pcp":         row.get("강수량"),
                "apparent":    row.get("체감온도"),
                "heat":        row.get("온도지수"),
            })
            inserted += result.rowcount

        conn.commit()

    print(f"  ✅ DB 저장 완료: {inserted}행 insert")


# ══════════════════════════════════════════════════════════════════════════════
# 메인 진입점 — best_train_time.py 에서 호출
# ══════════════════════════════════════════════════════════════════════════════

def run_collection_pipeline(
    weather_df: pd.DataFrame,
    base_date: str,
    base_time: str,
    target_dates: list[str],
    data_dir: str = DEFAULT_DATA_DIR,
    skip_db: bool = False,
) -> dict:
    """
    best_train_time.py 에서 get_weather_data() 결과를 받아 저장까지 수행한다.
    API를 다시 호출하지 않고 이미 수집된 DataFrame을 재사용한다.

    Parameters
    ----------
    weather_df   : get_weather_data() 가 반환한 DataFrame
    base_date    : df.attrs['base_date']  예) '20260330'
    base_time    : df.attrs['base_time']  예) '2300'
    target_dates : 예보 대상 날짜 리스트  예) ['20260330','20260331','20260401']
    data_dir     : CSV 저장 디렉터리 (기본 'data/forecast')
    skip_db      : True 이면 MySQL 저장 스킵

    Returns
    -------
    { 'df': 전처리 완료 DataFrame, 'csv_path': 저장된 CSV 경로 }
    """
    df       = preprocess_forecast_df(weather_df, base_date, base_time)
    csv_path = save_to_dated_csv(df, target_dates, data_dir)
    if not skip_db:
        save_to_db(df)
    return {"df": df, "csv_path": csv_path}


# ══════════════════════════════════════════════════════════════════════════════
# CLI 단독 실행 (선택) — python -m utils.best_train_forecast_pipeline
# ══════════════════════════════════════════════════════════════════════════════

def _cli_get_forecast_data() -> tuple[pd.DataFrame, str, str, list[str]]:
    """CLI 단독 실행 시에만 사용. _fetch_area() 로 직접 수집."""
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST)
    # now          = datetime.now()
    base_date    = (now - timedelta(days=1)).strftime('%Y%m%d')
    base_time    = "2300"
    target_dates = [(now + timedelta(days=i)).strftime('%Y%m%d') for i in range(3)]

    all_rows: list[dict] = []
    for name, info in AREA_INFO.items():
        rows, err = _fetch_area(name, info, base_date, base_time, target_dates)
        if err:
            print(f"  ⚠️  {err}", file=sys.stderr)
        all_rows.extend(rows)

    if not all_rows:
        return pd.DataFrame(), base_date, base_time, target_dates

    df = pd.DataFrame(all_rows)
    df = compute_apparent_temperatures(df)
    return df, base_date, base_time, target_dates


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="단기예보 수집 파이프라인")
    parser.add_argument("--csv-only", action="store_true",
                        help="CSV 저장만 수행하고 MySQL DB 저장을 건너뜁니다.")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR,
                        help=f"CSV 저장 디렉터리 (기본값: {DEFAULT_DATA_DIR})")
    args = parser.parse_args()

    print("=" * 60)
    print(f"[1/3] API 수집  {datetime.now():%Y-%m-%d %H:%M:%S}")
    df, base_date, base_time, target_dates = _cli_get_forecast_data()

    if df.empty:
        print("  ❌ 수집된 데이터가 없습니다.")
        sys.exit(1)
    print(f"  ✅ {len(df):,}행  지역={list(df['지역'].unique())}")

    result = run_collection_pipeline(
        weather_df   = df,
        base_date    = base_date,
        base_time    = base_time,
        target_dates = target_dates,
        data_dir     = args.data_dir,
        skip_db      = args.csv_only,
    )
    print("=" * 60)
    print(f"완료  {datetime.now():%Y-%m-%d %H:%M:%S}")
