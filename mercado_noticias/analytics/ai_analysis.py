"""
ai_analysis.py — Análisis inteligente de sentimiento de mercado.

Flujo:
  1. Recibe lista de noticias (dicts con titulo/descripcion/url)
  2. Opcionalmente scrapea el contenido completo del artículo (trafilatura → BS4)
  3. Construye prompt de analista senior de commodities
  4. Llama a Gemini API (gemini-2.0-flash o gemini-1.5-flash)
  5. Cachea el resultado en cache/ai_summaries/<hash>.json para no repetir llamadas

Cache key: MD5(variable + str(round(sigma, 1)) + fecha_hoy)
"""

from __future__ import annotations
import hashlib
import json
import os
import re
import time
from datetime import datetime, date
from pathlib import Path

import requests

# ── Ruta de caché ─────────────────────────────────────────────────────────────
_ROOT_DIR   = Path(__file__).resolve().parents[2]          # raíz del proyecto
CACHE_DIR   = _ROOT_DIR / "cache" / "ai_summaries"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── Timeout HTTP general ───────────────────────────────────────────────────────
HTTP_TIMEOUT = 10  # segundos

# ══════════════════════════════════════════════════════════════════════════════
# SCRAPING DE ARTÍCULOS
# ══════════════════════════════════════════════════════════════════════════════

def _scrape_trafilatura(url: str) -> str:
    """Extrae texto del artículo usando trafilatura (mejor calidad)."""
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False,
                                        include_tables=False)
            return (text or "").strip()
    except ImportError:
        pass
    except Exception:
        pass
    return ""


def _scrape_bs4(url: str) -> str:
    """Fallback: extrae texto con requests + BeautifulSoup4."""
    try:
        from bs4 import BeautifulSoup
        headers = {"User-Agent": "Mozilla/5.0 (compatible; TyasaBI/1.0)"}
        resp = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.content, "html.parser")
        # Eliminar script, style, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        # Extraer párrafos
        paras = [p.get_text(separator=" ").strip()
                 for p in soup.find_all("p") if len(p.get_text()) > 60]
        return " ".join(paras[:30])          # máx ~30 párrafos
    except ImportError:
        pass
    except Exception:
        pass
    return ""


def scrape_articulo(url: str, max_chars: int = 2000) -> str:
    """
    Intenta trafilatura primero, BS4 de fallback.
    Trunca a max_chars para no sobrepasar el contexto del LLM.
    """
    if not url or not url.startswith("http"):
        return ""
    text = _scrape_trafilatura(url) or _scrape_bs4(url)
    return text[:max_chars] if text else ""


# ══════════════════════════════════════════════════════════════════════════════
# CONSTRUCCIÓN DEL PROMPT
# ══════════════════════════════════════════════════════════════════════════════

_SYSTEM_PROMPT = """Eres un analista senior de commodities con 20 años de experiencia \
en mercados de acero, energía, fletes y divisas emergentes. Trabajas para TYASA, \
acería mexicana que produce acero plano vía horno eléctrico de arco.

Tu tarea: analizar el movimiento inusual de una variable de mercado y generar \
un resumen ejecutivo conciso en español para el equipo directivo."""

_USER_TEMPLATE = """## Variable: {variable}
- Sigma actual: {sigma:+.2f}σ  (movimiento {sigma_desc})
- Cambio 7 días: {cambio7:+.1f}%
- Valor actual: {valor:.2f}  |  Media histórica base: {media_base:.2f}
- Tendencia: {tendencia}

## Noticias recientes ({n_noticias} artículos):
{noticias_txt}

---
Con base en lo anterior, genera un análisis ejecutivo con EXACTAMENTE este formato JSON \
(sin markdown extra, solo el JSON):

{{
  "puntos_clave": [
    "Punto 1 (máx 25 palabras)",
    "Punto 2 (máx 25 palabras)",
    "Punto 3 (máx 25 palabras)",
    "Punto 4 (máx 25 palabras)",
    "Punto 5 (máx 25 palabras)"
  ],
  "driver_principal": "Oferta | Demanda | Geopolitica | Macro | Sectorial",
  "sentimiento": "Alcista | Bajista | Neutral",
  "confianza": "Alta | Media | Baja",
  "impacto_tyasa": "una oración de máx 30 palabras sobre el impacto directo en TYASA"
}}"""


