from __future__ import annotations

import streamlit as st

_LIGHT = {
    "bg": "#f4f7fb",
    "surface": "#ffffff",
    "surface_2": "#f7faff",
    "border": "#d9e4f0",
    "text": "#132238",
    "muted": "#66758b",
    "primary": "#2f6fed",
    "primary_soft": "#e8f0ff",
    "success_soft": "#e8f7ee",
    "danger_soft": "#fee9e7",
    "card_grad": "linear-gradient(180deg, #ffffff 0%, #f8fbff 100%)",
    "hero_grad": "linear-gradient(135deg, #ffffff 0%, #edf4ff 100%)",
    "shadow": "0 12px 28px rgba(15, 23, 42, 0.06)",
}


def _theme_vars(colors: dict[str, str]) -> str:
    return "\n".join(
        [
            f"--wb-bg: {colors['bg']};",
            f"--wb-surface: {colors['surface']};",
            f"--wb-surface-2: {colors['surface_2']};",
            f"--wb-border: {colors['border']};",
            f"--wb-text: {colors['text']};",
            f"--wb-muted: {colors['muted']};",
            f"--wb-primary: {colors['primary']};",
            f"--wb-primary-soft: {colors['primary_soft']};",
            f"--wb-success-soft: {colors['success_soft']};",
            f"--wb-danger-soft: {colors['danger_soft']};",
            f"--wb-card-grad: {colors['card_grad']};",
            f"--wb-hero-grad: {colors['hero_grad']};",
            f"--wb-shadow: {colors['shadow']};",
        ]
    )


