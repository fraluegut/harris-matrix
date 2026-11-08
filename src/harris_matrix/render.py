"""Harris matrix as editable SVG, with no dependencies."""

from __future__ import annotations

from xml.sax.saxutils import escape, quoteattr

from .model import TEMPORAL, Project, natural_key
from .verify import find_cycles, temporal_graph

WIDTH, HEIGHT, GAP_X, GAP_Y, MARGIN = 84, 38, 28, 58, 30
DASH = {"certain": "", "probable": "7 4", "doubtful": "2 4"}
STRENGTH = {"certain": 3, "probable": 2, "doubtful": 1}

STYLE = """
.node rect { fill: #fff; stroke: #222; stroke-width: 1.5 }
.node.interface rect { fill: #eef3fb }
.node.structure rect { fill: #f4ede4; stroke-width: 2.5 }
.node.virtual rect { stroke-dasharray: 4 3 }
.node text { font: 13px sans-serif; fill: #111; text-anchor: middle }
.edge { stroke: #222; stroke-width: 1.5; fill: none }
.error rect { stroke: #c00; stroke-width: 3 }
.edge.error { stroke: #c00 }
""".strip()


def _levels(nodes, edges):
    """Level = longest path from the top; cycle edges are ignored."""
    cycles = find_cycles(edges)
    broken = {(c[i], c[i + 1]) for c in cycles for i in range(len(c) - 1)}
    usable = {a: {b for b in edges[a] if (a, b) not in broken} for a in nodes}
    level: dict[str, int] = {}

    def depth(n: str) -> int:
        if n not in level:
            level[n] = -1
            level[n] = max((depth(p) + 1 for p in nodes if n in usable[p]), default=0)
        return level[n]

    for n in nodes:
        depth(n)
    return level, broken, {n for c in cycles for n in c}


def _reduce(edges):
    """Transitive reduction: draw only the edges that are not implied by others."""
    def reaches(origin, target, skip):
        stack, seen = [x for x in edges[origin] if (origin, x) != skip], {origin}
        while stack:
            n = stack.pop()
            if n == target:
                return True
            if n not in seen:
                seen.add(n)
                stack.extend(edges[n])
        return False
    return {a: {b for b in bs if not reaches(a, b, (a, b))} for a, bs in edges.items()}


def render_svg(project: Project, highlight_errors: bool = True) -> str:
    """Return the Harris matrix as an SVG document (later units on top)."""
    rep, edges = temporal_graph(project)
    nodes = sorted(edges, key=natural_key)
    level, broken, in_cycle = _levels(nodes, edges)
    drawn = edges if broken else _reduce(edges)

    members = {n: [u for u in project.units if rep[u.unit_id] == n] for n in nodes}
    label = {n: " = ".join(sorted((u.unit_id for u in members[n]), key=natural_key)) for n in nodes}
    kind = {n: members[n][0].unit_type for n in nodes}
    width = {n: max(WIDTH, 9 * len(label[n]) + 20) for n in nodes}

    rows: dict[int, list[str]] = {}
    for n in nodes:
        rows.setdefault(level[n], []).append(n)
    neighbours = {n: [m for m in nodes if m in drawn[n] or n in drawn[m]] for n in nodes}
    order: dict[str, float] = {}
    for row in rows.values():
        for i, n in enumerate(row):
            order[n] = i
    # Barycentre sweeps, alternating direction, to reduce crossings.
    for sweep in range(6):
        for k in sorted(rows, reverse=bool(sweep % 2)):
            def barycentre(n):
                v = [order[m] for m in neighbours[n] if level[m] != k]
                return sum(v) / len(v) if v else order[n]
            rows[k].sort(key=lambda n: (barycentre(n), natural_key(n)))
            for i, n in enumerate(rows[k]):
                order[n] = i

    row_width = {k: sum(width[n] for n in r) + GAP_X * (len(r) - 1) for k, r in rows.items()}
    total = max(row_width.values(), default=WIDTH)
    xy: dict[str, tuple[float, float]] = {}
    for k, row in rows.items():
        x = MARGIN + (total - row_width[k]) / 2
        for n in row:
            xy[n] = (x + width[n] / 2, MARGIN + k * (HEIGHT + GAP_Y) + HEIGHT / 2)
            x += width[n] + GAP_X

    strength: dict[tuple[str, str], int] = {}
    for r in project.relations:
        if r.type in TEMPORAL and r.from_unit in rep and r.to_unit in rep:
            pair = (rep[r.from_unit], rep[r.to_unit])
            strength[pair] = max(strength.get(pair, 0), STRENGTH.get(r.certainty, 3))
    name = {v: k for k, v in STRENGTH.items()}

    last = max(rows, default=0)
    w = total + 2 * MARGIN
    h = 2 * MARGIN + (last + 1) * HEIGHT + last * GAP_Y
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'width="{w:.0f}" height="{h:.0f}">',
        f"<style>{STYLE}</style>",
        '<rect width="100%" height="100%" fill="#fff"/>',
        '<g id="edges">',
    ]
    for a in nodes:
        for b in sorted(drawn[a], key=natural_key):
            (x1, y1), (x2, y2) = xy[a], xy[b]
            certainty = name[strength.get((a, b), 3)]
            bad = highlight_errors and (a, b) in broken
            dash = f' stroke-dasharray="{DASH[certainty]}"' if DASH[certainty] else ""
            out.append(
                f'<line class="edge{" error" if bad else ""}" data-certainty="{certainty}" '
                f'x1="{x1:.0f}" y1="{y1 + HEIGHT / 2:.0f}" x2="{x2:.0f}" y2="{y2 - HEIGHT / 2:.0f}"{dash}/>'
            )
    out.append("</g>")
    out.append('<g id="units">')
    for n in nodes:
        x, y = xy[n]
        classes = f"node {kind[n]}" + (" error" if highlight_errors and n in in_cycle else "")
        ident = "unit-" + "-".join(u.unit_id.replace(" ", "_") for u in members[n])
        title = "; ".join(f"{u.unit_id}: {u.description}" for u in members[n] if u.description)
        out.append(
            f'<g id={quoteattr(ident)} class="{classes}" data-type="{kind[n]}">'
            f"<title>{escape(title)}</title>"
            f'<rect x="{x - width[n] / 2:.0f}" y="{y - HEIGHT / 2:.0f}" width="{width[n]}" height="{HEIGHT}" '
            f'rx="{HEIGHT / 2 if kind[n] == "interface" else 3:.0f}"/>'
            f'<text x="{x:.0f}" y="{y + 5:.0f}">{escape(label[n])}</text></g>'
        )
    out += ["</g>", "</svg>"]
    return "\n".join(out) + "\n"
