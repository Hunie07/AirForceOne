
from __future__ import annotations

import html
import streamlit as st


def render_summary_cards(items: list[tuple[str, str | int]]):
    if not items:
        return

    cols = st.columns(len(items), gap="large")
    for col, (label, value) in zip(cols, items):
        with col:
            st.markdown(
                '''
                <div class="wb-stat-card">
                    <div class="wb-stat-label">{label}</div>
                    <div class="wb-stat-value">{value}</div>
                </div>
                '''.format(
                    label=html.escape(str(label)),
                    value=html.escape(str(value)),
                ),
                unsafe_allow_html=True,
            )
