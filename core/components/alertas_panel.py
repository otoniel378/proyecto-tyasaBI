"""
alertas_panel.py — Componentes visuales de alertas y estado para TYASA BI.
Renderiza anomalías, termómetros de mes y semáforos de área.
"""

from __future__ import annotations
import streamlit as st
from config import COLORS


# ── Anomalía card ─────────────────────────────────────────────────────────────

def render_anomalia_card(
    titulo: str,
    descripcion: str,
    severidad: str = "media",      # "alta" | "media" | "baja"
    tipo: str = "",                # "Fuga" | "Enfriamiento" | "Cambio Mix" | ...
    delta_pct: float | None = None,
    cliente: str = "",
    producto: str = "",
    fecha: str = "",
) -> None:
    color_map = {
        "alta":  (COLORS["danger"],  "rgba(231,76,60,0.12)"),
        "media": (COLORS["warning"], "rgba(243,156,18,0.12)"),
        "baja":  (COLORS["primary"], "rgba(74,159,212,0.12)"),
    }
    border_color, bg_color = color_map.get(severidad.lower(), color_map["media"])

    icon_map = {
        "alta":  "🔴",
        "media": "🟡",
        "baja":  "🔵",
    }
    icon = icon_map.get(severidad.lower(), "⚪")

    delta_html = ""
    if delta_pct is not None:
        arrow = "▼" if delta_pct < 0 else "▲"
        c = COLORS["danger"] if delta_pct < 0 else COLORS["success"]
        delta_html = (
            f"<span style='color:{c};font-size:0.8rem;font-weight:600;'>"
            f"{arrow} {abs(delta_pct):.1f}%</span> "
        )

    meta_parts = []
    if cliente:
        meta_parts.append(f"<span style='color:{COLORS['text_light']};font-size:0.75rem;'>👤 {cliente}</span>")
    if producto:
        meta_parts.append(f"<span style='color:{COLORS['text_light']};font-size:0.75rem;'>📦 {producto}</span>")
    if fecha:
        meta_parts.append(f"<span style='color:{COLORS['text_light']};font-size:0.75rem;'>📅 {fecha}</span>")
    meta_html = "  &nbsp;·&nbsp;  ".join(meta_parts) if meta_parts else ""

    tipo_badge = ""
    if tipo:
        tipo_badge = (
            f"<span style='background:{bg_color};color:{border_color};"
            f"padding:2px 8px;border-radius:10px;font-size:0.72rem;font-weight:600;"
            f"margin-left:8px;'>{tipo}</span>"
        )

    st.markdown(
        f"""
        <div style='
            background:{bg_color};
            border:1px solid {border_color};
            border-left:4px solid {border_color};
            border-radius:8px;
            padding:12px 16px;
            margin-bottom:8px;
        '>
            <div style='display:flex;align-items:center;margin-bottom:4px;'>
                <span style='font-size:0.95rem;font-weight:700;color:{COLORS["text"]};'>
                    {icon} {titulo}
                </span>
                {tipo_badge}
            </div>
            <p style='color:{COLORS["neutral"]};font-size:0.83rem;margin:4px 0;'>{descripcion}</p>
            <div style='margin-top:4px;'>{delta_html}{meta_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Termómetro del mes (progreso vs objetivo) ─────────────────────────────────

def render_termometro_mes(
    real: float,
    objetivo: float,
    label: str = "Cierre del mes",
    sufijo: str = " ton",
    dias_restantes: int | None = None,
) -> None:
    pct = min(real / objetivo * 100, 120) if objetivo > 0 else 0
    bar_fill = min(pct, 100)

    if pct >= 95:
        bar_color = COLORS["success"]
        estado = "En objetivo"
        estado_color = COLORS["success"]
    elif pct >= 80:
        bar_color = COLORS["warning"]
        estado = "En riesgo"
        estado_color = COLORS["warning"]
    else:
        bar_color = COLORS["danger"]
        estado = "Por debajo del objetivo"
        estado_color = COLORS["danger"]

    proyeccion_html = ""
    if dias_restantes is not None and dias_restantes > 0:
        proyeccion_html = (
            f"<span style='color:{COLORS['text_light']};font-size:0.78rem;'>"
            f"· {dias_restantes} días restantes</span>"
        )

    st.markdown(
        f"""
        <div style='
            background:{COLORS["surface"]};
            border:1px solid {COLORS["border"]};
            border-radius:10px;
            padding:18px 20px;
            margin-bottom:12px;
        '>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;'>
                <span style='color:{COLORS["text_light"]};font-size:0.78rem;font-weight:600;
                             text-transform:uppercase;letter-spacing:0.05em;'>{label}</span>
                <span style='color:{estado_color};font-size:0.78rem;font-weight:700;'>
                    {estado}
                </span>
            </div>
            <div style='display:flex;align-items:baseline;gap:8px;margin-bottom:12px;'>
                <span style='color:{COLORS["text"]};font-size:1.8rem;font-weight:800;'>
                    {real:,.1f}{sufijo}
                </span>
                <span style='color:{COLORS["text_light"]};font-size:0.9rem;'>
                    / {objetivo:,.1f}{sufijo}
                </span>
                {proyeccion_html}
            </div>
            <!-- Barra de progreso -->
            <div style='position:relative;background:{COLORS["border"]};border-radius:6px;height:10px;overflow:visible;'>
                <div style='width:{bar_fill:.1f}%;height:100%;background:{bar_color};
                            border-radius:6px;transition:width 0.5s ease;'></div>
                <!-- Marcador objetivo -->
                <div style='position:absolute;top:-4px;left:100%;transform:translateX(-50%);
                            width:2px;height:18px;background:{COLORS["text_light"]};opacity:0.6;'></div>
            </div>
            <div style='display:flex;justify-content:flex-end;margin-top:4px;'>
                <span style='color:{COLORS["text_light"]};font-size:0.75rem;'>{pct:.1f}% del objetivo</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Semáforo por área ─────────────────────────────────────────────────────────

def render_semaforo_area(
    areas: list[dict],
) -> None:
    """
    areas: lista de dicts con keys:
      nombre, valor, objetivo, unidad (opt), icono (opt)
    """
    html_cards = []
    for a in areas:
        nombre = a.get("nombre", "")
        valor = a.get("valor", 0)
        objetivo = a.get("objetivo", 1)
        unidad = a.get("unidad", "")
        icono = a.get("icono", "")
        pct = (valor / objetivo * 100) if objetivo else 0

        if pct >= 95:
            color = COLORS["success"]
            dot = "🟢"
        elif pct >= 75:
            color = COLORS["warning"]
            dot = "🟡"
        else:
            color = COLORS["danger"]
            dot = "🔴"

        html_cards.append(
            f"""
            <div style='
                flex:1;min-width:120px;
                background:{COLORS["surface"]};
                border:1px solid {COLORS["border"]};
                border-top:3px solid {color};
                border-radius:8px;
                padding:12px 14px;
                text-align:center;
            '>
                <div style='font-size:1.1rem;margin-bottom:2px;'>{icono or dot}</div>
                <div style='color:{COLORS["text_light"]};font-size:0.72rem;font-weight:600;
                            text-transform:uppercase;letter-spacing:0.04em;margin-bottom:4px;'>
                    {nombre}
                </div>
                <div style='color:{COLORS["text"]};font-size:1.3rem;font-weight:700;'>
                    {valor:,.1f}<span style='font-size:0.75rem;color:{COLORS["text_light"]};'>{unidad}</span>
                </div>
                <div style='color:{color};font-size:0.75rem;font-weight:600;margin-top:2px;'>
                    {pct:.0f}% obj.
                </div>
            </div>
            """
        )

    st.markdown(
        f"<div style='display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;'>"
        + "".join(html_cards)
        + "</div>",
        unsafe_allow_html=True,
    )
