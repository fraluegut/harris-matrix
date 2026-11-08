# Instrucciones de trabajo

- Cada cambio relativamente mínimo o acotado debe terminar con un commit y, cuando exista el remoto `origin`, un push a `origin/master`.
- Antes de hacer push, comprobar que el cambio compila o pasa la verificación relevante y que no se han incluido secretos.
- No publicar en PyPI sin que el usuario lo pida expresamente.

# Proyecto

Librería Python (`harris-matrix`, import `harris_matrix`) para arqueología estratigráfica y paramental: modelo de datos desde CSV, verificación de coherencia y matriz de Harris en SVG. Diseño en `docs/modelo-de-datos.md`.

- Código en `src/harris_matrix/`, tests en `tests/`.
- Sin dependencias en tiempo de ejecución salvo que se justifique; las de desarrollo van en `[project.optional-dependencies].dev`.
- Vocabulario y mensajes en español.
