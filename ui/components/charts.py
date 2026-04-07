
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st


def _theme_colors():
    return {
        "paper": "#ffffff",
        "plot": "#ffffff",
        "grid": "rgba(148,163,184,0.18)",
        "line": "#dbe4f0",
        "text": "#132238",
        "muted": "#66758b",
        "title": "#132238",
    }


def _base_layout(fig, title: str | None = None):
    t = _theme_colors()
    fig.update_layout(
        template=None,
        title=dict(text=title or "", x=0.02, xanchor="left", font=dict(size=18, color=t["title"])),
        margin=dict(l=28, r=20, t=60, b=34),
        paper_bgcolor=t["paper"],
        plot_bgcolor=t["plot"],
        font=dict(color=t["text"], size=13),
        hoverlabel=dict(bgcolor=t["paper"], bordercolor=t["line"], font_size=12, font_color=t["text"]),
    )
    fig.update_xaxes(showgrid=False, linecolor=t["line"], tickfont=dict(color=t["muted"]), zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor=t["grid"], linecolor=t["line"], tickfont=dict(color=t["muted"]), zeroline=False, automargin=True, title_standoff=24)
    return fig


def draw_bar_chart(df: pd.DataFrame, x: str, y: str, title: str | None = None):
    if df.empty:
        return _base_layout(go.Figure(), title)
    vals = df[y].tolist()
    colors = []
    for v in vals:
        if v >= 0.8:
            colors.append("#22c55e")
        elif v >= 0.6:
            colors.append("#06b6d4")
        elif v >= 0.4:
            colors.append("#3b82f6")
        elif v >= 0.25:
            colors.append("#f59e0b")
        else:
            colors.append("#ef4444")
    t = _theme_colors()
    fig = go.Figure(data=[go.Bar(
        x=df[x], y=df[y],
        marker=dict(color=colors, line=dict(color=t["line"], width=1)),
        text=[f"{v:.2f}" for v in vals],
        textposition="outside",
        textfont=dict(color=t["title"], size=11),
        hovertemplate="%{x}<br>점수: %{y:.2f}<extra></extra>",
    )])
    fig.update_layout(bargap=0.22)
    return _base_layout(fig, title)


def draw_multi_line_chart(df: pd.DataFrame, x: str, series: list[tuple[str, str]], title: str | None = None):
    if df.empty:
        return _base_layout(go.Figure(), title)
    fig = go.Figure()
    palette = ["#22d3ee", "#22c55e", "#f59e0b", "#ef4444"]
    for idx, (col, label) in enumerate(series):
        fig.add_trace(go.Scatter(
            x=df[x],
            y=df[col],
            mode="lines+markers",
            name=label,
            line=dict(color=palette[idx % len(palette)], width=3),
            marker=dict(size=6),
            hovertemplate="%{x}<br>" + label + ": %{y:.3f}<extra></extra>",
        ))
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"))
    return _base_layout(fig, title)


def draw_line_chart(df: pd.DataFrame, x: str, y: str, title: str | None = None, y_title: str | None = None):
    if df.empty:
        return _base_layout(go.Figure(), title)
    t = _theme_colors()
    fig = go.Figure(data=[go.Scatter(
        x=df[x], y=df[y], mode="lines+markers",
        line=dict(color="#22d3ee", width=3),
        marker=dict(size=7, color="#22c55e", line=dict(color=t["line"], width=1)),
        hovertemplate="%{x}시<br>%{y:.1f}<extra></extra>",
    )])
    fig.update_layout(
        yaxis_title=y_title or y,
        xaxis_title="시간",
        margin=dict(l=42, r=20, t=60, b=44),
    )
    fig.update_xaxes(dtick=2, tickangle=0)
    return _base_layout(fig, title)


