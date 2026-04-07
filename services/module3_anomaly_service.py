
from __future__ import annotations

from datetime import datetime
import math
import pandas as pd

from services.heatmap_service import get_raw_data


def get_module3_region_options() -> list[str]:
    raw = get_raw_data()
    opts = sorted(raw["sploc"].dropna().astype(str).unique().tolist())
    return ["전체 평균"] + opts


def _select_region(df: pd.DataFrame, region_name: str) -> pd.DataFrame:
    if not region_name or region_name == "전체 평균":
        return df.copy()
    return df[df["sploc"].astype(str) == str(region_name)].copy()


def compute_module3_snapshot(region_name: str = "전체 평균", mode: str = "체감온도") -> dict:
    raw = get_raw_data().copy()
    raw = _select_region(raw, region_name)

    metric = "wct" if mode == "체감온도" else "ta"
    if raw.empty or metric not in raw.columns:
        return {
            "latest_date": None,
            "today_avg": None,
            "climate_mean": None,
            "sigma": 0.0,
            "std": 0.0,
            "monthly_baseline": pd.DataFrame(columns=["month", "value"]),
            "status": "데이터 없음",
            "mode": mode,
            "region_name": region_name,
        }

    latest = raw[["year", "month", "day"]].drop_duplicates().sort_values(["year", "month", "day"]).iloc[-1]
    y, m, d = int(latest["year"]), int(latest["month"]), int(latest["day"])

    today_df = raw[(raw["year"].astype(int) == y) & (raw["month"].astype(int) == m) & (raw["day"].astype(int) == d)].copy()
    today_avg = float(today_df[metric].mean()) if not today_df.empty else None

    hist_month = raw[raw["month"].astype(int) == m].copy()
    climate_mean = float(hist_month[metric].mean()) if not hist_month.empty else None
    std = float(hist_month[metric].std(ddof=0)) if len(hist_month) > 1 else 0.0
    if std and today_avg is not None and not math.isnan(std):
        sigma = (today_avg - climate_mean) / std
    else:
        sigma = 0.0

    if sigma >= 2:
        status = "매우 높음"
    elif sigma >= 1:
        status = "높음"
    elif sigma <= -2:
        status = "매우 낮음"
    elif sigma <= -1:
        status = "낮음"
    else:
        status = "정상 범위"

    baseline = (
        raw.groupby("month", as_index=False)[metric]
           .mean()
           .rename(columns={metric: "value"})
           .sort_values("month")
    )

    return {
        "latest_date": datetime(y, m, d),
        "today_avg": round(today_avg, 1) if today_avg is not None else None,
        "climate_mean": round(climate_mean, 1) if climate_mean is not None else None,
        "sigma": round(float(sigma), 2),
        "std": round(float(std), 2),
        "monthly_baseline": baseline,
        "status": status,
        "mode": mode,
        "region_name": region_name,
    }