BASE_CSS = """
<style>
:root {
    __ROOT_VARS__
    --wb-radius: 18px;
    --wb-radius-sm: 12px;
}

[data-testid="stSidebarNav"] {
    display: none;
}

html, body, [class*="css"], .stApp {
    color: var(--wb-text);
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.stApp {
    background: var(--wb-bg);
}

[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: var(--wb-surface);
    border-right: 1px solid var(--wb-border);
}

section[data-testid="stSidebar"] * {
    color: var(--wb-text) !important;
}

[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button,
[data-testid="collapsedControl"] {
    opacity: 1 !important;
    visibility: visible !important;
}

[data-testid="stSidebarCollapseButton"] button,
[data-testid="collapsedControl"] {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: 40px !important;
    min-height: 40px !important;
    background: #2563eb !important;
    border: 1px solid #2563eb !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 20px rgba(37,99,235,.35) !important;
}

[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="collapsedControl"]:hover {
    background: #1d4ed8 !important;
    border-color: #1d4ed8 !important;
}

[data-testid="stSidebarCollapseButton"] button svg,
[data-testid="stSidebarCollapseButton"] button *,
[data-testid="collapsedControl"] svg,
[data-testid="collapsedControl"] * {
    color: #ffffff !important;
    fill: #ffffff !important;
    stroke: #ffffff !important;
    opacity: 1 !important;
}

[data-testid="collapsedControl"] {
    position: fixed !important;
    top: 4.2rem !important;
    left: .9rem !important;
    z-index: 1000 !important;
}

.block-container {
    max-width: none;
    padding-top: .9rem;
    padding-bottom: 1rem;
    padding-left: .75rem;
    padding-right: .75rem;
}

.wb-brand {
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin-bottom: .2rem;
}

.hero-card {
    background: var(--wb-hero-grad);
    border: 1px solid var(--wb-border);
    border-radius: 24px;
    box-shadow: var(--wb-shadow);
    padding: 1.3rem 1.45rem;
    margin-bottom: 1rem;
}

.wb-panel,
.card-soft,
.wb-module-card {
    background: var(--wb-card-grad);
    border: 1px solid var(--wb-border);
    border-radius: 20px;
    box-shadow: var(--wb-shadow);
    padding: 1rem 1.05rem;
}

.page-eyebrow {
    color: var(--wb-primary);
    font-size: .88rem;
    font-weight: 800;
    letter-spacing: .04em;
    margin-bottom: .32rem;
}

.page-title {
    font-size: 2.12rem;
    line-height: 1.08;
    font-weight: 800;
    margin: 0 0 .35rem 0;
    color: var(--wb-text);
}

.page-subtitle {
    color: var(--wb-muted);
    font-size: 1.03rem;
    margin: 0;
}

.section-title {
    font-size: 1.03rem;
    font-weight: 800;
    margin-bottom: .7rem;
    color: var(--wb-text);
}

p, li, label, .stCaption, .stMarkdown {
    color: var(--wb-text);
    font-size: .98rem;
}

.wb-hero-chip-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: .55rem;
}

.wb-hero-chip {
    padding: .52rem .9rem;
    border-radius: 999px;
    border: 1px solid var(--wb-border);
    background: rgba(255,255,255,.74);
    font-size: .84rem;
    font-weight: 800;
    color: var(--wb-primary);
}

.wb-module-card {
    min-height: 225px;
}

.wb-module-icon {
    width: 54px;
    height: 54px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: .9rem;
    background: linear-gradient(135deg, var(--wb-primary), #38bdf8);
    color: #fff;
    font-size: 1.55rem;
}

.wb-module-list {
    margin: 0 0 1rem 1.1rem;
    padding: 0;
    color: var(--wb-muted);
}

.wb-module-list li {
    margin-bottom: .28rem;
}


.wb-module-card-strong {
    min-height: 250px;
}

.wb-module-head {
    display: flex;
    align-items: flex-start;
    gap: .9rem;
    margin-bottom: .9rem;
}

.wb-brief-card {
    background: var(--wb-card-grad);
    border: 1px solid var(--wb-border);
    border-radius: 18px;
    box-shadow: var(--wb-shadow);
    padding: 1rem;
    min-height: 126px;
}

.wb-brief-label {
    font-size: .82rem;
    color: var(--wb-muted);
    font-weight: 800;
    margin-bottom: .45rem;
}

.wb-brief-value {
    font-size: 1.38rem;
    line-height: 1.1;
    color: var(--wb-text);
    font-weight: 800;
    margin-bottom: .32rem;
}

.wb-brief-desc {
    font-size: .88rem;
    color: var(--wb-muted);
}

section[data-testid="stSidebar"] [data-testid="stPageLinkContainer"] a {
    border: 1px solid var(--wb-border) !important;
    border-radius: 16px !important;
    padding: .85rem .9rem !important;
    margin-bottom: .65rem !important;
    background: var(--wb-surface) !important;
    box-shadow: none !important;
}

section[data-testid="stSidebar"] [data-testid="stPageLinkContainer"] a:hover {
    border-color: var(--wb-primary) !important;
    background: var(--wb-primary-soft) !important;
}


.wb-info-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: .8rem;
}

.wb-info-item {
    background: var(--wb-surface);
    border: 1px solid var(--wb-border);
    border-radius: 14px;
    padding: .9rem 1rem;
}

.wb-info-label {
    color: var(--wb-muted);
    font-size: .84rem;
    margin-bottom: .2rem;
}

.wb-info-value {
    color: var(--wb-text);
    font-size: 1.05rem;
    font-weight: 700;
}

.wb-operator-box {
    background: linear-gradient(180deg, #ffffff 0%, #f4f8ff 100%);
    border: 1px solid var(--wb-border);
    border-radius: 18px;
    box-shadow: var(--wb-shadow);
    padding: 1rem;
}

.wb-operator-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: .5rem;
    margin-bottom: .55rem;
}

.wb-operator-badge {
    display: inline-flex;
    align-items: center;
    padding: .26rem .56rem;
    border-radius: 999px;
    background: var(--wb-primary-soft);
    color: var(--wb-primary);
    font-size: .74rem;
    font-weight: 800;
}

.wb-operator-state {
    font-size: .74rem;
    color: var(--wb-muted);
    font-weight: 700;
}

.wb-operator-name {
    font-size: 1.18rem;
    font-weight: 800;
    color: var(--wb-text);
    margin-bottom: .18rem;
}

.wb-operator-meta {
    font-size: .86rem;
    color: var(--wb-muted);
}

.wb-operator-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: .55rem;
    margin-top: .8rem;
}

.wb-operator-chip {
    border: 1px solid var(--wb-border);
    border-radius: 14px;
    background: var(--wb-surface);
    padding: .7rem .75rem;
}

.wb-operator-chip span {
    display: block;
    font-size: .75rem;
    color: var(--wb-muted);
    margin-bottom: .2rem;
}

.wb-operator-chip strong {
    font-size: .88rem;
    color: var(--wb-text);
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stDateInput input,
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--wb-surface) !important;
    color: var(--wb-text) !important;
    border: 1px solid var(--wb-border) !important;
    border-radius: 14px !important;
    box-shadow: none !important;
}

.stButton > button, .stFormSubmitButton > button {
    width: 100%;
    min-height: 44px;
    font-size: 1rem;
    font-weight: 700;
    white-space: nowrap;
    border-radius: 14px !important;
    border: 1px solid var(--wb-border) !important;
    background: var(--wb-surface) !important;
    color: var(--wb-text) !important;
    box-shadow: none !important;
}

.stButton > button:hover, .stFormSubmitButton > button:hover {
    border-color: var(--wb-primary) !important;
    color: var(--wb-primary) !important;
    background: var(--wb-primary-soft) !important;
}

[data-testid="stSidebar"] .stPageLink a {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
    padding: .72rem .86rem !important;
    margin-bottom: .42rem !important;
    border: 1px solid var(--wb-border) !important;
    border-radius: 14px !important;
    background: var(--wb-surface) !important;
    text-decoration: none !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] .stPageLink a:hover {
    border-color: var(--wb-primary) !important;
    background: var(--wb-primary-soft) !important;
    color: var(--wb-primary) !important;
}

[data-testid="stSidebar"] .stPageLink a[aria-current="page"] {
    background: linear-gradient(135deg, #2f6fed 0%, #4f8cff 100%) !important;
    color: #ffffff !important;
    border-color: #2f6fed !important;
    box-shadow: 0 10px 24px rgba(47,111,237,.24) !important;
}

[data-testid="stSidebar"] .stPageLink a[aria-current="page"] * {
    color: #ffffff !important;
}

[data-testid="stMetricValue"],
[data-testid="stMetricLabel"] {
    color: var(--wb-text) !important;
}

[data-testid="stDataFrame"],
[data-testid="stTable"],
[data-testid="stPlotlyChart"] {
    border: 1px solid var(--wb-border);
    border-radius: 18px;
    overflow: hidden;
    background: var(--wb-surface);
}

[data-testid="stAlert"] {
    border-radius: 14px;
    border: 1px solid var(--wb-border);
}

.stInfo { background: var(--wb-primary-soft) !important; }
.stSuccess { background: var(--wb-success-soft) !important; }
.stError { background: var(--wb-danger-soft) !important; }

.stTabs [data-baseweb="tab-list"] { gap: .4rem; }

.stTabs [data-baseweb="tab"] {
    border-radius: 12px 12px 0 0;
    background: var(--wb-surface);
    border: 1px solid var(--wb-border);
    padding: .7rem 1rem;
}

.wb-stat-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: .85rem;
}

.wb-stat-card {
    background: var(--wb-card-grad);
    border: 1px solid var(--wb-border);
    border-radius: 18px;
    padding: .95rem 1rem;
    min-height: 104px;
    box-shadow: var(--wb-shadow);
}

.wb-stat-label {
    color: var(--wb-muted);
    font-size: .82rem;
    font-weight: 700;
    margin-bottom: .35rem;
}

.wb-stat-value {
    color: var(--wb-text);
    font-size: 1.9rem;
    font-weight: 800;
    line-height: 1;
}

@media (max-width: 1024px) {
    .wb-stat-grid,
    .wb-info-grid,
    .wb-operator-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}


.wb-operator-box {
    background: var(--wb-card-grad);
    border: 1px solid var(--wb-border);
    border-radius: 22px;
    box-shadow: var(--wb-shadow);
    padding: 1rem;
}
.wb-operator-top {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:.75rem;
    margin-bottom:.8rem;
}
.wb-operator-badge {
    display:inline-flex;
    padding:.42rem .7rem;
    border-radius:999px;
    background: var(--wb-primary-soft);
    color: var(--wb-text);
    font-size:.8rem;
    font-weight:800;
}
.wb-operator-state {font-size:.86rem;font-weight:700;color:var(--wb-text);}
.wb-operator-name {font-size:2rem;font-weight:800;line-height:1.05;margin-bottom:.35rem;}
.wb-operator-meta {color:var(--wb-muted);margin-bottom:.9rem;}
.wb-operator-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.6rem;}
.wb-operator-chip {background:var(--wb-surface);border:1px solid var(--wb-border);border-radius:16px;padding:.85rem .9rem;}
.wb-operator-chip span {display:block;color:var(--wb-muted);font-size:.82rem;margin-bottom:.25rem;}
.wb-operator-chip strong {font-size:1.35rem;}
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    border:1px solid var(--wb-border);
    border-radius:16px;
    background: var(--wb-surface);
    padding:.85rem 1rem;
    margin-bottom:.65rem;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
    border-color: var(--wb-primary);
    background: var(--wb-primary-soft);
}
.wb-brief-desc {color:var(--wb-muted);font-size:.9rem;line-height:1.45;}

</style>
"""


def render_streamlit_base_style() -> None:
    root_vars = _theme_vars(_LIGHT)
    css = BASE_CSS.replace("__ROOT_VARS__", root_vars)
    st.markdown(css, unsafe_allow_html=True)
