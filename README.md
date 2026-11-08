# harris-matrix

**Record, verify and draw archaeological stratigraphy** (excavation and standing-buildings archaeology) from plain CSV files. Zero runtime dependencies.

🇪🇸 [Leer en español](README.es.md)

> Status: **alpha (0.1)**. Core model, `verify` and SVG `render` work; spatial/chronological rules and the hmdp adapter are planned. The data model is a draft that has not yet been reviewed by field archaeologists ([design](docs/modelo-de-datos.md), in Spanish).

![Harris matrix generated from examples/demo](docs/img/demo.svg)

## How it works

```
 ues.csv ---------+
                  +--> model --> temporal graph --+--> verify --> report (text/JSON)
 relaciones.csv --+    (igual_a merged)           |              exit code 1 on errors
                                                  +--> render --> editable SVG
```

Facts are recorded (which unit covers, cuts or fills which); order and drawing are **derived**. Every relation carries a certainty (`segura`, `probable`, `dudosa`), drawn as solid, dashed or dotted lines. Absence of a relation never implies contemporaneity.

## Quick start

```bash
pip install -e .
harris-matrix verify examples/demo
harris-matrix render examples/demo -o matrix.svg
```

Input is a folder with two CSV files (UTF-8):

| `ues.csv` | |
| --- | --- |
| `ue_id` | unit identifier (text, e.g. `1045b`) |
| `tipo_unidad` | `deposito` · `interfaz` · `estructura` · `virtual` |
| `subtipo`, `descripcion` | optional |

| `relaciones.csv` | |
| --- | --- |
| `ue_origen`, `tipo`, `ue_destino` | the origin unit is **later** than the destination |
| `certeza` | `segura` (default) · `probable` · `dudosa` |

Relation types: `cubre` (covers), `corta` (cuts), `rellena` (fills), `se_apoya_en` (abuts/rests on), `se_une_a` (bonded), `igual_a` (same unit), `posterior_a`. Inverse names (`cubierto_por`…) are accepted.

## Verification

```console
$ harris-matrix --lang en verify examples/con-errores
error   R01  ues.csv:9            Duplicate SU 2 (also on row 3)
error   R02  relaciones.csv:4     Relation refers to missing SU 99
error   R03  relaciones.csv:8     Unknown relation type: 'toca'
error   R04  relaciones.csv:7     6 corta 1: not allowed between 'estructura' and 'deposito'
error   R05  relaciones.csv:9     SU 2 is related to itself
error   R10  relaciones.csv       Cycle in the sequence: 1 → 2 → 7 → 1
error   R11  relaciones.csv       Direct contradiction between 4 and 5
warning R14  ues.csv:4            Cut 3 has no recorded fill
warning R15  ues.csv:7            SU 6 has no relations
7 errors, 2 warnings, 0 notes
```

Implemented: R01–R05, R10–R16 (duplicates, dangling references, vocabulary, allowed unit types, cycles, `igual_a` conflicts, unfilled cuts, orphans, transitive redundancy). `--json` for machine output; `--lang es|en` for messages.

Cycles are highlighted in red in the SVG:

![Matrix with a cycle highlighted](docs/img/errors.svg)

## SVG output

Editable in Inkscape/Illustrator: one `<g id="ue-1045" data-tipo="…">` per unit (merged `igual_a` units share a node, e.g. `10 = 12`), rectangles for deposits, rounded for interfaces, thick for structures, styles embedded.

## Python API

```python
from harris_matrix import cargar_proyecto, verificar, renderizar_svg

p = cargar_proyecto("examples/demo")
problems = verificar(p, idioma="en")
open("matrix.svg", "w", encoding="utf-8").write(renderizar_svg(p))
```

## Roadmap

- Phases, dates and propagation rules (R30–R34); spatial checks (R20–R23)
- Standing-buildings vocabulary (wall faces, bonded/abutting relations)
- DOT/GraphML export, [hmdp](https://www.iosa.it/specs/harris-matrix-data-package/) import/export
- Better edge routing for relations spanning several levels
- Optional nanopublication export (relations and datings with provenance)

## Development

```bash
pip install -e ".[dev]" && pytest
# or, without installing anything:
PYTHONPATH=src python3 -m unittest discover -s tests
```

## License

To be decided before the first public release.
