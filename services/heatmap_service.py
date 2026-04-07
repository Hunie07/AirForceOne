
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

from core.config import DATA_DIR

CSV_PATH = DATA_DIR / "heatmap.csv"
ACTUAL_CSV_PATH = DATA_DIR / "heatmap_actual.csv"
ALL_MONTHS = list(range(1, 13))


def _read_csv_with_fallback(path: Path, **kwargs) -> pd.DataFrame:
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


def _score_from_wct(wct: float) -> float:
    if pd.isna(wct):
        return np.nan
    if wct <= -25:
        return 0.10
    if wct <= -15:
        return 0.25
    if wct <= -5:
        return 0.50
    if wct <= 25:
        return 0.95
    if wct <= 30:
        return 0.60
    return 0.20


def _find_actual_csv() -> Path | None:
    if ACTUAL_CSV_PATH.exists():
        return ACTUAL_CSV_PATH
    if CSV_PATH.exists():
        return CSV_PATH
    for p in DATA_DIR.rglob("*.csv"):
        lower = str(p).lower()
        if "forecast" in lower or "special_report" in lower:
            continue
        try:
            head = _read_csv_with_fallback(p, nrows=3)
        except Exception:
            continue
        cols = {str(c).strip().lower() for c in head.columns}
        if {"year", "month", "day", "hour", "sploc", "wct"}.issubset(cols) or {"year", "month", "hour", "sploc", "wct"}.issubset(cols):
            return p
    return None


