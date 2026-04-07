"""
W-BOSS 시각화 컴포넌트
────────────────────────
- Folium 기상현황 지도 만들기
- Altair 기상요소 추이 차트 만들기
"""
import folium
import altair as alt
import pandas as pd
from utils.realtime.utils import MAP_COLOR, METRIC_UNIT


def _fmt(v: float | None, unit: str) -> str:
    """float 값 포맷팅. None 이면 '-' 반환."""
    return f"{v:.1f}{unit}" if v is not None else "-"


def build_weather_map(map_df: pd.DataFrame, target_col: str) -> folium.Map:
    """훈련 판정 색상 CircleMarker Folium 지도를 반환합니다.

    Parameters
    ----------
    map_df     : 지역·lat·lng·status·value·기온·풍속·강수량·습도 컬럼 포함 DataFrame
    target_col : 현재 판정 기준 지표명 (예: '온도지수' / '체감온도')
    """
    center_lat = map_df["lat"].mean()
    center_lng = map_df["lng"].mean()
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=9,
        tiles="CartoDB positron",
    )
    for _, row in map_df.iterrows():
        color = MAP_COLOR.get(row["status"], "#888888")
        tip = (
            f"{row['지역']}  |  {row['status']}"
            f"  |  {target_col}: {_fmt(row['value'], '')}"
            f"  |  기온: {_fmt(row['기온'], '℃')}"
            f"  풍속: {_fmt(row['풍속'], 'm/s')}"
            f"  강수량: {_fmt(row['강수량'], 'mm')}"
            f"  습도: {_fmt(row['습도'], '%')}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=18,
            fill=True,
            color=color,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            tooltip=folium.Tooltip(tip, sticky=True),
        ).add_to(m)
    return m


def build_altair_chart(chart_df: pd.DataFrame, chart_metric: str) -> alt.Chart:
    """기상요소 추이 Altair 꺾은선 차트를 반환합니다.

    Parameters
    ----------
    chart_df     : '시간' 컬럼과 chart_metric 컬럼을 포함한 DataFrame
    chart_metric : 표시할 기상 지표명 (예: '기온', '풍속')
    """
    unit = METRIC_UNIT.get(chart_metric, "")
    return (
        alt.Chart(chart_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("시간:O", sort=None, title="시간"),
            y=alt.Y(f"{chart_metric}:Q", title=f"{chart_metric} ({unit})"),
        )
        .properties(height=280)
    )
