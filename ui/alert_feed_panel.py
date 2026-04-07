from __future__ import annotations

import html
import pandas as pd
import streamlit as st


def render_alert_feed_panel(active_df: pd.DataFrame):
    st.markdown('<div class="section-title" style="margin-top:1rem;">실시간 특보 요약</div>', unsafe_allow_html=True)

    if active_df is None or active_df.empty:
        st.info("현재 발효 중인 특보가 없습니다.")
        return

    for _, row in active_df.head(4).iterrows():
        level = str(row.get("TTL", ""))
        zone = str(row.get("RLVT_ZONE") or row.get("SPNE_FRMNT_PRCON_CN") or "-")
        tm = str(row.get("발표시각") or row.get("PRSNTN_TM") or "-")
        tone = "var(--wb-primary)"
        if "경보" in level:
            tone = "#ef4444"
        elif "주의" in level:
            tone = "#f59e0b"

        st.markdown(
            '''
            <div class="wb-panel" style="padding:.85rem 1rem;margin-bottom:.65rem;">
                <div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;">
                    <div style="min-width:0;">
                        <div style="font-size:1rem;font-weight:800;color:{tone};">{level}</div>
                        <div style="font-size:.9rem;color:var(--wb-text);margin-top:.18rem;">{zone}</div>
                        <div style="font-size:.8rem;color:var(--wb-muted);margin-top:.22rem;">발표시각 · {tm}</div>
                    </div>
                    <div style="font-size:.76rem;color:{tone};font-weight:800;border:1px solid {tone};border-radius:999px;padding:.28rem .55rem;">
                        ALERT
                    </div>
                </div>
            </div>
            '''.format(
                tone=tone,
                level=html.escape(level),
                zone=html.escape(zone),
                tm=html.escape(tm),
            ),
            unsafe_allow_html=True,
        )