def draw_heatmap_chart(pivot_df: pd.DataFrame, title: str = "Heatmap"):
    if pivot_df.empty:
        return _base_layout(go.Figure(), title)
    t = _theme_colors()
    fig = px.imshow(
        pivot_df,
        aspect="auto",
        color_continuous_scale=[
            [0.0, "#7f1d1d"],
            [0.18, "#ef4444"],
            [0.35, "#f59e0b"],
            [0.55, "#60a5fa"],
            [0.78, "#22d3ee"],
            [1.0, "#22c55e"],
        ],
        text_auto=".2f",
    )
    fig.update_traces(
        hovertemplate="월 %{y}<br>연도 %{x}<br>점수 %{z:.2f}<extra></extra>",
        xgap=3,
        ygap=3,
    )
    fig.update_layout(
        title=dict(text=title, x=0.02, xanchor="left", font=dict(size=18, color=t["title"])),
        margin=dict(l=28, r=20, t=74, b=44),
        paper_bgcolor=t["paper"],
        plot_bgcolor=t["plot"],
        font=dict(color=t["text"], size=13),
        coloraxis_colorbar=dict(
            title=dict(text="점수"),
            thickness=12,
            outlinewidth=0,
            tickfont=dict(color=t["muted"]),
        ),
        xaxis_title=None,
        yaxis_title=None,
    )
    fig.update_xaxes(side="bottom", tickfont=dict(color=t["text"]), showgrid=False, linecolor=t["line"], automargin=True)
    fig.update_yaxes(tickfont=dict(color=t["text"]), showgrid=False, linecolor=t["line"], automargin=True)
    return fig


def draw_annual_day_heatmap(mat: pd.DataFrame, title: str, metric_label: str = "체감온도"):
    if mat.empty:
        return _base_layout(go.Figure(), title)
    t = _theme_colors()
    fig = go.Figure(
        data=[
            go.Heatmap(
                z=mat.values,
                x=[f"{c}일" for c in mat.columns],
                y=[f"{i}월" for i in mat.index],
                colorscale=[
                    [0.0, "#2563eb"],
                    [0.25, "#06b6d4"],
                    [0.5, "#22c55e"],
                    [0.75, "#f59e0b"],
                    [1.0, "#ef4444"],
                ],
                zmin=-20 if metric_label == "기온" else -25,
                zmax=35,
                text=[[("" if pd.isna(v) else f"{v:.1f}") for v in row] for row in mat.values],
                texttemplate="%{text}",
                textfont=dict(size=9, color="white"),
                hovertemplate="%{y} %{x}<br>" + metric_label + ": %{z:.1f}<extra></extra>",
                colorbar=dict(title=metric_label, thickness=10),
                xgap=1,
                ygap=1,
            )
        ]
    )
    fig.update_layout(
        title=dict(text=title, x=0.02, xanchor="left", font=dict(size=18, color=t["title"])),
        margin=dict(l=20, r=16, t=54, b=18),
        paper_bgcolor=t["paper"],
        plot_bgcolor=t["plot"],
        font=dict(color=t["text"], size=12),
    )
    fig.update_xaxes(side="bottom", tickangle=0, dtick=2, showgrid=False, linecolor=t["line"], tickfont=dict(color=t["muted"], size=10))
    fig.update_yaxes(showgrid=False, linecolor=t["line"], tickfont=dict(color=t["text"], size=11), autorange="reversed")
    return fig


def draw_daily_reference_chart(df: pd.DataFrame, metric_label: str, title: str):
    if df.empty:
        return _base_layout(go.Figure(), title)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["hour"],
        y=df["actual"],
        mode="lines+markers",
        name=metric_label,
        line=dict(color="#2563eb", width=3),
        marker=dict(size=6),
        hovertemplate="%{x}시<br>실측: %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["hour"],
        y=df["baseline"],
        mode="lines",
        name="기준",
        line=dict(color="#ef4444", width=2, dash="dot"),
        hovertemplate="%{x}시<br>기준: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="시간",
        yaxis_title=metric_label,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"),
        margin=dict(l=36, r=16, t=56, b=34),
    )
    fig.update_xaxes(dtick=2, tickangle=0)
    return _base_layout(fig, title)
