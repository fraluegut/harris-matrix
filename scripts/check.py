"""Project review: one command that checks everything that can be checked automatically.

    python3 scripts/check.py                  # run all checks
    python3 scripts/check.py --update-images  # regenerate docs/img from the examples

Exit code 1 if any check fails. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from harris_matrix import __version__, load_project, render_svg, verify  # noqa: E402

# image -> (example folder, render labels)
IMAGES = {
    "demo.svg": ("demo", ["unit_id"]),
    "demo-labels.svg": ("demo", ["unit_id", "subtype", "period"]),
    "errors.svg": ("with-errors", ["unit_id"]),
    "complex.svg": ("complex", ["unit_id"]),
    "bizarre.svg": ("bizarre", ["unit_id"]),
}
SECRET = re.compile(r"gh[opsu]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC )?PRIVATE KEY|pypi-[A-Za-z0-9_-]{20,}")
SPANISH = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡]")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")


def tracked() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / p for p in out.splitlines() if (ROOT / p).is_file()]


def check_version() -> list[str]:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    declared = re.search(r'^version = "([^"]+)"', text, re.M).group(1)
    return [] if declared == __version__ else [f"pyproject version {declared} != __version__ {__version__}"]


def check_tests() -> list[str]:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(stream=open("/dev/null" if sys.platform != "win32" else "NUL", "w")).run(suite)
    return [f"{len(result.failures) + len(result.errors)} failing test(s); run the tests for details"] if not result.wasSuccessful() else []


def check_examples() -> list[str]:
    problems = []
    for folder in sorted(p for p in (ROOT / "examples").iterdir() if p.is_dir()):
        issues = verify(load_project(folder))
        errors = [i for i in issues if i.severity == "error"]
        loud = [i for i in issues if i.severity == "warning"]
        if folder.name == "with-errors":
            if not errors:
                problems.append("examples/with-errors should contain errors but has none")
        elif errors or loud:
            problems.append(f"examples/{folder.name}: {len(errors)} error(s), {len(loud)} warning(s)")
    return problems


def check_links() -> list[str]:
    problems = []
    for md in [p for p in tracked() if p.suffix == ".md"]:
        for target in LINK.findall(md.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("mailto:"):
                continue
            if not (md.parent / target).exists():
                problems.append(f"{md.relative_to(ROOT)}: broken link {target}")
    return problems


def check_language() -> list[str]:
    """Everything is English except README.es.md (see AGENTS.md)."""
    problems = []
    for p in tracked():
        if p.suffix not in {".py", ".md", ".csv", ".toml", ".yml"} or p.name == "README.es.md":
            continue
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if SPANISH.search(line) and "authors" not in line and "README.es.md" not in line and p.name != "check.py":
                problems.append(f"{p.relative_to(ROOT)}:{n}: non-English text")
    return problems


def check_secrets() -> list[str]:
    problems = []
    for p in tracked():
        if p.suffix in {".svg", ".png"} or p.name == "check.py":
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if SECRET.search(text):
            problems.append(f"{p.relative_to(ROOT)}: looks like a secret")
    return problems


def render_image(name: str) -> str:
    folder, labels = IMAGES[name]
    return render_svg(load_project(ROOT / "examples" / folder), labels=labels)


def check_images() -> list[str]:
    return [
        f"docs/img/{name} is out of date (run: python3 scripts/check.py --update-images)"
        for name in IMAGES
        if not (ROOT / "docs/img" / name).exists()
        or (ROOT / "docs/img" / name).read_text(encoding="utf-8") != render_image(name)
    ]


CHECKS = {
    "version": check_version,
    "tests": check_tests,
    "examples": check_examples,
    "links": check_links,
    "language": check_language,
    "secrets": check_secrets,
    "images": check_images,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--update-images", action="store_true")
    args = parser.parse_args()
    if args.update_images:
        for name in IMAGES:
            (ROOT / "docs/img" / name).write_text(render_image(name), encoding="utf-8")
            print(f"updated docs/img/{name}")
        return 0
    failed = 0
    for name, fn in CHECKS.items():
        problems = fn()
        print(f"{'ok  ' if not problems else 'FAIL'} {name}")
        for p in problems:
            print(f"       - {p}")
        failed += bool(problems)
    print(f"\n{failed} check(s) failed" if failed else "\nall checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
