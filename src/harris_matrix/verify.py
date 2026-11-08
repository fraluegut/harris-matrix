"""Consistency checks on the stratigraphic record (rules R01-R16)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from .model import (
    CERTAINTIES, RELATIONS, TEMPORAL, UNIT_TYPES, Project, natural_key,
)

# code -> (severity, message template)
RULES: dict[str, tuple[str, str]] = {
    "R01": ("error", "Duplicate unit {unit} (also on row {other})"),
    "R02": ("error", "Relation refers to missing unit {unit}"),
    "R03": ("error", "Unknown relation type: '{kind}'"),
    "R04": ("error", "{a} {kind} {b}: not allowed between '{ta}' and '{tb}'"),
    "R05": ("error", "Unit {unit} is related to itself"),
    "R06": ("error", "Invalid value in '{column}': '{value}'"),
    "R10": ("error", "Cycle in the sequence: {path}"),
    "R11": ("error", "Direct contradiction between {a} and {b}"),
    "R12": ("error", "{a} {kind} {b}: both units are the same via 'same_as'"),
    "R13": ("warning", "'same_as' between different types: {a} ({ta}) and {b} ({tb})"),
    "R14": ("warning", "Cut {unit} has no recorded fill"),
    "R14b": ("warning", "Interface {unit} has a fill but cuts nothing"),
    "R15": ("warning", "Unit {unit} has no relations"),
    "R16": ("info", "{a} -> {b} is redundant: already implied via {via}"),
}


@dataclass
class Issue:
    code: str
    severity: str
    message: str
    row: int | None = None
    file: str = ""


def temporal_graph(project: Project) -> tuple[dict[str, str], dict[str, set[str]]]:
    """Return (representative of each unit after merging `same_as`, edges later -> earlier)."""
    parent = {u.unit_id: u.unit_id for u in project.units}

    def root(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in project.relations:
        if r.type == "same_as" and r.from_unit in parent and r.to_unit in parent:
            a, b = sorted((root(r.from_unit), root(r.to_unit)), key=natural_key)
            parent[b] = a
    rep = {u: root(u) for u in parent}
    edges: dict[str, set[str]] = {v: set() for v in set(rep.values())}
    for r in project.relations:
        if r.type in TEMPORAL and r.from_unit in rep and r.to_unit in rep:
            a, b = rep[r.from_unit], rep[r.to_unit]
            if a != b:
                edges[a].add(b)
    return rep, edges


def find_cycles(edges: dict[str, set[str]]) -> list[list[str]]:
    """One closed path per back edge found by an iterative DFS."""
    state: dict[str, int] = {}  # 1 = on the stack, 2 = done
    cycles: list[list[str]] = []
    for start in sorted(edges, key=natural_key):
        if state.get(start):
            continue
        stack = [(start, iter(sorted(edges[start], key=natural_key)))]
        path = [start]
        state[start] = 1
        while stack:
            node, it = stack[-1]
            for nxt in it:
                if state.get(nxt) == 1:
                    cycles.append(path[path.index(nxt):] + [nxt])
                elif not state.get(nxt):
                    state[nxt] = 1
                    path.append(nxt)
                    stack.append((nxt, iter(sorted(edges[nxt], key=natural_key))))
                    break
            else:
                state[node] = 2
                path.pop()
                stack.pop()
    return cycles


def _alternative_path(edges: dict[str, set[str]], origin: str, target: str, skip: tuple[str, str]):
    """First hop of a path origin -> target that avoids the edge `skip`, or None."""
    for first in sorted(edges[origin], key=natural_key):
        if (origin, first) == skip:
            continue
        seen, stack = {origin}, [first]
        while stack:
            n = stack.pop()
            if n == target:
                return first
            if n not in seen:
                seen.add(n)
                stack.extend(edges.get(n, ()))
    return None


def verify(project: Project) -> list[Issue]:
    """Run all checks and return the issues, errors first."""
    out: list[Issue] = []

    def report(code: str, row: int | None, file: str, **kw) -> None:
        severity, template = RULES[code]
        out.append(Issue(code.rstrip("b"), severity, template.format(**kw), row, file))

    type_of: dict[str, str] = {}
    row_of: dict[str, int] = {}
    for u in project.units:
        if u.unit_id in type_of:
            report("R01", u.row, "units.csv", unit=u.unit_id, other=row_of[u.unit_id])
            continue
        type_of[u.unit_id], row_of[u.unit_id] = u.unit_type, u.row
        if u.unit_type not in UNIT_TYPES:
            report("R06", u.row, "units.csv", column="unit_type", value=u.unit_type)

    valid = []
    for r in project.relations:
        f = "relations.csv"
        if r.certainty not in CERTAINTIES:
            report("R06", r.row, f, column="certainty", value=r.certainty)
        if r.type not in RELATIONS:
            report("R03", r.row, f, kind=r.type)
            continue
        known = True
        for unit in (r.from_unit, r.to_unit):
            if unit not in type_of:
                report("R02", r.row, f, unit=unit)
                known = False
        if not known:
            continue
        if r.from_unit == r.to_unit:
            report("R05", r.row, f, unit=r.from_unit)
            continue
        _, allowed_from, allowed_to = RELATIONS[r.type]
        ta, tb = type_of[r.from_unit], type_of[r.to_unit]
        if (allowed_from and ta not in allowed_from) or (allowed_to and tb not in allowed_to):
            report("R04", r.row, f, a=r.from_unit, kind=r.type, b=r.to_unit, ta=ta, tb=tb)
            continue
        if r.type == "same_as" and ta != tb:
            report("R13", r.row, f, a=r.from_unit, b=r.to_unit, ta=ta, tb=tb)
        valid.append(r)

    rep, edges = temporal_graph(Project(project.units, valid))
    for r in valid:
        if r.type in TEMPORAL and rep[r.from_unit] == rep[r.to_unit]:
            report("R12", r.row, "relations.csv", a=r.from_unit, kind=r.type, b=r.to_unit)

    for cycle in find_cycles(edges):
        if len(cycle) == 3 and cycle[0] == cycle[2]:
            report("R11", None, "relations.csv", a=cycle[0], b=cycle[1])
        else:
            report("R10", None, "relations.csv", path=" -> ".join(cycle))

    related = {x for r in valid for x in (r.from_unit, r.to_unit)}
    for u in project.units:
        if u.unit_id in type_of and u.unit_id not in related:
            report("R15", u.row, "units.csv", unit=u.unit_id)

    cutters = {r.from_unit for r in valid if r.type == "cuts"}
    filled = {r.to_unit for r in valid if r.type == "fills"}
    for u in project.units:
        if u.unit_id not in type_of or type_of[u.unit_id] != "interface":
            continue
        if u.unit_id in cutters and u.unit_id not in filled:
            report("R14", u.row, "units.csv", unit=u.unit_id)
        elif u.unit_id in filled and u.unit_id not in cutters:
            report("R14b", u.row, "units.csv", unit=u.unit_id)

    if not any(i.code in ("R10", "R11") for i in out):
        for a in sorted(edges, key=natural_key):
            for b in sorted(edges[a], key=natural_key):
                via = _alternative_path(edges, a, b, (a, b))
                if via:
                    report("R16", None, "relations.csv", a=a, b=b, via=via)

    order = {"error": 0, "warning": 1, "info": 2}
    return sorted(out, key=lambda i: (order[i.severity], i.code, i.file, i.row or 0))


def report_text(issues: list[Issue]) -> str:
    lines = []
    for i in issues:
        where = f"{i.file}:{i.row}" if i.row else i.file
        lines.append(f"{i.severity:<7} {i.code}  {where:<20} {i.message}")
    n = {s: sum(i.severity == s for i in issues) for s in ("error", "warning", "info")}
    lines.append(f"{n['error']} errors, {n['warning']} warnings, {n['info']} notes")
    return "\n".join(lines)


def report_json(issues: list[Issue]) -> str:
    return json.dumps([asdict(i) for i in issues], indent=2)
