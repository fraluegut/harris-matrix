# harris-matrix

**Registrar, verificar y dibujar la estratigrafía arqueológica** (excavación y arqueología paramental) desde ficheros CSV. Sin dependencias en tiempo de ejecución.

🇬🇧 [Read in English](README.md)

> Estado: **alfa (0.1)**. Funcionan el modelo base, `verify` y `render` a SVG. El modelo de datos es un borrador sin contrastar con arqueólogos de campo (ver el [diseño](docs/data-model.md), en inglés).

![Matriz de Harris generada desde examples/demo](docs/img/demo.svg)

## Uso

```bash
pip install -e .
harris-matrix verify examples/demo
harris-matrix render examples/demo -o matriz.svg
```

Una carpeta con dos CSV (UTF-8):

- `units.csv` (unidades): `unit_id`, `unit_type` (`deposit` depósito, `interface` interfaz, `structure` estructura, `virtual`), `subtype`, `description`.
- `relations.csv` (relaciones): `from_unit`, `type`, `to_unit`, `certainty` (`certain` segura, `probable`, `doubtful` dudosa). La unidad de origen es **posterior** a la de destino.

Tipos de relación: `covers` (cubre), `cuts` (corta), `fills` (rellena), `rests_on` (se apoya en), `bonded_to` (trabada con), `same_as` (igual a), `later_than` (posterior a). Se aceptan también las inversas (`covered_by`, `cut_by`...).

Verificación (R01–R06, R10–R16, R18): duplicados, referencias inexistentes, vocabulario, tipos admitidos, ciclos, cortes sin relleno, unidades huérfanas, relaciones redundantes. Los ciclos salen en rojo en el SVG. Devuelve código de salida distinto de cero si hay errores; `--json` para salida automática.

Qué se muestra en cada cuadro: por defecto el identificador. Con `--labels unit_id,subtype,period` se imprimen esos campos, uno por línea; vale cualquier columna estándar o extra de `units.csv` (por ejemplo `period` para la cronología). Desde Python: `render_svg(project, labels=[...])`.

Principios: se registran hechos, el orden y el gráfico se derivan; toda relación lleva certeza; la ausencia de relación no implica contemporaneidad.

Desde Python:

```python
from harris_matrix import load_project, verify, render_svg

project = load_project("examples/demo")
issues = verify(project)
svg = render_svg(project)
```

## Desarrollo

```bash
pip install -e ".[dev]" && pytest
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Licencia

MIT, ver [LICENSE](LICENSE).