def _build_prompt(
    variable: str,
    sigma: float,
    cambio7: float,
    valor: float,
    media_base: float,
    tendencia: str,
    noticias: list[dict],
    scrape: bool = False,
) -> str:
    sigma_desc = (
        "EXTREMO — posible crisis"    if abs(sigma) >= 4 else
        "muy alto — alerta crítica"   if abs(sigma) >= 3 else
        "alto — vigilancia activa"    if abs(sigma) >= 2 else
        "moderado"
    )

    lineas = []
    for i, n in enumerate(noticias[:10], 1):
        titulo = (n.get("titulo", "") or "").strip()
        desc   = (n.get("descripcion", "") or "").strip()[:180]
        fecha  = (n.get("fecha_pub", "") or "").strip()
        body   = ""
        if scrape and n.get("url"):
            body = scrape_articulo(n["url"], max_chars=800)

        linea = f"{i}. [{fecha}] {titulo}"
        if desc:
            linea += f"\n   {desc}"
        if body:
            linea += f"\n   [Contenido] {body[:400]}"
        lineas.append(linea)

    noticias_txt = "\n".join(lineas) if lineas else "(Sin noticias disponibles)"

    return _USER_TEMPLATE.format(
        variable    = variable.replace("_", " "),
        sigma       = sigma,
        sigma_desc  = sigma_desc,
        cambio7     = cambio7,
        valor       = valor,
        media_base  = media_base,
        tendencia   = tendencia,
        n_noticias  = len(noticias[:10]),
        noticias_txt = noticias_txt,
    )


# ══════════════════════════════════════════════════════════════════════════════
# LLAMADA A GEMINI API
# ══════════════════════════════════════════════════════════════════════════════

def _call_gemini(prompt: str, api_key: str, model: str = "gemini-2.5-flash") -> dict | None:
    """
    Llama a Gemini via google-genai SDK (nuevo) con fallback a REST directo.
    Retorna dict con los campos del análisis, o None si falla.
    """
    # Intentar con nuevo SDK google-genai
    try:
        from google import genai                          # type: ignore
        from google.genai import types as genai_types    # type: ignore

        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=2048,
                # gemini-2.5-flash tiene "thinking" que consume tokens del budget;
                # deshabilitarlo garantiza que el JSON completo cabe en la respuesta.
                thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = resp.text.strip() if resp.text else ""
        if raw:
            return _parse_json_response(raw)
    except ImportError:
        pass  # SDK no instalado → usar requests
    except Exception as e:
        print(f"[ai_analysis] SDK error: {e}")

    # Fallback: REST directo (no requiere SDK)
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        body = {
            "system_instruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
        }
        resp = requests.post(url, json=body, timeout=30)
        if resp.status_code != 200:
            print(f"[ai_analysis] REST {resp.status_code}: {resp.text[:300]}")
            return None
        data = resp.json()
        raw  = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return _parse_json_response(raw)
    except Exception as e:
        print(f"[ai_analysis] REST error: {e}")
        return None


