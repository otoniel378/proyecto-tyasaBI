"""
mananera.py — Analiza la conferencia mañanera presidencial para impacto siderúrgico.

Flujo:
  1. Busca en YouTube el video de la conferencia del día (yt-dlp) — en vivo o grabado
  2. Obtiene la transcripción automática en español (youtube-transcript-api)
  3. Filtra y analiza con Gemini: solo información relevante para acero
  4. Caché por fecha en cache/mananera/ (máx 3 días, limpieza automática)
"""
from __future__ import annotations

import json
import re
import datetime
from pathlib import Path

# ── Rutas ─────────────────────────────────────────────────────────────────────
_ROOT_DIR = Path(__file__).resolve().parents[2]
MANANERA_CACHE_DIR = _ROOT_DIR / "cache" / "mananera"
MANANERA_CACHE_DAYS = 3

# ── Meses en español ──────────────────────────────────────────────────────────
_MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

# Palabras clave para identificar el canal oficial
_OFFICIAL_KW = {"presidencia", "gobierno", "sheinbaum", "claudia", "gob.mx"}

# ── System prompt ─────────────────────────────────────────────────────────────
_SYSTEM = (
    "Eres un analista senior de inteligencia de negocios especializado en la "
    "industria siderúrgica en México. Analizas conferencias de prensa presidencial "
    "y extraes únicamente la información que puede impactar a la industria del acero. "
    "Responde siempre con JSON válido, sin bloques de markdown."
)

_PROMPT_TEMPLATE = """\
Analiza la siguiente transcripción de la conferencia mañanera de la presidenta \
Claudia Sheinbaum del {fecha}.

IGNORA completamente: política partidista, seguridad pública, programas sociales \
sin impacto industrial, opiniones sin implicaciones económicas.

EXTRAE SOLO información sobre:
- Regulación: aranceles, comercio exterior, antidumping, T-MEC
- Energía: electricidad, gas, CFE, costos energéticos, proyectos
- Infraestructura: obra pública, construcción, vivienda, trenes, puertos
- Industria: inversión, nearshoring, manufactura, PYMES, parques industriales
- Economía: PIB industrial, inflación, tipo de cambio, crédito productivo

Responde con este JSON exacto (sin markdown):

{{
  "tiene_contenido_relevante": true,
  "resumen_ejecutivo": [
    "Punto clave 1 (máx 25 palabras)",
    "Punto clave 2 (máx 25 palabras)"
  ],
  "analisis_impacto": [
    {{
      "punto": "Descripción del tema en 10-15 palabras",
      "tipo": "Regulación | Energía | Demanda | Riesgo | Oportunidad",
      "impacto": "Alto | Medio | Bajo",
      "direccion": "Positivo | Negativo | Neutral",
      "areas_afectadas": ["SBQ", "Aceros Planos", "Aceros Largos"],
      "explicacion": "2-3 oraciones sobre por qué impacta al sector acero."
    }}
  ],
  "alertas_criticas": [],
  "insight_estrategico": "2-3 oraciones: implicaciones para precios, costos o demanda en México.",
  "recomendacion": "Una oración con acción concreta para empresa siderúrgica mexicana."
}}

Si NO hay contenido relevante responde:
{{"tiene_contenido_relevante": false, "resumen_ejecutivo": [], \
"analisis_impacto": [], "alertas_criticas": [], \
"insight_estrategico": "", "recomendacion": ""}}

TRANSCRIPCIÓN ({chars} caracteres):
{transcripcion}"""


# ── Caché ─────────────────────────────────────────────────────────────────────

def _cleanup_old_cache(days: int = MANANERA_CACHE_DAYS) -> None:
    if not MANANERA_CACHE_DIR.exists():
        return
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    for f in MANANERA_CACHE_DIR.glob("*.json"):
        try:
            if datetime.date.fromisoformat(f.stem) < cutoff:
                f.unlink()
        except (ValueError, OSError):
            pass


def _cache_load(fecha: str) -> dict | None:
    path = MANANERA_CACHE_DIR / f"{fecha}.json"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _cache_save(fecha: str, data: dict) -> None:
    MANANERA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = MANANERA_CACHE_DIR / f"{fecha}.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[mananera] Cache write error: {e}")


# ── YouTube helpers ───────────────────────────────────────────────────────────

def _find_video_id(fecha: str) -> tuple[str | None, str, bool]:
    """
    Busca la mañanera de `fecha` en YouTube con múltiples estrategias.
    Retorna (video_id, error_msg, is_live).
    Prioridades:
      1. Canal oficial + duración >= 45 min
      2. Canal oficial en vivo (live)
      3. Cualquier video >= 45 min
      4. Cualquier live que coincida con la búsqueda
      5. Primer resultado
    """
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        return None, "yt-dlp no instalado — ejecuta: pip install yt-dlp", False

    try:
        dt = datetime.date.fromisoformat(fecha)
        mes = _MESES[dt.month]
        dia = dt.day
        year = dt.year
    except Exception:
        return None, f"Fecha inválida: {fecha}", False

    # Múltiples queries para aumentar probabilidad de encontrar el video
    queries = [
        f"conferencia mañanera Claudia Sheinbaum {dia} {mes} {year}",
        f"mañanera presidencial {dia} {mes} {year}",
        f"conferencia mañanera presidencia Mexico {fecha}",
    ]

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }

    for query in queries:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(f"ytsearch10:{query}", download=False)
                entries = [
                    e for e in (result or {}).get("entries", [])
                    if e and e.get("id")
                ]
                if not entries:
                    continue

                def _is_official(e: dict) -> bool:
                    uploader = (
                        e.get("uploader") or e.get("channel") or
                        e.get("uploader_id") or ""
                    ).lower()
                    return any(kw in uploader for kw in _OFFICIAL_KW)

                def _is_live(e: dict) -> bool:
                    return bool(
                        e.get("is_live") or
                        e.get("live_status") in ("is_live", "is_upcoming")
                    )

                # 1. Canal oficial + >= 45 min
                for e in entries:
                    if _is_official(e) and (e.get("duration") or 0) >= 2700:
                        return e["id"], "", False

                # 2. Canal oficial en vivo
                for e in entries:
                    if _is_official(e) and _is_live(e):
                        return e["id"], "", True

                # 3. Cualquier video >= 45 min
                for e in entries:
                    if (e.get("duration") or 0) >= 2700:
                        return e["id"], "", False

                # 4. Cualquier live
                for e in entries:
                    if _is_live(e):
                        return e["id"], "", True

                # 5. Primer resultado
                return entries[0]["id"], "", False

        except Exception as exc:
            # Continúa con el siguiente query si falla
            last_err = str(exc)[:120]
            continue

    return None, f"No se encontró video de la mañanera para {fecha}.", False


