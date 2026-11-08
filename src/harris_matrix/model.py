"""Data model and CSV project loading."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

UNIT_TYPES = ("deposit", "interface", "structure", "virtual")
CERTAINTIES = ("certain", "probable", "doubtful")

# type -> (inverse, allowed origin unit types, allowed destination unit types); None = any
RELATIONS: dict[str, tuple[str, frozenset | None, frozenset | None]] = {
    "covers": ("covered_by", frozenset({"deposit", "structure"}), None),
    "cuts": ("cut_by", frozenset({"interface"}), None),
    "fills": ("filled_by", frozenset({"deposit"}), frozenset({"interface"})),
    "rests_on": ("supports", frozenset({"deposit", "structure"}), None),
    "bonded_to": ("bonded_to", frozenset({"structure"}), frozenset({"structure"})),
    "same_as": ("same_as", None, None),
    "later_than": ("earlier_than", None, None),
}
INVERSES = {inv: name for name, (inv, _, _) in RELATIONS.items() if inv != name}
# Relations that fix a temporal order: the origin is later than the destination.
TEMPORAL = frozenset({"covers", "cuts", "fills", "rests_on", "later_than"})


class ProjectError(Exception):
    """A file is missing or lacks required columns."""


@dataclass
class Unit:
    unit_id: str
    unit_type: str
    description: str = ""
    subtype: str = ""
    row: int = 0
    # Every column of the CSV row (including custom ones such as `period`),
    # so any of them can be shown in the matrix.
    attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class Relation:
    from_unit: str
    type: str
    to_unit: str
    certainty: str = "certain"
    rel_id: str = ""
    row: int = 0


@dataclass
class Project:
    units: list[Unit] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)


def natural_key(text: str) -> list:
    """Natural sort key: '2' < '10' < '10b' (numbers before text, never a type clash)."""
    return [(0, int(t), "") if t.isdigit() else (1, 0, t) for t in re.split(r"(\d+)", text) if t]


def _read(path: Path, required: tuple[str, ...]) -> list[tuple[int, dict]]:
    if not path.is_file():
        raise ProjectError(f"{path} does not exist")
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            raise ProjectError(f"{path.name}: missing columns {', '.join(missing)}")
        return [
            (n, {k: (v or "").strip() for k, v in row.items() if k})
            for n, row in enumerate(reader, start=2)
        ]


def load_project(folder: str | Path) -> Project:
    """Read `units.csv` and `relations.csv` from a project folder."""
    base = Path(folder)
    project = Project()
    for n, r in _read(base / "units.csv", ("unit_id", "unit_type")):
        project.units.append(
            Unit(r["unit_id"], r["unit_type"], r.get("description", ""), r.get("subtype", ""), n, dict(r))
        )
    for n, r in _read(base / "relations.csv", ("from_unit", "type", "to_unit")):
        origin, kind, target = r["from_unit"], r["type"], r["to_unit"]
        if kind in INVERSES:  # normalise to the direct form
            origin, kind, target = target, INVERSES[kind], origin
        project.relations.append(
            Relation(origin, kind, target, r.get("certainty") or "certain", r.get("rel_id", ""), n)
        )
    return project
