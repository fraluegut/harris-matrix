# Working instructions

- Every relatively small, self-contained change ends with a commit and, when the `origin` remote exists, a push to `origin/master`.
- Before pushing, run `python3 scripts/check.py` (also run by the pre-commit hook and CI; see `docs/review.md`). It covers tests, examples, links, language, secrets and generated images.
- The user's goal is to learn how to build a library with good practices: when adding tooling or conventions, briefly explain why it is good practice.
- Do not publish to PyPI unless the user explicitly asks.

# Project

Python library (`harris-matrix`, import `harris_matrix`) for stratigraphic and standing-buildings archaeology: data model from CSV, consistency checks and Harris matrix as SVG. Design in `docs/data-model.md`.

- Code in `src/harris_matrix/`, tests in `tests/`, sample projects in `examples/`.
- No runtime dependencies unless justified; development ones go in `[project.optional-dependencies].dev`.
- Language: everything (code, identifiers, comments, docstrings, messages, CSV vocabulary, docs) is in English. Only `README.md` (English) and `README.es.md` (Spanish) are bilingual.