def _get_transcript(video_id: str) -> tuple[str | None, str]:
    """Obtiene la transcripción en español (youtube-transcript-api v1.x)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except ImportError:
        return None, "youtube-transcript-api no instalado — pip install youtube-transcript-api"

    # Intento 1: fetch directo con idiomas preferidos
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["es", "es-MX", "es-419", "es-ES", "es-US"])
        text = " ".join(s.text for s in fetched).strip()
        if text:
            return text, ""
    except Exception:
        pass

    # Intento 2: listar todas y tomar la primera en español
    try:
        api2 = YouTubeTranscriptApi()
        for t in api2.list(video_id):
            if t.language_code.startswith("es"):
                fetched2 = t.fetch()
                text2 = " ".join(s.text for s in fetched2).strip()
                if text2:
                    return text2, ""
        return None, "El video no tiene transcripción en español disponible."
    except Exception as e:
        return None, f"Error al obtener transcripción: {str(e)[:160]}"


# ── Gemini ────────────────────────────────────────────────────────────────────

def _call_gemini(prompt: str, api_key: str) -> dict | None:
    try:
        from google import genai  # type: ignore
        from google.genai import types as T  # type: ignore

        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=T.GenerateContentConfig(
                system_instruction=_SYSTEM,
                temperature=0.2,
                max_output_tokens=3000,
                thinking_config=T.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = (resp.text or "").strip()
        if not raw:
            return None
        clean = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).strip("`").strip()
        m = re.search(r"\{.*\}", clean, re.DOTALL)
        return json.loads(m.group()) if m else None
    except Exception as e:
        print(f"[mananera] Gemini error: {e}")
        return None


# ── API pública ───────────────────────────────────────────────────────────────

def analizar_mananera(
    api_key: str,
    fecha: str | None = None,
    force_refresh: bool = False,
) -> dict:
    """
    Analiza la mañanera de `fecha` (YYYY-MM-DD, default: hoy).
    Soporta videos en vivo (is_live=True) y grabados.

    Retorna dict con:
      tiene_contenido_relevante, resumen_ejecutivo, analisis_impacto,
      alertas_criticas, insight_estrategico, recomendacion,
      _cached, _error (opcional), _video_id (opcional), _is_live, fecha
    """
    if fecha is None:
        fecha = str(datetime.date.today())

    MANANERA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cleanup_old_cache()

    if not force_refresh:
        cached = _cache_load(fecha)
        if cached:
            cached["_cached"] = True
            return cached

    # Paso 1 — buscar video
    video_id, err, is_live = _find_video_id(fecha)
    if not video_id:
        return {
            "tiene_contenido_relevante": False,
            "_error": err,
            "_cached": False,
            "fecha": fecha,
            "_is_live": False,
        }

    # Paso 2 — transcripción
    transcript, err = _get_transcript(video_id)
    if not transcript:
        # Para live sin transcripción: mensaje específico
        if is_live:
            msg = (
                "La conferencia está en vivo o acaba de terminar. "
                "Las transcripciones automáticas de YouTube quedan disponibles "
                "aproximadamente 15-30 minutos después de finalizar la transmisión. "
                "Intenta de nuevo en unos minutos."
            )
        else:
            msg = err or "No se pudo obtener la transcripción del video."
        return {
            "tiene_contenido_relevante": False,
            "_error": msg,
            "_cached": False,
            "fecha": fecha,
            "_video_id": video_id,
            "_is_live": is_live,
        }

    # Paso 3 — Gemini (truncar a 40 000 chars ≈ 1 h de discurso)
    trunc = transcript[:40_000]
    prompt = _PROMPT_TEMPLATE.format(
        fecha=fecha, chars=len(trunc), transcripcion=trunc
    )
    result = _call_gemini(prompt, api_key)

    if result is None:
        return {
            "tiene_contenido_relevante": False,
            "_error": "Gemini no pudo procesar la transcripción.",
            "_cached": False,
            "fecha": fecha,
            "_video_id": video_id,
            "_is_live": is_live,
        }

    result.update({
        "_cached": False,
        "fecha": fecha,
        "_video_id": video_id,
        "_is_live": is_live,
    })
    result.pop("_error", None)
    # No cachear videos en vivo (transcripción puede ser parcial)
    if not is_live:
        _cache_save(fecha, result)
    return result
