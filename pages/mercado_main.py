"""
mercado_main.py — Mercado Global (página principal del sidebar)
Ejecuta el contenido de pages/mercado/00_mercado_global.py
"""
import os, sys

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

_page = os.path.join(os.path.dirname(__file__), "mercado", "00_mercado_global.py")
exec(open(_page, encoding="utf-8").read(), {"__name__": "__main__", "__file__": _page})
