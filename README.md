# harris-matrix

Librería Python para **registrar, verificar y dibujar la estratigrafía arqueológica**, tanto de excavación como de arqueología paramental (de la arquitectura).

> Estado: **planificación** (v0.0.1). Todavía no hay funcionalidad; solo el esqueleto del paquete y el diseño del modelo de datos.

## Objetivo

1. **Modelo de datos** de unidades estratigráficas (UE), relaciones, posición espacial, cronología, materiales y agrupaciones, leído desde CSV.
2. **`verify`**: comprobar que el registro es coherente (referencias, ciclos, relaciones imposibles, dataciones contradictorias con la secuencia, cotas).
3. **`render`**: generar la matriz de Harris en **SVG** editable (Inkscape, Illustrator...), además de DOT y GraphML.
4. Compatibilidad de importación y exportación con el [Harris Matrix Data Package](https://www.iosa.it/specs/harris-matrix-data-package/) (hmdp).

## Principios

- Se registran los hechos observados; el orden temporal, las fases y el gráfico se **derivan**.
- Toda relación y toda datación lleva **certeza** y **fuente**.
- La ausencia de relación no implica contemporaneidad.
- Ficheros abiertos: un CSV por tabla, UTF-8, versionables con git.

Ver el diseño completo en [docs/modelo-de-datos.md](docs/modelo-de-datos.md).

## Desarrollo

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Sin instalar nada, los tests también se pueden lanzar con la librería estándar:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Licencia

Pendiente de decidir antes de publicar.
