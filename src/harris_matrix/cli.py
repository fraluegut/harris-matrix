"""Command line: `harris-matrix verify|render FOLDER`."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .model import ProjectError, load_project
from .render import render_svg
from .verify import report_json, report_text, verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="harris-matrix")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_verify = sub.add_parser("verify", help="check the consistency of a project")
    p_verify.add_argument("folder")
    p_verify.add_argument("--json", action="store_true", help="machine-readable output")
    p_render = sub.add_parser("render", help="write the Harris matrix as SVG")
    p_render.add_argument("folder")
    p_render.add_argument("-o", "--output", default="-", help="output file (default: stdout)")
    p_render.add_argument("--no-errors", action="store_true", help="do not highlight cycles")
    p_render.add_argument(
        "--labels", default="unit_id",
        help="comma-separated fields to print in each node, e.g. unit_id,subtype,period "
             "(standard fields or any custom column of units.csv)",
    )
    args = parser.parse_args(argv)

    try:
        project = load_project(args.folder)
    except ProjectError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.command == "verify":
        issues = verify(project)
        print(report_json(issues) if args.json else report_text(issues))
        return 1 if any(i.severity == "error" for i in issues) else 0
    try:
        svg = render_svg(
            project,
            highlight_errors=not args.no_errors,
            labels=[f.strip() for f in args.labels.split(",") if f.strip()],
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.output == "-":
        sys.stdout.write(svg)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
