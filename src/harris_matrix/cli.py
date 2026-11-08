"""Línea de órdenes: `harris-matrix verify|render CARPETA`."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .model import ProyectoError, cargar_proyecto
from .render import renderizar_svg
from .verify import informe_json, informe_texto, verificar


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="harris-matrix")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--lang", choices=("es", "en"), default="es", help="language / idioma")
    sub = p.add_subparsers(dest="orden", required=True)
    v = sub.add_parser("verify", help="check consistency / verificar coherencia")
    v.add_argument("carpeta")
    v.add_argument("--json", action="store_true")
    r = sub.add_parser("render", help="write the matrix as SVG / dibujar la matriz")
    r.add_argument("carpeta")
    r.add_argument("-o", "--salida", default="-")
    r.add_argument("--sin-errores", action="store_true", help="do not highlight cycles")
    a = p.parse_args(argv)

    try:
        proyecto = cargar_proyecto(a.carpeta)
    except ProyectoError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if a.orden == "verify":
        inc = verificar(proyecto, a.lang)
        print(informe_json(inc) if a.json else informe_texto(inc, a.lang))
        return 1 if any(i.severidad == "error" for i in inc) else 0
    svg = renderizar_svg(proyecto, errores=not a.sin_errores)
    if a.salida == "-":
        sys.stdout.write(svg)
    else:
        with open(a.salida, "w", encoding="utf-8") as f:
            f.write(svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
