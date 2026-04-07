
from __future__ import annotations

import html
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def _palette() -> dict:
    if st.session_state.get("theme_mode") == "라이트 모드":
        return {
            "panel_bg": "#ffffff",
            "panel_bg_soft": "#f8fbff",
            "border": "#dbe4f0",
            "text": "#132238",
            "muted": "#66758b",
            "cyan": "#06b6d4",
            "amber": "#f59e0b",
            "red": "#ef4444",
            "shadow": "0 10px 28px rgba(15,23,42,.06)",
        }
    return {
        "panel_bg": "#121a2b",
        "panel_bg_soft": "#0f1728",
        "border": "#263247",
        "text": "#e5edf7",
        "muted": "#98a8bc",
        "cyan": "#22d3ee",
        "amber": "#f59e0b",
        "red": "#f43f5e",
        "shadow": "0 14px 34px rgba(0,0,0,.22)",
    }


def _safe(v) -> str:
    return html.escape("" if v is None else str(v))


def _badge(label: str, p: dict) -> str:
    color = p["amber"]
    if "경보" in label:
        color = p["red"]
    elif "해제" in label:
        color = p["muted"]
    return (
        '<span style="display:inline-flex;align-items:center;padding:.28rem .58rem;'
        f'border-radius:999px;border:1px solid {color};color:{color};font-size:.78rem;'
        'font-weight:700;background:rgba(255,255,255,.02);">' + _safe(label) + '</span>'
    )


def render_module3_panel(active_df: pd.DataFrame, summary: dict):
    p = _palette()
    rows_html = []

    if active_df is not None and not active_df.empty:
        view = active_df.copy()
        if "발표시각" not in view.columns and "PRSNTN_TM" in view.columns:
            view["발표시각"] = view["PRSNTN_TM"].astype(str)
        for _, row in view.head(5).iterrows():
            title = _safe(row.get("TTL", "-"))
            zone = _safe(row.get("RLVT_ZONE") or row.get("SPNE_FRMNT_PRCON_CN") or "-")
            time = _safe(row.get("발표시각", "-"))
            badge = _badge(str(row.get("TTL", "")), p)
            rows_html.append(
                '''
                <div class="m3-item">
                    <div class="m3-main">
                        <div class="m3-title">{title}</div>
                        <div class="m3-zone">{zone}</div>
                        <div class="m3-time">발표시각 · {time}</div>
                    </div>
                    <div class="m3-badge">{badge}</div>
                </div>
                '''.format(title=title, zone=zone, time=time, badge=badge)
            )
    else:
        rows_html.append(
            '<div class="m3-empty">현재 발효 중인 특보가 없습니다.</div>'
        )

    total_active = int(summary.get("warning", 0)) + int(summary.get("advisory", 0))

    html_doc = '''
    <html>
    <head>
    <style>
      body {{
        margin:0;
        background:{panel_bg};
        color:{text};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }}
      .m3-wrap {{
        background:{panel_bg};
        border:1px solid {border};
        border-radius:20px;
        box-shadow:{shadow};
        padding:1rem;
      }}
      .m3-head {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        margin-bottom:.85rem;
      }}
      .m3-mini {{
        font-size:.82rem;
        font-weight:800;
        color:{cyan};
        letter-spacing:.06em;
      }}
      .m3-title-head {{
        font-size:1.08rem;
        font-weight:800;
        color:{text};
        margin-top:.15rem;
      }}
      .m3-sub {{
        font-size:.8rem;
        color:{muted};
      }}
      .m3-stats {{
        display:grid;
        grid-template-columns:repeat(3,minmax(0,1fr));
        gap:.7rem;
        margin-bottom:.9rem;
      }}
      .m3-stat {{
        padding:.9rem 1rem;
        border:1px solid {border};
        border-radius:14px;
        background:{panel_bg_soft};
      }}
      .m3-stat-label {{
        font-size:.78rem;
        color:{muted};
      }}
      .m3-stat-value {{
        font-size:1.9rem;
        font-weight:800;
        margin-top:.15rem;
      }}
      .m3-list {{
        display:flex;
        flex-direction:column;
        gap:.65rem;
      }}
      .m3-item {{
        display:flex;
        justify-content:space-between;
        gap:1rem;
        padding:.9rem 1rem;
        border:1px solid {border};
        border-radius:14px;
        background:{panel_bg_soft};
      }}
      .m3-main {{
        min-width:0;
      }}
      .m3-title {{
        font-size:1rem;
        font-weight:800;
        color:{text};
      }}
      .m3-zone {{
        font-size:.88rem;
        color:{muted};
        margin-top:.18rem;
      }}
      .m3-time {{
        font-size:.8rem;
        color:{muted};
        margin-top:.25rem;
      }}
      .m3-empty {{
        padding:1.2rem;
        border:1px dashed {border};
        border-radius:14px;
        color:{muted};
        text-align:center;
      }}
    </style>
    </head>
    <body>
      <div class="m3-wrap">
        <div class="m3-head">
          <div>
            <div class="m3-mini">MODULE-03</div>
            <div class="m3-title-head">실시간 특보 요약</div>
          </div>
          <div class="m3-sub">실시간 현황 핵심만 표시</div>
        </div>
        <div class="m3-stats">
          <div class="m3-stat">
            <div class="m3-stat-label">발효 중</div>
            <div class="m3-stat-value" style="color:{text};">{total_active}</div>
          </div>
          <div class="m3-stat">
            <div class="m3-stat-label">경보</div>
            <div class="m3-stat-value" style="color:{red};">{warning}</div>
          </div>
          <div class="m3-stat">
            <div class="m3-stat-label">주의보</div>
            <div class="m3-stat-value" style="color:{amber};">{advisory}</div>
          </div>
        </div>
        <div class="m3-list">
          {rows}
        </div>
      </div>
    </body>
    </html>
    '''.format(
        panel_bg=p["panel_bg"],
        panel_bg_soft=p["panel_bg_soft"],
        border=p["border"],
        text=p["text"],
        muted=p["muted"],
        cyan=p["cyan"],
        shadow=p["shadow"],
        total_active=total_active,
        warning=int(summary.get("warning", 0)),
        advisory=int(summary.get("advisory", 0)),
        red=p["red"],
        amber=p["amber"],
        rows="".join(rows_html),
    )

    height = 250 + len(rows_html) * 92
    components.html(html_doc, height=height, scrolling=False)
