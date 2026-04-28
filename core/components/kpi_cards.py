"""
kpi_cards.py - Tarjetas KPI prominentes estilo dashboard Power BI.
"""

import streamlit as st
from config import COLORS

_ACCENTS = ["#1B3A5C", "#2563EB", "#059669", "#D97706", "#7C3AED", "#DC2626"]


def kpi_card(label, value, delta=None, delta_label="", icon="", suffix="", prefix="",
             help_text=None, accent_color=None):
    accent = accent_color or COLORS["primary"]

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
            up = delta_num >= 0
            color = "#059669" if up else "#DC2626"
            bg    = "#ECFDF5" if up else "#FEF2F2"
            arrow = "▲" if up else "▼"
            delta_html = (
                f'<div style="display:flex;align-items:center;gap:6px;margin-top:6px;">'
                f'<span style="color:{color};background:{bg};font-size:0.68rem;font-weight:700;'
                f'padding:2px 7px;border-radius:20px;">{arrow} {abs(delta_num):.1f}%</span>'
                f'<span style="color:#94A3B8;font-size:0.68rem;">{delta_label}</span>'
                f'</div>'
            )
        except (TypeError, ValueError):
            delta_html = f'<div style="color:#94A3B8;font-size:0.68rem;margin-top:3px;">{delta}</div>'

    help_attr = f'title="{help_text}"' if help_text else ""

    st.markdown(
        f"""
        <div {help_attr} style="
            background:#FFFFFF;
            border:1.5px solid #DDE3EC;
            border-top:4px solid {accent};
            border-radius:8px;
            padding:14px 16px 12px;
            box-shadow:0 2px 8px rgba(15,23,42,0.08), 0 1px 3px rgba(15,23,42,0.04);
            transition:box-shadow 0.2s ease, transform 0.15s ease;
            cursor:default;
        ">
            <div style="color:#64748B;font-size:0.62rem;font-weight:700;
                        text-transform:uppercase;letter-spacing:0.09em;margin-bottom:5px;">
                {(icon + '  ') if icon else ''}{label}
            </div>
            <div style="color:#0F172A;font-size:1.55rem;font-weight:700;
                        line-height:1.1;font-family:'Segoe UI',sans-serif;letter-spacing:-0.01em;">
                {value_str}
            </div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(kpis):
    cols = st.columns(len(kpis))
    for i, (col, kpi) in enumerate(zip(cols, kpis)):
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
                accent_color=kpi.get("accent_color", _ACCENTS[i % len(_ACCENTS)]),
            )


def seccion_titulo(titulo, subtitulo=""):
    sub_html = (
        f'<span style="color:#94A3B8;font-size:0.72rem;font-weight:400;margin-left:8px;">'
        f'{subtitulo}</span>'
        if subtitulo else ""
    )
    st.markdown(
        f'<div style="display:flex;align-items:baseline;gap:4px;'
        f'margin:12px 0 6px;padding-bottom:6px;border-bottom:1.5px solid #DDE3EC;">'
        f'<span style="color:#1B3A5C;font-size:0.72rem;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:0.08em;">{titulo}</span>'
        f'{sub_html}</div>',
        unsafe_allow_html=True,
    )
