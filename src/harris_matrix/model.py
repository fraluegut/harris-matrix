"""Modelo de datos y lectura de proyectos desde CSV."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

TIPOS_UNIDAD = ("deposito", "interfaz", "estructura", "virtual")
CERTEZAS = ("segura", "probable", "dudosa")

# tipo -> (inversa, origen admitido, destino admitido); None = cualquiera
RELACIONES: dict[str, tuple[str, frozenset | None, frozenset | None]] = {
    "cubre": ("cubierto_por", frozenset({"deposito", "estructura"}), None),
    "corta": ("cortado_por", frozenset({"interfaz"}), None),
    "rellena": ("relleno_por", frozenset({"deposito"}), frozenset({"interfaz"})),
    "se_apoya_en": ("soporta", frozenset({"deposito", "estructura"}), None),
    "se_une_a": ("se_une_a", frozenset({"estructura"}), frozenset({"estructura"})),
    "igual_a": ("igual_a", None, None),
    "posterior_a": ("anterior_a", None, None),
}
INVERSAS = {inv: tipo for tipo, (inv, _, _) in RELACIONES.items() if inv != tipo}
# Relaciones que fijan un orden temporal: origen posterior a destino.
TEMPORALES = frozenset({"cubre", "corta", "rellena", "se_apoya_en", "posterior_a"})


class ProyectoError(Exception):
    """Fichero ausente o con columnas obligatorias que faltan."""


@dataclass
class UE:
    ue_id: str
    tipo_unidad: str
    descripcion: str = ""
    subtipo: str = ""
    fila: int = 0


@dataclass
class Relacion:
    ue_origen: str
    tipo: str
    ue_destino: str
    certeza: str = "segura"
    rel_id: str = ""
    fila: int = 0


@dataclass
class Proyecto:
    ues: list[UE] = field(default_factory=list)
    relaciones: list[Relacion] = field(default_factory=list)

    def ue(self, ue_id: str) -> UE | None:
        return next((u for u in self.ues if u.ue_id == ue_id), None)


def clave_natural(texto: str) -> list:
    """Orden natural: '2' < '10' < '10b'."""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", texto) if t]


def _leer(ruta: Path, obligatorias: tuple[str, ...]) -> list[tuple[int, dict]]:
    if not ruta.is_file():
        raise ProyectoError(f"No existe {ruta}")
    with ruta.open(newline="", encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        faltan = [c for c in obligatorias if c not in (lector.fieldnames or [])]
        if faltan:
            raise ProyectoError(f"{ruta.name}: faltan columnas {', '.join(faltan)}")
        return [
            (n, {k: (v or "").strip() for k, v in fila.items() if k})
            for n, fila in enumerate(lector, start=2)
        ]


def cargar_proyecto(carpeta: str | Path) -> Proyecto:
    """Lee `ues.csv` y `relaciones.csv` de una carpeta de proyecto."""
    base = Path(carpeta)
    proyecto = Proyecto()
    for n, f in _leer(base / "ues.csv", ("ue_id", "tipo_unidad")):
        proyecto.ues.append(
            UE(f["ue_id"], f["tipo_unidad"], f.get("descripcion", ""), f.get("subtipo", ""), n)
        )
    for n, f in _leer(base / "relaciones.csv", ("ue_origen", "tipo", "ue_destino")):
        origen, tipo, destino = f["ue_origen"], f["tipo"], f["ue_destino"]
        if tipo in INVERSAS:  # se normaliza a la forma directa
            origen, tipo, destino = destino, INVERSAS[tipo], origen
        proyecto.relaciones.append(
            Relacion(origen, tipo, destino, f.get("certeza") or "segura", f.get("rel_id", ""), n)
        )
    return proyecto
