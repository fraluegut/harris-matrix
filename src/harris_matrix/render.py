"""Matriz de Harris en SVG editable, sin dependencias."""

from __future__ import annotations

from xml.sax.saxutils import escape, quoteattr

from .model import TEMPORALES, Proyecto, clave_natural
from .verify import encontrar_ciclos, grafo_temporal

ANCHO, ALTO, SEP_X, SEP_Y, MARGEN = 84, 38, 28, 58, 30
DASH = {"segura": "", "probable": "7 4", "dudosa": "2 4"}
FUERZA = {"segura": 3, "probable": 2, "dudosa": 1}

ESTILO = """
.nodo rect { fill: #fff; stroke: #222; stroke-width: 1.5 }
.nodo.interfaz rect { fill: #eef3fb }
.nodo.estructura rect { fill: #f4ede4; stroke-width: 2.5 }
.nodo.virtual rect { stroke-dasharray: 4 3 }
.nodo text { font: 13px sans-serif; fill: #111; text-anchor: middle }
.arista { stroke: #222; stroke-width: 1.5; fill: none }
.error rect { stroke: #c00; stroke-width: 3 }
.arista.error { stroke: #c00 }
""".strip()


def _niveles(nodos, aristas):
    """Nivel = camino más largo desde arriba; las aristas de ciclo se ignoran."""
    ciclos = encontrar_ciclos(aristas)
    rotas = {(c[i], c[i + 1]) for c in ciclos for i in range(len(c) - 1)}
    util = {a: {b for b in aristas[a] if (a, b) not in rotas} for a in nodos}
    nivel: dict[str, int] = {}

    def prof(n: str) -> int:
        if n not in nivel:
            nivel[n] = -1
            nivel[n] = max((prof(p) + 1 for p in nodos if n in util[p]), default=0)
        return nivel[n]

    for n in nodos:
        prof(n)
    return nivel, rotas, {n for c in ciclos for n in c}


def _reducir(aristas):
    """Reducción transitiva: se dibuja solo lo imprescindible."""
    def alcanza(o, d, sin):
        pila, visto = [x for x in aristas[o] if (o, x) != sin], {o}
        while pila:
            n = pila.pop()
            if n == d:
                return True
            if n not in visto:
                visto.add(n)
                pila.extend(aristas[n])
        return False
    return {a: {b for b in bs if not alcanza(a, b, (a, b))} for a, bs in aristas.items()}


def renderizar_svg(proyecto: Proyecto, errores: bool = True) -> str:
    rep, aristas = grafo_temporal(proyecto)
    nodos = sorted(aristas, key=clave_natural)
    nivel, rotas, en_ciclo = _niveles(nodos, aristas)
    reducidas = aristas if rotas else _reducir(aristas)

    grupos = {n: [u for u in proyecto.ues if rep[u.ue_id] == n] for n in nodos}
    etiqueta = {n: " = ".join(sorted((u.ue_id for u in grupos[n]), key=clave_natural)) for n in nodos}
    tipo = {n: grupos[n][0].tipo_unidad for n in nodos}
    ancho = {n: max(ANCHO, 9 * len(etiqueta[n]) + 20) for n in nodos}

    filas: dict[int, list[str]] = {}
    for n in nodos:
        filas.setdefault(nivel[n], []).append(n)
    vecinos = {n: [m for m in nodos if m in reducidas[n] or n in reducidas[m]] for n in nodos}
    pos: dict[str, float] = {}

    def repartir() -> None:
        for fila in filas.values():
            for i, n in enumerate(fila):
                pos[n] = i
    repartir()
    for barrido in range(6):
        for k in sorted(filas, reverse=bool(barrido % 2)):
            def baricentro(n):
                v = [pos[m] for m in vecinos[n] if nivel[m] != k]
                return sum(v) / len(v) if v else pos[n]
            filas[k].sort(key=lambda n: (baricentro(n), clave_natural(n)))
            for i, n in enumerate(filas[k]):
                pos[n] = i

    anchos_fila = {k: sum(ancho[n] for n in f) + SEP_X * (len(f) - 1) for k, f in filas.items()}
    total = max(anchos_fila.values(), default=ANCHO)
    xy: dict[str, tuple[float, float]] = {}
    for k, fila in filas.items():
        x = MARGEN + (total - anchos_fila[k]) / 2
        for n in fila:
            xy[n] = (x + ancho[n] / 2, MARGEN + k * (ALTO + SEP_Y) + ALTO / 2)
            x += ancho[n] + SEP_X

    fuerza: dict[tuple[str, str], int] = {}
    for r in proyecto.relaciones:
        if r.tipo in TEMPORALES and r.ue_origen in rep and r.ue_destino in rep:
            par = (rep[r.ue_origen], rep[r.ue_destino])
            fuerza[par] = max(fuerza.get(par, 0), FUERZA.get(r.certeza, 3))
    nombre = {v: k for k, v in FUERZA.items()}

    w = total + 2 * MARGEN
    h = 2 * MARGEN + (max(filas, default=0) + 1) * ALTO + max(filas, default=0) * SEP_Y
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'width="{w:.0f}" height="{h:.0f}">',
        f"<style>{ESTILO}</style>",
        '<rect width="100%" height="100%" fill="#fff"/>',
        '<g id="aristas">',
    ]
    for a in nodos:
        for b in sorted(reducidas[a], key=clave_natural):
            (x1, y1), (x2, y2) = xy[a], xy[b]
            cert = nombre[fuerza.get((a, b), 3)]
            malo = errores and (a, b) in rotas
            dash = f' stroke-dasharray="{DASH[cert]}"' if DASH[cert] else ""
            out.append(
                f'<line class="arista{" error" if malo else ""}" data-certeza="{cert}" '
                f'x1="{x1:.0f}" y1="{y1 + ALTO / 2:.0f}" x2="{x2:.0f}" y2="{y2 - ALTO / 2:.0f}"{dash}/>'
            )
    out.append("</g>")
    out.append('<g id="ues">')
    for n in nodos:
        x, y = xy[n]
        clases = f"nodo {tipo[n]}" + (" error" if errores and n in en_ciclo else "")
        ident = "ue-" + "-".join(u.ue_id.replace(" ", "_") for u in grupos[n])
        titulo = "; ".join(f"{u.ue_id}: {u.descripcion}" for u in grupos[n] if u.descripcion)
        out.append(
            f'<g id={quoteattr(ident)} class="{clases}" data-tipo="{tipo[n]}">'
            f"<title>{escape(titulo)}</title>"
            f'<rect x="{x - ancho[n] / 2:.0f}" y="{y - ALTO / 2:.0f}" width="{ancho[n]}" height="{ALTO}" '
            f'rx="{ALTO / 2 if tipo[n] == "interfaz" else 3:.0f}"/>'
            f'<text x="{x:.0f}" y="{y + 5:.0f}">{escape(etiqueta[n])}</text></g>'
        )
    out += ["</g>", "</svg>"]
    return "\n".join(out) + "\n"