def _parse_json_response(raw: str) -> dict | None:
    """Extrae JSON del texto crudo del LLM (puede venir dentro de ```json ... ```)."""
    try:
        # Eliminar bloques markdown ```json ... ```
        clean = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip("`").strip()
        # Buscar el primer { ... }
        m = re.search(r"\{.*\}", clean, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        print(f"[ai_analysis] JSON parse error: {e}\nRaw: {raw[:300]}")
    return None


# ══════════════════════════════════════════════════════════════════════════════
# CACHÉ JSON
# ══════════════════════════════════════════════════════════════════════════════

def _cache_key(variable: str, sigma: float) -> str:
    hoy   = date.today().isoformat()
    sigma_r = round(sigma, 1)
    raw   = f"{variable}|{sigma_r}|{hoy}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def _cache_load(key: str) -> dict | None:
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _cache_save(key: str, data: dict) -> None:
    path = CACHE_DIR / f"{key}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ai_analysis] Cache write error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# API PÚBLICA
# ══════════════════════════════════════════════════════════════════════════════

def analizar_alerta(
    variable: str,
    sigma: float,
    cambio7: float,
    valor: float,
    media_base: float,
    tendencia: str,
    noticias: list[dict],
    api_key: str,
    model: str = "gemini-2.5-flash",
    scrape_articles: bool = False,
    force_refresh: bool = False,
) -> dict | None:
    """
    Función principal. Retorna dict con:
      - puntos_clave: list[str]   (5 puntos)
      - driver_principal: str     (Oferta/Demanda/Geopolitica/Macro/Sectorial)
      - sentimiento: str          (Alcista/Bajista/Neutral)
      - confianza: str            (Alta/Media/Baja)
      - impacto_tyasa: str
      - _cached: bool             (True si vino del caché)
      - _error: str | None

    Retorna None si no hay API key.
    """
    if not api_key:
        return None

    ckey   = _cache_key(variable, sigma)
    cached = _cache_load(ckey)
    if cached and not force_refresh:
        cached["_cached"] = True
        return cached

    prompt = _build_prompt(
        variable, sigma, cambio7, valor, media_base, tendencia, noticias,
        scrape=scrape_articles,
    )

    resultado = _call_gemini(prompt, api_key, model=model)

    if resultado:
        resultado["_cached"] = False
        resultado["_error"]  = None
        _cache_save(ckey, resultado)
        return resultado

    return {
        "puntos_clave":     [],
        "driver_principal": "—",
        "sentimiento":      "—",
        "confianza":        "—",
        "impacto_tyasa":    "No se pudo generar el análisis. Verifica la API key y la conexión.",
        "_cached":          False,
        "_error":           "Gemini no respondió o la respuesta no pudo ser parseada.",
    }


# ════════════════════════════════════════════════════════════════════════════
# CHAT / TEXTO LIBRE
# ════════════════════════════════════════════════════════════════════════════

_SYSTEM_CHAT = (
    "Eres un analista senior de commodities y mercados de acero con 20 años de "
    "experiencia. Trabajas para TYASA, acería mexicana con horno eléctrico de arco. "
    "Responde de forma concisa, técnica y en español. Máximo 3 párrafos cortos."
)


def _call_gemini_text(
    prompt: str,
    api_key: str,
    system: str = _SYSTEM_CHAT,
    model: str = "gemini-2.5-flash",
) -> str:
    """Llama a Gemini y retorna texto libre (para chat y síntesis abierta)."""
    try:
        from google import genai                       # type: ignore
        from google.genai import types as genai_types  # type: ignore
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.5,
                max_output_tokens=600,
                thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return (resp.text or "").strip() or "Sin respuesta."
    except Exception as e:
        print(f"[ai_analysis] _call_gemini_text error: {e}")
        return f"Error al consultar la IA: {str(e)[:120]}"


# ════════════════════════════════════════════════════════════════════════════
# SÍNTESIS INDUSTRIAL (Monitor Siderúrgico)
# ════════════════════════════════════════════════════════════════════════════

_SINTESIS_TMPL = """Eres analista senior de la industria siderúrgica para TYASA México (acería EAF).

Con base en las siguientes noticias recientes de la industria, genera una síntesis ejecutiva
en JSON con EXACTAMENTE este formato (sin markdown extra):

{{
  "impacto_precios": "2-3 oraciones sobre movimientos de precios HRC/CRC/insumos/fletes",
  "tendencias_mexico": "2-3 oraciones sobre el mercado mexicano: inversiones, nearshoring, demanda",
  "riesgos_globales": "2-3 oraciones sobre riesgos: sobrecapacidad China, aranceles, demanda global",
  "nivel_alerta": "Alto | Medio | Bajo",
  "recomendacion": "una oración de acción concreta para el equipo comercial de TYASA"
}}

## Noticias recientes ({n} artículos):
{noticias_txt}
"""


def sintesis_industrial(
    noticias_por_grupo: dict[str, list[dict]],
    api_key: str,
    model: str = "gemini-2.5-flash",
    force_refresh: bool = False,
) -> dict | None:
    """
    Síntesis de industria siderúrgica. Caché diario en disco.
    Retorna dict: impacto_precios, tendencias_mexico, riesgos_globales,
                  nivel_alerta, recomendacion, _cached, _error
    """
    hoy  = date.today().isoformat()
    ckey = hashlib.md5(f"industria|{hoy}".encode()).hexdigest()[:16]

    cached = _cache_load(ckey)
    if cached and not force_refresh:
        cached["_cached"] = True
        return cached

    todos: list[str] = []
    for grupo, noticias in noticias_por_grupo.items():
        for n in noticias[:4]:
            titulo = (n.get("titulo", "") or "").strip()
            desc   = (n.get("descripcion", "") or "").strip()[:100]
            fecha  = (n.get("fecha_pub", "") or "")
            todos.append(f"[{grupo}·{fecha}] {titulo}. {desc}")

    noticias_txt = "\n".join(todos[:20]) if todos else "(sin noticias disponibles)"
    prompt = _SINTESIS_TMPL.format(n=len(todos), noticias_txt=noticias_txt)

    resultado = _call_gemini(prompt, api_key, model=model)
    if resultado:
        resultado["_cached"] = False
        resultado["_error"]  = None
        _cache_save(ckey, resultado)
        return resultado

    return {
        "impacto_precios":   "No se pudo generar la síntesis.",
        "tendencias_mexico": "",
        "riesgos_globales":  "",
        "nivel_alerta":      "—",
        "recomendacion":     "",
        "_cached": False,
        "_error":  "Gemini no respondió o la respuesta no pudo ser parseada.",
    }
