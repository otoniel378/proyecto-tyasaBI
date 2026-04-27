"""
charts.py — Funciones reutilizables de graficos con Plotly.
Todas retornan figuras de Plotly configuradas con la paleta TYASA.
Compartido entre todas las areas.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from config import COLORS, COLOR_SEQUENCE, HEATMAP_COLORSCALE


_LAYOUT_BASE = dict(
    paper_bgcolor=COLORS["surface"],
    plot_bgcolor=COLORS["surface"],
    font=dict(family="Inter, Arial, sans-serif", color=COLORS["text"], size=12),
    margin=dict(l=40, r=20, t=50, b=40),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.25,
        xanchor="center",
        x=0.5,
        font=dict(size=11, color=COLORS["text_light"]),
        bgcolor="rgba(0,0,0,0)",
    ),
)


def linea_temporal(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    titulo: str = "",
    y_label: str = "Toneladas",
    show_area: bool = False,
) -> go.Figure:
    if df.empty:
        return _empty_fig(titulo)

    if color and color in df.columns:
        fig = px.line(
            df, x=x, y=y, color=color,
            color_discrete_sequence=COLOR_SEQUENCE,
            title=titulo,
        )
    else:
        fig = px.area(df, x=x, y=y, title=titulo) if show_area else px.line(df, x=x, y=y, title=titulo)
        fig.update_traces(line_color=COLORS["primary"])
        if show_area:
            fig.update_traces(fillcolor="rgba(27,58,92,0.15)")

    fig.update_layout(
        **_LAYOUT_BASE,
        xaxis_title="",
        yaxis_title=y_label,
        title=dict(font=dict(size=14, color=COLORS["text"]), x=0),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=COLORS["border"])
    return fig


def barras_horizontales(
    df: pd.DataFrame,
    x: str,
    y: str,
    titulo: str = "",
    x_label: str = "Toneladas",
    max_items: int = 15,
) -> go.Figure:
    if df.empty:
        return _empty_fig(titulo)

    df_plot = df.nlargest(max_items, x).sort_values(x, ascending=True)
    fig = px.bar(
        df_plot, x=x, y=y, orientation="h", title=titulo,
        color_discrete_sequence=[COLORS["primary"]], text=x,
    )
    fig.update_traces(texttemplate="%{text:,.1f}", textposition="outside")
    fig.update_layout(
        **_LAYOUT_BASE,
        xaxis_title=x_label,
        yaxis_title="",
        title=dict(font=dict(size=14, color=COLORS["text"]), x=0),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor=COLORS["border"])
    fig.update_yaxes(showgrid=False)
    return fig


def donut(
    df: pd.DataFrame,
    names: str,
    values: str,
    titulo: str = "",
    hole: float = 0.55,
) -> go.Figure:
    if df.empty:
        return _empty_fig(titulo)

    fig = px.pie(
        df, names=names, values=values, hole=hole,
        title=titulo, color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_traces(
        textposition="outside",
        textinfo="percent+label",
        hovertemplate="%{label}<br>%{value:,.1f} ton<br>%{percent}",
    )
    fig.update_layout(
        **_LAYOUT_BASE,
        showlegend=False,
        title=dict(font=dict(size=14, color=COLORS["text"]), x=0),
    )
    return fig


def treemap(
    df: pd.DataFrame,
    path: list[str],
    values: str,
    titulo: str = "",
) -> go.Figure:
    if df.empty:
        return _empty_fig(titulo)

    fig = px.treemap(
        df, path=path, values=values, title=titulo,
        color=values, color_continuous_scale=HEATMAP_COLORSCALE,
    )
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(font=dict(size=14, color=COLORS["text"]), x=0),
    )
    return fig


def heatmap(
    pivot_df: pd.DataFrame,
    titulo: str = "",
    x_label: str = "Anio",
    y_label: str = "Mes",
    fmt: str = ".0f",
) -> go.Figure:
    if pivot_df.empty:
        return _empty_fig(titulo)

    fig = go.Figure(
        go.Heatmap(
            z=pivot_df.values,
            x=[str(c) for c in pivot_df.columns],
            y=pivot_df.index.tolist(),
            colorscale=HEATMAP_COLORSCALE,
            hoverongaps=False,
            hovertemplate=f"<b>%{{y}} — %{{x}}</b><br>Toneladas: %{{z:{fmt}}}<extra></extra>",
            showscale=True,
        )
    )
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text=titulo, font=dict(size=14, color=COLORS["text"]), x=0),
        xaxis_title=x_label,
        yaxis_title=y_label,
    )
    return fig


def pareto(
    df: pd.DataFrame,
    x: str,
    y: str,
    y_acum: str = "PCT_ACUM",
    titulo: str = "Analisis Pareto",
    max_items: int = 30,
) -> go.Figure:
    if df.empty:
        return _empty_fig(titulo)

    df_plot = df.head(max_items).copy()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_plot[x], y=df_plot[y], name="Toneladas",
        marker_color=COLORS["primary"],
        hovertemplate=f"%{{x}}<br>Toneladas: %{{y:,.1f}}<extra></extra>",
    ))

    if y_acum in df_plot.columns:
        fig.add_trace(go.Scatter(
            x=df_plot[x], y=df_plot[y_acum], name="% Acumulado",
            yaxis="y2",
            line=dict(color=COLORS["warning"], width=2.5, dash="dot"),
            mode="lines+markers", marker=dict(size=5),
            hovertemplate=f"%{{x}}<br>Acumulado: %{{y:.1f}}%<extra></extra>",
        ))
        fig.add_hline(
            y=80, yref="y2",
            line=dict(color=COLORS["danger"], width=1.5, dash="dash"),
            annotation_text="80%", annotation_position="right",
        )

    layout = {k: v for k, v in _LAYOUT_BASE.items() if k != "legend"}
    fig.update_layout(
        **layout,
        title=dict(text=titulo, font=dict(size=14, color=COLORS["text"]), x=0),
        xaxis=dict(title="", tickangle=-40, showgrid=False),
        yaxis=dict(title="Toneladas", gridcolor="#E5E7EB"),
        yaxis2=dict(
            title="% Acumulado", overlaying="y", side="right",
            range=[0, 105], showgrid=False, ticksuffix="%",
        ),
        legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"),
        barmode="overlay",
    )
    return fig


def scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    size: str | None = None,
    color: str | None = None,
    hover_name: str | None = None,
    titulo: str = "",
    x_label: str = "",
    y_label: str = "",
) -> go.Figure:
    if df.empty:
        return _empty_fig(titulo)

    fig = px.scatter(
        df, x=x, y=y, size=size, color=color, hover_name=hover_name,
        title=titulo, color_discrete_sequence=COLOR_SEQUENCE,
        color_continuous_scale=HEATMAP_COLORSCALE,
    )
    fig.update_layout(
        **_LAYOUT_BASE,
        xaxis_title=x_label or x,
        yaxis_title=y_label or y,
        title=dict(font=dict(size=14, color=COLORS["text"]), x=0),
    )
    return fig


def multi_axis_line(
    df: pd.DataFrame,
    x: str,
    y1: str,
    y2: str,
    titulo: str = "",
    y1_label: str = "",
    y2_label: str = "",
    color1: str | None = None,
    color2: str | None = None,
) -> go.Figure:
    if df.empty:
        return _empty_fig(titulo)

    c1 = color1 or COLORS["primary"]
    c2 = color2 or COLORS["accent"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x], y=df[y1], name=y1_label or y1,
        line=dict(color=c1, width=2.5),
        mode="lines", yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=df[x], y=df[y2], name=y2_label or y2,
        line=dict(color=c2, width=2.5, dash="dot"),
        mode="lines", yaxis="y2",
    ))
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text=titulo, font=dict(size=14, color=COLORS["text"]), x=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(title=y1_label or y1, gridcolor=COLORS["border"]),
        yaxis2=dict(
            title=y2_label or y2, overlaying="y", side="right",
            showgrid=False,
        ),
    )
    return fig


def yoy_comparison(
    df: pd.DataFrame,
    x: str,
    y: str,
    anio_col: str = "ANIO",
    titulo: str = "",
    y_label: str = "Toneladas",
    max_anios: int = 5,
) -> go.Figure:
    if df.empty:
        return _empty_fig(titulo)

    anios = sorted(df[anio_col].unique(), reverse=True)[:max_anios]
    fig = go.Figure()
    palette = COLOR_SEQUENCE
    for i, anio in enumerate(sorted(anios)):
        df_a = df[df[anio_col] == anio].copy()
        fig.add_trace(go.Scatter(
            x=df_a[x], y=df_a[y], name=str(anio),
            mode="lines+markers",
            line=dict(color=palette[i % len(palette)], width=2),
            marker=dict(size=5),
        ))
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text=titulo, font=dict(size=14, color=COLORS["text"]), x=0),
        xaxis_title="",
        yaxis_title=y_label,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=COLORS["border"])
    return fig


def sparkline(
    series: list[float] | pd.Series,
    color: str | None = None,
    height: int = 60,
    show_area: bool = True,
) -> go.Figure:
    data = list(series) if not isinstance(series, list) else series
    c = color or COLORS["primary"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=data,
        mode="lines",
        line=dict(color=c, width=2),
        fill="tozeroy" if show_area else "none",
        fillcolor=c.replace(")", ",0.15)").replace("rgb", "rgba") if "rgb" in c else f"{c}26",
        hoverinfo="skip",
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def gauge_chart(
    value: float,
    min_val: float = 0,
    max_val: float = 100,
    titulo: str = "",
    suffix: str = "%",
    threshold_warn: float | None = None,
    threshold_crit: float | None = None,
) -> go.Figure:
    steps = []
    if threshold_crit is not None:
        steps = [
            dict(range=[min_val, threshold_warn or max_val * 0.5], color=COLORS["surface2"]),
            dict(range=[threshold_warn or max_val * 0.5, threshold_crit], color=COLORS["surface2"]),
            dict(range=[threshold_crit, max_val], color=COLORS["surface2"]),
        ]

    bar_color = COLORS["primary"]
    if threshold_warn is not None and value < threshold_warn:
        bar_color = COLORS["danger"]
    elif threshold_crit is not None and value < threshold_crit:
        bar_color = COLORS["warning"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix=suffix, font=dict(color=COLORS["text"], size=28)),
        gauge=dict(
            axis=dict(range=[min_val, max_val], tickcolor=COLORS["text_light"],
                      tickfont=dict(color=COLORS["text_light"], size=11)),
            bar=dict(color=bar_color, thickness=0.6),
            bgcolor=COLORS["surface2"],
            borderwidth=1,
            bordercolor=COLORS["border"],
            steps=steps,
            threshold=dict(
                line=dict(color=COLORS["accent"], width=2),
                thickness=0.75,
                value=value,
            ) if threshold_crit else None,
        ),
        title=dict(text=titulo, font=dict(color=COLORS["text_light"], size=12)),
    ))
    fig.update_layout(
        paper_bgcolor=COLORS["surface"],
        font=dict(family="Inter, Arial, sans-serif", color=COLORS["text"]),
        margin=dict(l=20, r=20, t=50, b=20),
        height=220,
    )
    return fig


def _empty_fig(titulo: str = "") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        **_LAYOUT_BASE,
        title=dict(text=titulo, font=dict(size=14, color=COLORS["text"]), x=0),
        annotations=[dict(
            text="Sin datos disponibles para el periodo seleccionado.",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(size=13, color=COLORS["neutral"]),
        )],
    )
    return fig
