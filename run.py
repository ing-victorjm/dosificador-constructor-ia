"""Arranque de METRA AI.

    python run.py              → http://127.0.0.1:8770
    python run.py --demo       → recrea el proyecto de demostración
    python run.py --puerto 9000
"""
from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    analizador = argparse.ArgumentParser(description="METRA AI")
    analizador.add_argument("--puerto", type=int, default=int(os.environ.get("PORT", 8770)))
    analizador.add_argument("--host", default="127.0.0.1")
    analizador.add_argument("--demo", action="store_true",
                            help="Borra y vuelve a crear el proyecto de demostración")
    analizador.add_argument("--sin-navegador", action="store_true")
    analizador.add_argument("--recargar", action="store_true",
                            help="Recarga automática al cambiar el código (desarrollo)")
    args = analizador.parse_args()

    from backend.db import crear_tablas
    crear_tablas()

    from backend.semillas import sembrar
    resumen = sembrar()
    print(f"  Catálogo normativo: {resumen['partidas_catalogo']} partidas")

    from backend import demo
    if args.demo:
        demo.rehacer()
        print("  Proyecto de demostración recreado.")
    else:
        demo.asegurar()

    url = f"http://{args.host}:{args.puerto}"
    print(f"\n  METRA AI en {url}")
    print(f"  Documentación de la API en {url}/api/docs\n")

    if not args.sin_navegador:
        webbrowser.open(url)

    import uvicorn
    uvicorn.run("backend.main:app", host=args.host, port=args.puerto,
                reload=args.recargar, log_level="info")


if __name__ == "__main__":
    main()
