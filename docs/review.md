# Review workflow

Three layers, from fastest feedback to slowest. The goal is as much to learn the practices as to protect the project, so each one says *why* it exists.

| Layer | When it runs | Why it exists |
| --- | --- | --- |
| Pre-commit hook | before every local commit | Cheapest place to catch a mistake: seconds after you made it, before it enters history. |
| CI (GitHub Actions) | every push and pull request | The hook can be skipped or not installed; CI is the check nobody can forget, and it runs on clean machines and several Python versions. |
| Pull request + human review | before merging to `master` | Machines check rules; a person checks meaning. It also leaves a readable record of *why* each change was made. |

## 1. Automatic: `python3 scripts/check.py`

Enable the hook once per clone: `git config core.hooksPath .githooks`.

| Check | Catches | Practice it teaches |
| --- | --- | --- |
| `version` | `pyproject.toml` and `__version__` out of sync | Single source of truth for the version. |
| `tests` | any failing test | Automated tests are what let you change code without fear. |
| `examples` | an example that stops verifying cleanly (`with-errors` must keep failing) | Examples are executable documentation; they rot unless tested. |
| `links` | broken relative links and images in Markdown | Docs are part of the product. |
| `language` | non-English text outside `README.es.md` | Conventions written in `AGENTS.md` are enforced, not just remembered. |
| `secrets` | tokens or private keys in tracked files | Secrets in git history are effectively permanent. |
| `images` | `docs/img/*.svg` differing from what the code renders; fix with `--update-images` | Generated artefacts must be reproducible, not hand-edited. |

CI also builds the package and runs `twine check`, which validates exactly what would be uploaded to PyPI.

## 2. Pull requests

Work on a branch, open a PR, merge when CI is green: `git switch -c feature/x`, commit, `git push -u origin feature/x`, `gh pr create`. Branch protection on `master` can make this mandatory (require a PR and a passing `tests` check).

## 3. Human review (each change, as relevant)

- **Archaeological meaning**: do vocabulary, relation rules and drawing conventions match field practice? Anything touching the vocabulary in `model.py` or `docs/data-model.md` needs a domain reviewer before version 1.
- **Data format**: does the change alter CSV columns or values? If so it breaks existing projects: say it in the commit, bump the minor version while in 0.x, and update the examples.
- **Honest scope**: README and `docs/data-model.md` mark what is implemented and what is a draft; nothing claims more than the code does.
- **Rendering**: open the SVGs changed by `--update-images` and look at them.
- **Messages**: `verify` messages say which row fails and why, in plain English.

## 4. Release checklist

1. `python3 scripts/check.py` passes and CI is green on `master`.
2. Version bumped in `pyproject.toml` and `src/harris_matrix/__init__.py`.
3. README images use absolute URLs (PyPI does not resolve relative paths); the repository is public.
4. `python -m build && twine check dist/*`.
5. Tag `vX.Y.Z`, then `twine upload` (only when the maintainer asks; see `AGENTS.md`).
6. Install the published package in a clean environment and run `harris-matrix verify` on an example.
