"""Verificación de coherencia del registro estratigráfico (reglas R01-R16)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from .model import (
    CERTEZAS, RELACIONES, TEMPORALES, TIPOS_UNIDAD, Proyecto, clave_natural,
)

IDIOMAS = ("es", "en")

# código -> (severidad, {idioma: plantilla})
REGLAS: dict[str, tuple[str, dict[str, str]]] = {
    "R01": ("error", {"es": "UE {ue} duplicada (también en la fila {otra})",
                      "en": "Duplicate SU {ue} (also on row {otra})"}),
    "R02": ("error", {"es": "La relación cita la UE inexistente {ue}",
                      "en": "Relation refers to missing SU {ue}"}),
    "R03": ("error", {"es": "Tipo de relación desconocido: «{tipo}»",
                      "en": "Unknown relation type: '{tipo}'"}),
    "R04": ("error", {"es": "{o} {tipo} {d}: no admitido entre «{to}» y «{td}»",
                      "en": "{o} {tipo} {d}: not allowed between '{to}' and '{td}'"}),
    "R05": ("error", {"es": "La UE {ue} está relacionada consigo misma",
                      "en": "SU {ue} is related to itself"}),
    "R06": ("error", {"es": "Valor no válido en «{campo}»: «{valor}»",
                      "en": "Invalid value in '{campo}': '{valor}'"}),
    "R10": ("error", {"es": "Ciclo en la secuencia: {camino}",
                      "en": "Cycle in the sequence: {camino}"}),
    "R11": ("error", {"es": "Contradicción directa entre {a} y {b}",
                      "en": "Direct contradiction between {a} and {b}"}),
    "R12": ("error", {"es": "{o} {tipo} {d}: ambas UE son la misma por «igual_a»",
                      "en": "{o} {tipo} {d}: both SU are the same via 'igual_a'"}),
    "R13": ("aviso", {"es": "«igual_a» entre tipos distintos: {o} ({to}) y {d} ({td})",
                      "en": "'igual_a' between different types: {o} ({to}) and {d} ({td})"}),
    "R14": ("aviso", {"es": "El corte {ue} no tiene relleno registrado",
                      "en": "Cut {ue} has no recorded fill"}),
    "R14b": ("aviso", {"es": "La interfaz {ue} tiene relleno pero no corta nada",
                       "en": "Interface {ue} has a fill but cuts nothing"}),
    "R15": ("aviso", {"es": "La UE {ue} no tiene ninguna relación",
                      "en": "SU {ue} has no relations"}),
    "R16": ("info", {"es": "{o} → {d} es redundante: ya se deduce por {via}",
                     "en": "{o} → {d} is redundant: already implied via {via}"}),
}


@dataclass
class Incidencia:
    codigo: str
    severidad: str
    mensaje: str
    fila: int | None = None
    archivo: str = ""


def grafo_temporal(proyecto: Proyecto) -> tuple[dict[str, str], dict[str, set[str]]]:
    """Devuelve (representante de cada UE tras fusionar `igual_a`, aristas posterior→anterior)."""
    padre = {u.ue_id: u.ue_id for u in proyecto.ues}

    def raiz(x: str) -> str:
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for r in proyecto.relaciones:
        if r.tipo == "igual_a" and r.ue_origen in padre and r.ue_destino in padre:
            a, b = sorted((raiz(r.ue_origen), raiz(r.ue_destino)), key=clave_natural)
            padre[b] = a
    rep = {u: raiz(u) for u in padre}
    aristas: dict[str, set[str]] = {v: set() for v in set(rep.values())}
    for r in proyecto.relaciones:
        if r.tipo in TEMPORALES and r.ue_origen in rep and r.ue_destino in rep:
            a, b = rep[r.ue_origen], rep[r.ue_destino]
            if a != b:
                aristas[a].add(b)
    return rep, aristas


def encontrar_ciclos(aristas: dict[str, set[str]]) -> list[list[str]]:
    """Un camino cerrado por cada arista de retroceso del DFS."""
    estado: dict[str, int] = {}
    ciclos: list[list[str]] = []
    for inicio in sorted(aristas, key=clave_natural):
        if estado.get(inicio):
            continue
        pila = [(inicio, iter(sorted(aristas[inicio], key=clave_natural)))]
        camino = [inicio]
        estado[inicio] = 1
        while pila:
            nodo, it = pila[-1]
            for sig in it:
                if estado.get(sig) == 1:
                    ciclos.append(camino[camino.index(sig):] + [sig])
                elif not estado.get(sig):
                    estado[sig] = 1
                    camino.append(sig)
                    pila.append((sig, iter(sorted(aristas[sig], key=clave_natural))))
                    break
            else:
                estado[nodo] = 2
                camino.pop()
                pila.pop()
    return ciclos


def _alcanzable(aristas: dict[str, set[str]], origen: str, destino: str, sin: tuple[str, str]):
    """Camino origen→destino sin usar la arista `sin`; devuelve el primer salto o None."""
    for primero in sorted(aristas[origen], key=clave_natural):
        if (origen, primero) == sin:
            continue
        visto, pila = {origen}, [primero]
        while pila:
            n = pila.pop()
            if n == destino:
                return primero
            if n not in visto:
                visto.add(n)
                pila.extend(aristas.get(n, ()))
    return None


def verificar(proyecto: Proyecto, idioma: str = "es") -> list[Incidencia]:
    if idioma not in IDIOMAS:
        raise ValueError(f"idioma no soportado: {idioma}")
    out: list[Incidencia] = []

    def avisar(codigo: str, fila: int | None, archivo: str, **kw) -> None:
        sev, plantillas = REGLAS[codigo]
        out.append(Incidencia(codigo.rstrip("b"), sev, plantillas[idioma].format(**kw), fila, archivo))

    tipo_de: dict[str, str] = {}
    fila_de: dict[str, int] = {}
    for u in proyecto.ues:
        if u.ue_id in tipo_de:
            avisar("R01", u.fila, "ues.csv", ue=u.ue_id, otra=fila_de[u.ue_id])
            continue
        tipo_de[u.ue_id], fila_de[u.ue_id] = u.tipo_unidad, u.fila
        if u.tipo_unidad not in TIPOS_UNIDAD:
            avisar("R06", u.fila, "ues.csv", campo="tipo_unidad", valor=u.tipo_unidad)

    validas = []
    for r in proyecto.relaciones:
        f = "relaciones.csv"
        if r.certeza not in CERTEZAS:
            avisar("R06", r.fila, f, campo="certeza", valor=r.certeza)
        if r.tipo not in RELACIONES:
            avisar("R03", r.fila, f, tipo=r.tipo)
            continue
        ok = True
        for ue in (r.ue_origen, r.ue_destino):
            if ue not in tipo_de:
                avisar("R02", r.fila, f, ue=ue)
                ok = False
        if not ok:
            continue
        if r.ue_origen == r.ue_destino:
            avisar("R05", r.fila, f, ue=r.ue_origen)
            continue
        _, perm_o, perm_d = RELACIONES[r.tipo]
        to, td = tipo_de[r.ue_origen], tipo_de[r.ue_destino]
        if (perm_o and to not in perm_o) or (perm_d and td not in perm_d):
            avisar("R04", r.fila, f, o=r.ue_origen, tipo=r.tipo, d=r.ue_destino, to=to, td=td)
            continue
        if r.tipo == "igual_a" and to != td:
            avisar("R13", r.fila, f, o=r.ue_origen, d=r.ue_destino, to=to, td=td)
        validas.append(r)

    rep, aristas = grafo_temporal(Proyecto(proyecto.ues, validas))
    for r in validas:
        if r.tipo in TEMPORALES and rep[r.ue_origen] == rep[r.ue_destino]:
            avisar("R12", r.fila, "relaciones.csv", o=r.ue_origen, tipo=r.tipo, d=r.ue_destino)

    for c in encontrar_ciclos(aristas):
        if len(c) == 3 and c[0] == c[2]:
            avisar("R11", None, "relaciones.csv", a=c[0], b=c[1])
        else:
            avisar("R10", None, "relaciones.csv", camino=" → ".join(c))

    con_relacion = {x for r in validas for x in (r.ue_origen, r.ue_destino)}
    for u in proyecto.ues:
        if u.ue_id in tipo_de and u.ue_id not in con_relacion:
            avisar("R15", u.fila, "ues.csv", ue=u.ue_id)

    cortan = {r.ue_origen for r in validas if r.tipo == "corta"}
    rellenadas = {r.ue_destino for r in validas if r.tipo == "rellena"}
    cortadas_por = {r.ue_destino for r in validas if r.tipo == "corta"}
    for u in proyecto.ues:
        if tipo_de.get(u.ue_id) != "interfaz" or u.ue_id not in tipo_de:
            continue
        if u.ue_id in cortan and u.ue_id not in rellenadas:
            avisar("R14", u.fila, "ues.csv", ue=u.ue_id)
        elif u.ue_id in rellenadas and u.ue_id not in cortan:
            avisar("R14b", u.fila, "ues.csv", ue=u.ue_id)
    del cortadas_por

    if not any(i.codigo in ("R10", "R11") for i in out):
        for a in sorted(aristas, key=clave_natural):
            for b in sorted(aristas[a], key=clave_natural):
                via = _alcanzable(aristas, a, b, (a, b))
                if via:
                    avisar("R16", None, "relaciones.csv", o=a, d=b, via=via)

    orden = {"error": 0, "aviso": 1, "info": 2}
    return sorted(out, key=lambda i: (orden[i.severidad], i.codigo, i.archivo, i.fila or 0))


def informe_texto(incidencias: list[Incidencia], idioma: str = "es") -> str:
    etiquetas = {"es": ("error", "aviso", "info"), "en": ("error", "warning", "info")}[idioma]
    nombre = dict(zip(("error", "aviso", "info"), etiquetas))
    lineas = []
    for i in incidencias:
        donde = f"{i.archivo}:{i.fila}" if i.fila else i.archivo
        lineas.append(f"{nombre[i.severidad]:<7} {i.codigo}  {donde:<20} {i.mensaje}")
    n = {s: sum(i.severidad == s for i in incidencias) for s in ("error", "aviso", "info")}
    resumen = {
        "es": f"{n['error']} errores, {n['aviso']} avisos, {n['info']} informaciones",
        "en": f"{n['error']} errors, {n['aviso']} warnings, {n['info']} notes",
    }[idioma]
    return "\n".join(lineas + [resumen])


def informe_json(incidencias: list[Incidencia]) -> str:
    return json.dumps([asdict(i) for i in incidencias], ensure_ascii=False, indent=2)
