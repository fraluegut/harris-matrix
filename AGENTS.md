# Working instructions

- Every relatively small, self-contained change ends with a commit and, when the `origin` remote exists, a push to `origin/master`.
- Before pushing, check that the change builds or passes the relevant verification and that no secrets are included.
- Do not publish to PyPI unless the user explicitly asks.

# Project

Python library (`harris-matrix`, import `harris_matrix`) for stratigraphic and standing-buildings archaeology: data model from CSV, consistency checks and Harris matrix as SVG. Design in `docs/data-model.md`.

- Code in `src/harris_matrix/`, tests in `tests/`, sample projects in `examples/`.
- No runtime dependencies unless justified; development ones go in `[project.optional-dependencies].dev`.
- Language: everything (code, identifiers, comments, docstrings, messages, CSV vocabulary, docs) is in English. Only `README.md` (English) and `README.es.md` (Spanish) are bilingual.
