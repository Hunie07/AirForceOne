from __future__ import annotations

import html
import streamlit as st
import streamlit.components.v1 as components

from services import get_module3_region_options, compute_module3_snapshot


def _panel_palette() -> dict:
    mode = st.session_state.get("theme_mode", "시스템")
    if mode == "라이트 모드":
        return {
            "panel_bg": "#ffffff",
            "panel_bg_soft": "#f8fbff",
            "border": "#dbe4f0",
            "text": "#132238",
            "muted": "#66758b",
            "accent": "#2f6fed",
            "active_border": "#38bdf8",
        }
    return {
        "panel_bg": "#12203a",
        "panel_bg_soft": "#0f1a2e",
        "border": "#223454",
        "text": "#e5edf7",
        "muted": "#98a8bc",
        "accent": "#59a8ff",
        "active_border": "#22d3ee",
    }


def _month_strip_html(monthly_baseline, current_month: int, mode: str) -> str:
    p = _panel_palette()

    if monthly_baseline is None or monthly_baseline.empty:
        return f"""
        <html><body style='margin:0;background:transparent;'>
        <div style='padding:1rem;border:1px solid {p["border"]};border-radius:18px;color:{p["muted"]};background:{p["panel_bg"]};font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;'>
            기준선 데이터가 없습니다.
        </div>
        </body></html>
        """

    values = monthly_baseline["value"].tolist()
    months = monthly_baseline["month"].tolist()
    vmin = min(values)
    vmax = max(values)
    denom = (vmax - vmin) if (vmax - vmin) else 1

    bars = []
    for month, value in zip(months, values):
        bar_h = 18 + ((value - vmin) / denom) * 48
        color = "#22c55e"
        if value >= 28:
            color = "#ef4444"
        elif value >= 20:
            color = "#f59e0b"
        elif value <= 0:
            color = "#3b82f6"

        border = (
            f'2px solid {p["active_border"]}'
            if int(month) == int(current_month)
            else f'1px solid {p["border"]}'
        )

        bars.append(
            """
            <div style='display:flex;flex-direction:column;align-items:center;gap:.35rem;min-width:52px;'>
                <div style='width:100%;height:{height}px;border-radius:10px 10px 4px 4px;background:{color};border:{border};opacity:.95;'></div>
                <div style='font-size:.82rem;color:{text};font-weight:700;'>{month}월</div>
            </div>
            """.format(
                height=round(bar_h, 1),
                color=color,
                border=border,
                text=p["text"],
                month=int(month),
            )
        )

    return """
    <html>
    <body style='margin:0;background:transparent;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;'>
      <div style='background:{panel_bg};border:1px solid {border};border-radius:18px;padding:1rem;'>
        <div style='font-size:.9rem;font-weight:800;color:{text};margin-bottom:.8rem;'>월별 평년 {mode} 기준선</div>
        <div style='display:flex;align-items:flex-end;gap:.45rem;overflow-x:auto;padding-bottom:.2rem;'>
          {bars}
        </div>
      </div>
    </body>
    </html>
    """.format(
        panel_bg=p["panel_bg"],
        border=p["border"],
        text=p["text"],
        mode=html.escape(mode),
        bars="".join(bars),
    )


def render_module3_anomaly_panel():
    options = get_module3_region_options()
    ctrl1, ctrl2 = st.columns([1.15, 0.85], gap="large")
    with ctrl1:
        region_name = st.selectbox("분석 지역", options, index=0, key="module3_region_select")
    with ctrl2:
        mode = st.radio("분석 모드", ["체감온도", "기온"], horizontal=True, key="module3_mode_radio")

    snap = compute_module3_snapshot(region_name, mode)
    current_month = snap["latest_date"].month if snap["latest_date"] else 1

    top_left, top_right = st.columns(2, gap="large")
    with top_left:
        st.markdown(
            '''
            <div class="wb-panel">
                <div class="page-eyebrow">MODULE-03</div>
                <div class="section-title" style="margin-bottom:.55rem;">오늘 평균 {mode}</div>
                <div style="font-size:2.35rem;font-weight:800;color:var(--wb-text);line-height:1.05;">{today}</div>
                <div style="margin-top:.55rem;color:var(--wb-muted);font-size:.92rem;">판정: {status}</div>
                <div style="margin-top:.25rem;color:var(--wb-muted);font-size:.82rem;">분석 지역: {region}</div>
            </div>
            '''.format(
                mode=html.escape(mode),
                today="-- °C" if snap["today_avg"] is None else f"{snap['today_avg']:+.1f}°C",
                status=html.escape(snap["status"]),
                region=html.escape(region_name),
            ),
            unsafe_allow_html=True,
        )
    with top_right:
        mean_label = "-- °C" if snap["climate_mean"] is None else f"{snap['climate_mean']:+.1f}°C"
        plus1 = "--" if snap["climate_mean"] is None else f"{snap['climate_mean'] + snap['std']:.1f}°C"
        minus1 = "--" if snap["climate_mean"] is None else f"{snap['climate_mean'] - snap['std']:.1f}°C"
        plus2 = "--" if snap["climate_mean"] is None else f"{snap['climate_mean'] + 2*snap['std']:.1f}°C"
        minus2 = "--" if snap["climate_mean"] is None else f"{snap['climate_mean'] - 2*snap['std']:.1f}°C"
        st.markdown(
            '''
            <div class="wb-panel">
                <div class="page-eyebrow">MODULE-03</div>
                <div class="section-title" style="margin-bottom:.55rem;">평년 기준 ({month}월) · {mode}</div>
                <div style="font-size:2.35rem;font-weight:800;color:var(--wb-text);line-height:1.05;">{mean}</div>
                <div style="margin-top:.7rem;color:var(--wb-muted);font-size:.86rem;">±1σ · {plus1} ~ {minus1}</div>
                <div style="margin-top:.18rem;color:var(--wb-muted);font-size:.86rem;">±2σ · {plus2} ~ {minus2}</div>
            </div>
            '''.format(
                month=current_month,
                mode=html.escape(mode),
                mean=mean_label,
                plus1=plus1,
                minus1=minus1,
                plus2=plus2,
                minus2=minus2,
            ),
            unsafe_allow_html=True,
        )

    st.caption("월별 평년 기준선")
    components.html(_month_strip_html(snap["monthly_baseline"], current_month, mode), height=180, scrolling=False)