@st.cache_data(show_spinner=False)
def _load_actual_raw_cached() -> pd.DataFrame:
    path = _find_actual_csv()
    if path is None:
        raise FileNotFoundError("heatmap actual csv not found")
    df = _read_csv_with_fallback(path)

    df.columns = [str(c).strip().lower() for c in df.columns]
    if "wct" not in df.columns and "WCT" in df.columns:
        df["wct"] = df["WCT"]

    if "day" not in df.columns:
        if "tm" in df.columns:
            try:
                dt = pd.to_datetime(df["tm"])
                df["day"] = dt.dt.day
            except Exception:
                df["day"] = 1
        else:
            df["day"] = 1

    numeric_cols = ["year", "month", "day", "hour", "ta", "ws", "wd", "rn", "dsnw", "hm", "wct"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "tm" in df.columns:
        try:
            df["tm"] = pd.to_datetime(df["tm"])
        except Exception:
            pass

    df["score"] = df["wct"].map(_score_from_wct) if "wct" in df.columns else np.nan
    return df.dropna(subset=["year", "month", "day", "hour", "sploc"]).copy()


def get_raw_data() -> pd.DataFrame:
    return _load_actual_raw_cached()


def get_station_options() -> list[str]:
    raw = get_raw_data()
    return sorted(raw["sploc"].dropna().astype(str).unique().tolist())


def get_hour_options() -> list[int]:
    raw = get_raw_data()
    return sorted(raw["hour"].dropna().astype(int).unique().tolist())


def get_year_options(sploc: str, hour: int) -> list[int]:
    raw = get_raw_data()
    mask = (raw["sploc"].astype(str) == str(sploc)) & (raw["hour"].astype(int) == int(hour))
    return sorted(raw.loc[mask, "year"].dropna().astype(int).unique().tolist())


def get_month_options(sploc: str, hour: int, year: int) -> list[int]:
    raw = get_raw_data()
    mask = (
        (raw["sploc"].astype(str) == str(sploc))
        & (raw["hour"].astype(int) == int(hour))
        & (raw["year"].astype(int) == int(year))
    )
    return sorted(raw.loc[mask, "month"].dropna().astype(int).unique().tolist())


def get_day_options(sploc: str, hour: int, year: int, month: int) -> list[int]:
    raw = get_raw_data()
    mask = (
        (raw["sploc"].astype(str) == str(sploc))
        & (raw["hour"].astype(int) == int(hour))
        & (raw["year"].astype(int) == int(year))
        & (raw["month"].astype(int) == int(month))
    )
    return sorted(raw.loc[mask, "day"].dropna().astype(int).unique().tolist())


def load_data(sploc: str | None = None, hour: int | None = None) -> pd.DataFrame:
    raw = get_raw_data()
    if sploc:
        raw = raw[raw["sploc"].astype(str) == str(sploc)].copy()
    if hour is not None:
        raw = raw[raw["hour"].astype(int) == int(hour)].copy()
    metric_col = "wct" if "wct" in raw.columns else "ta"
    monthly = (
        raw.groupby(["year", "month"], as_index=False)
           .agg(score=("score", "mean"), avg_wct=(metric_col, "mean"), samples=(metric_col, "size"))
           .sort_values(["year", "month"])
    )
    return monthly


def get_daily_detail(sploc: str, year: int, month: int, day: int) -> pd.DataFrame:
    raw = get_raw_data()
    mask = (
        (raw["sploc"].astype(str) == str(sploc))
        & (raw["year"].astype(int) == int(year))
        & (raw["month"].astype(int) == int(month))
        & (raw["day"].astype(int) == int(day))
    )
    cols = [c for c in ["hour", "wct", "ta", "ws", "hm", "rn", "dsnw", "score"] if c in raw.columns]
    return raw.loc[mask, cols].sort_values("hour").copy()


def get_all_yearly_pivots(df: pd.DataFrame | None = None):
    df = load_data() if df is None else df
    if df.empty:
        return pd.DataFrame()
    return df.pivot(index="month", columns="year", values="score").fillna(0)


def calculate_yearly_statistics(df: pd.DataFrame | None = None):
    df = load_data() if df is None else df
    if df.empty:
        return pd.DataFrame(columns=["year", "mean_score", "min_score", "max_score", "samples"])
    stats = (
        df.groupby("year", as_index=False)
          .agg(mean_score=("score", "mean"), min_score=("score", "min"), max_score=("score", "max"), samples=("samples", "sum"))
          .sort_values("year")
    )
    for c in ["mean_score", "min_score", "max_score"]:
        stats[c] = stats[c].round(3)
    return stats


def _daily_agg_func(formula: str):
    if formula == "최대":
        return "max"
    if formula == "최소":
        return "min"
    return "mean"


def _metric_col(metric_label: str) -> str:
    return "ta" if metric_label == "기온" else "wct"


def build_annual_heatmap(sploc: str, year: int, hour: int, metric_label: str = "체감온도", formula: str = "평균") -> pd.DataFrame:
    raw = get_raw_data().copy()
    metric = _metric_col(metric_label)
    agg = _daily_agg_func(formula)

    mask = (
        (raw["sploc"].astype(str) == str(sploc))
        & (raw["year"].astype(int) == int(year))
        & (raw["hour"].astype(int) == int(hour))
    )
    daily = raw.loc[mask, ["month", "day", metric]].copy()
    daily = daily.groupby(["month", "day"], as_index=False).agg(value=(metric, agg)).sort_values(["month", "day"])

    mat = pd.DataFrame(index=list(range(1, 13)), columns=list(range(1, 32)), dtype=float)
    for _, row in daily.iterrows():
        mat.loc[int(row["month"]), int(row["day"])] = float(row["value"])
    return mat


def _categorize_value(value: float, metric_label: str) -> str:
    if pd.isna(value):
        return "결측"
    if metric_label == "기온":
        if value < -15 or value >= 35:
            return "전면 중지"
        if value < -5 or value >= 31:
            return "부분제한"
        if value < 0 or value >= 28:
            return "주의"
        return "정상"
    if value <= -25 or value > 32:
        return "전면 중지"
    if value <= -15 or value > 30:
        return "부분제한"
    if value <= -5 or value > 25:
        return "주의"
    return "정상"


def summarize_annual_heatmap(mat: pd.DataFrame, metric_label: str = "체감온도") -> dict:
    values = []
    monthly = []
    for month in mat.index:
        row = mat.loc[month]
        valid = row.dropna()
        labels = valid.apply(lambda v: _categorize_value(v, metric_label))
        normal_count = int((labels == "정상").sum())
        total_count = int(valid.shape[0])
        percent = round((normal_count / total_count) * 100) if total_count else 0
        monthly.append({"month": int(month), "normal_days": normal_count, "total_days": total_count, "percent": percent})
        values.extend(valid.tolist())

    series = pd.Series(values)
    labels = series.apply(lambda v: _categorize_value(v, metric_label)) if not series.empty else pd.Series(dtype=object)
    return {
        "정상": int((labels == "정상").sum()),
        "주의": int((labels == "주의").sum()),
        "부분제한": int((labels == "부분제한").sum()),
        "전면 중지": int((labels == "전면 중지").sum()),
        "monthly": monthly,
        "total_days": int(series.shape[0]),
    }


def get_daily_compare_detail(sploc: str, year: int, month: int, day: int, metric_label: str = "체감온도") -> pd.DataFrame:
    raw = get_raw_data().copy()
    metric = _metric_col(metric_label)

    actual_mask = (
        (raw["sploc"].astype(str) == str(sploc))
        & (raw["year"].astype(int) == int(year))
        & (raw["month"].astype(int) == int(month))
        & (raw["day"].astype(int) == int(day))
    )
    actual = raw.loc[actual_mask, ["hour", metric, "ta", "ws", "hm", "rn", "dsnw"]].copy()
    actual = actual.rename(columns={metric: "actual"}).sort_values("hour")

    baseline_mask = (
        (raw["sploc"].astype(str) == str(sploc))
        & (raw["month"].astype(int) == int(month))
        & (raw["day"].astype(int) == int(day))
    )
    baseline = raw.loc[baseline_mask, ["hour", metric]].copy()
    if baseline.empty:
        baseline_mask = (
            (raw["sploc"].astype(str) == str(sploc))
            & (raw["month"].astype(int) == int(month))
        )
        baseline = raw.loc[baseline_mask, ["hour", metric]].copy()
    baseline = baseline.groupby("hour", as_index=False).agg(baseline=(metric, "mean"))

    return actual.merge(baseline, on="hour", how="left")
