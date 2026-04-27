"""
kpi_cards.py — Tarjetas KPI ejecutivas reutilizables.
Renderiza metricas con formato corporativo TYASA.
Compartido entre todas las areas.
"""

import streamlit as st
import pandas as pd
from typing import Sequence
from config import COLORS


def kpi_card(
    label: str,
    value: str | float | int,
    delta: str | float | None = None,
    delta_label: str = "",
    icon: str = "",
    suffix: str = "",
    prefix: str = "",
    help_text: str | None = None,
) -> None:
    if isinstance(value, float):
        value_str = f"{prefix}{value:,.1f}{suffix}"
    elif isinstance(value, int):
        value_str = f"{prefix}{value:,}{suffix}"
    else:
        value_str = f"{prefix}{value}{suffix}"

    delta_html = ""
    if delta is not None:
        try:
            delta_num = float(delta)
            color = COLORS["success"] if delta_num >= 0 else COLORS["danger"]
            arrow = "▲" if delta_num >= 0 else "▼"
            delta_html = (
                f"<span style='color:{color};font-size:0.82rem;font-weight:600;'>"
                f"{arrow} {abs(delta_num):.1f}%"
                f"</span>"
                f"<span style='color:{COLORS['text_light']};font-size:0.78rem;'> {delta_label}</span>"
            )
        except (TypeError, ValueError):
            delta_html = f"<span style='color:{COLORS['neutral']};font-size:0.82rem;'>{delta}</span>"

    help_attr = f'title="{help_text}"' if help_text else ""

    st.markdown(
        f"""
        <div {help_attr} style='
            background:{COLORS["surface"]};
            border:1px solid #E5E7EB;
            border-left:4px solid {COLORS["primary"]};
            border-radius:8px;
            padding:16px 20px;
            margin-bottom:8px;
        '>
            <div style='
                color:{COLORS["text_light"]};
                font-size:0.78rem;
                font-weight:600;
                text-transform:uppercase;
                letter-spacing:0.05em;
                margin-bottom:4px;
            '>{icon} {label}</div>
            <div style='
                color:{COLORS["primary"]};
                font-size:1.8rem;
                font-weight:700;
                line-height:1.2;
                margin-bottom:4px;
            '>{value_str}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(kpis: list[dict]) -> None:
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        with col:
            kpi_card(
                label=kpi.get("label", ""),
                value=kpi.get("value", 0),
                delta=kpi.get("delta"),
                delta_label=kpi.get("delta_label", "vs mes anterior"),
                icon=kpi.get("icon", ""),
                suffix=kpi.get("suffix", ""),
                prefix=kpi.get("prefix", ""),
                help_text=kpi.get("help_text"),
            )


def seccion_titulo(titulo: str, subtitulo: str = "") -> None:
    st.markdown(
        f"""
        <div style='margin:24px 0 12px 0;'>
            <h3 style='color:{COLORS["primary"]};margin:0;font-size:1.15rem;'>
                {titulo}
            </h3>
            {"<p style='color:" + COLORS["text_light"] + ";font-size:0.85rem;margin:2px 0 0 0;'>" + subtitulo + "</p>" if subtitulo else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Compact KPI (menor altura, para filas densas) ─────────────────────────────

def kpi_card_compact(
    label: str,
    value: str | float | int,
    delta: str | float | None = None,
    icon: str = "",
    suffix: str = "",
    prefix: str = "",
    accent: str | None = None,
) -> None:
    if isinstance(value, float):
        value_str = f"{prefix}{value:,.1f}{suffix}"
    elif isinstance(value, int):
        value_str = f"{prefix}{value:,}{suffix}"
    else:
        value_str = f"{prefix}{value}{suffix}"

    border_color = accent or COLORS["primary"]
    delta_html = ""
    if delta is not None:
        try:
            d = float(delta)
            color = COLORS["success"] if d >= 0 else COLORS["danger"]
            arrow = "▲" if d >= 0 else "▼"
            delta_html = f"<span style='color:{color};font-size:0.75rem;font-weight:600;'>{arrow} {abs(d):.1f}%</span>"
        except (TypeError, ValueError):
            delta_html = f"<span style='color:{COLORS['neutral']};font-size:0.75rem;'>{delta}</span>"

    st.markdown(
        f"""
        <div style='
            background:{COLORS["surface"]};
            border:1px solid {COLORS["border"]};
            border-left:3px solid {border_color};
            border-radius:6px;
            padding:10px 14px;
            margin-bottom:6px;
        '>
            <div style='color:{COLORS["text_light"]};font-size:0.72rem;font-weight:600;
                        text-transform:uppercase;letter-spacing:0.05em;margin-bottom:2px;'>
                {icon} {label}
            </div>
            <div style='color:{COLORS["text"]};font-size:1.35rem;font-weight:700;
                        line-height:1.1;margin-bottom:2px;'>
                {value_str}
            </div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── KPI con sparkline inline ──────────────────────────────────────────────────

def kpi_card_with_sparkline(
    label: str,
    value: str | float | int,
    series: Sequence[float],
    delta: float | None = None,
    icon: str = "",
    suffix: str = "",
    prefix: str = "",
    color: str | None = None,
) -> None:
    if isinstance(value, float):
        value_str = f"{prefix}{value:,.1f}{suffix}"
    elif isinstance(value, int):
        value_str = f"{prefix}{value:,}{suffix}"
    else:
        value_str = f"{prefix}{value}{suffix}"

    line_color = color or COLORS["primary"]
    delta_html = ""
    if delta is not None:
        c = COLORS["success"] if delta >= 0 else COLORS["danger"]
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = f"<span style='color:{c};font-size:0.78rem;font-weight:600;'>{arrow} {abs(delta):.1f}%</span>"

    # SVG sparkline
    data = list(series)
    if len(data) < 2:
        spark_svg = ""
    else:
        mn, mx = min(data), max(data)
        rng = mx - mn if mx != mn else 1
        w, h = 80, 28
        pts = []
        for i, v in enumerate(data):
            x = i / (len(data) - 1) * w
            y = h - ((v - mn) / rng) * h
            pts.append(f"{x:.1f},{y:.1f}")
        poly = " ".join(pts)
        spark_svg = (
            f"<svg width='{w}' height='{h}' style='display:block;'>"
            f"<polyline points='{poly}' fill='none' stroke='{line_color}' "
            f"stroke-width='2' stroke-linejoin='round'/></svg>"
        )

    st.markdown(
        f"""
        <div style='
            background:{COLORS["surface"]};
            border:1px solid {COLORS["border"]};
            border-left:4px solid {line_color};
            border-radius:8px;
            padding:14px 16px;
            margin-bottom:8px;
            display:flex;
            justify-content:space-between;
            align-items:center;
        '>
            <div>
                <div style='color:{COLORS["text_light"]};font-size:0.72rem;font-weight:600;
                            text-transform:uppercase;letter-spacing:0.05em;'>{icon} {label}</div>
                <div style='color:{COLORS["text"]};font-size:1.55rem;font-weight:700;
                            line-height:1.2;margin-top:2px;'>{value_str}</div>
                {delta_html}
            </div>
            <div style='opacity:0.8;'>{spark_svg}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Gauge KPI (arco de progreso semicircular) ─────────────────────────────────

def kpi_card_gauge(
    label: str,
    value: float,
    min_val: float = 0,
    max_val: float = 100,
    suffix: str = "%",
    thresholds: tuple[float, float] = (50, 75),
    icon: str = "",
) -> None:
    pct = max(0.0, min(1.0, (value - min_val) / (max_val - min_val) if max_val != min_val else 0))
    if pct < thresholds[0] / 100:
        bar_color = COLORS["danger"]
    elif pct < thresholds[1] / 100:
        bar_color = COLORS["warning"]
    else:
        bar_color = COLORS["success"]

    bar_w = int(pct * 100)
    value_str = f"{value:,.1f}{suffix}"

    st.markdown(
        f"""
        <div style='
            background:{COLORS["surface"]};
            border:1px solid {COLORS["border"]};
            border-radius:8px;
            padding:14px 16px;
            margin-bottom:8px;
        '>
            <div style='color:{COLORS["text_light"]};font-size:0.72rem;font-weight:600;
                        text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;'>
                {icon} {label}
            </div>
            <div style='color:{COLORS["text"]};font-size:1.5rem;font-weight:700;margin-bottom:8px;'>
                {value_str}
            </div>
            <div style='background:{COLORS["border"]};border-radius:4px;height:6px;overflow:hidden;'>
                <div style='width:{bar_w}%;height:100%;background:{bar_color};
                            border-radius:4px;transition:width 0.4s ease;'></div>
            </div>
            <div style='display:flex;justify-content:space-between;margin-top:3px;'>
                <span style='color:{COLORS["text_light"]};font-size:0.68rem;'>{min_val:g}</span>
                <span style='color:{COLORS["text_light"]};font-size:0.68rem;'>{max_val:g}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Badge inline (chip de estado) ────────────────────────────────────────────

def kpi_badge(text: str, variant: str = "primary") -> str:
    """Retorna HTML de un badge chip. variant: primary | accent | success | warning | danger | neutral."""
    colors = {
        "primary": (COLORS["primary"], "rgba(74,159,212,0.15)"),
        "accent":  (COLORS["accent"],  "rgba(224,92,45,0.15)"),
        "success": (COLORS["success"], "rgba(46,204,113,0.15)"),
        "warning": (COLORS["warning"], "rgba(243,156,18,0.15)"),
        "danger":  (COLORS["danger"],  "rgba(231,76,60,0.15)"),
        "neutral": (COLORS["neutral"], "rgba(143,163,177,0.15)"),
    }
    fg, bg = colors.get(variant, colors["neutral"])
    return (
        f"<span style='display:inline-block;padding:2px 10px;border-radius:12px;"
        f"font-size:0.75rem;font-weight:600;background:{bg};color:{fg};'>{text}</span>"
    )
