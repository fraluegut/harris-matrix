import contextlib
import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from harris_matrix import load_project, render_svg, verify
from harris_matrix.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def codes(folder):
    return {i.code for i in verify(load_project(EXAMPLES / folder))}


class VerifyTest(unittest.TestCase):
    def test_demo_has_no_errors(self):
        issues = verify(load_project(EXAMPLES / "demo"))
        self.assertEqual([i for i in issues if i.severity == "error"], [])

    def test_rules_detected(self):
        expected = {"R01", "R02", "R03", "R04", "R05", "R10", "R11", "R14", "R15"}
        self.assertTrue(expected <= codes("with-errors"))

    def test_complex_example_is_clean(self):
        self.assertEqual(verify(load_project(EXAMPLES / "complex")), [])

    def test_bizarre_example_only_reports_a_redundancy(self):
        self.assertEqual({(i.code, i.severity) for i in verify(load_project(EXAMPLES / "bizarre"))},
                         {("R16", "info")})

    def test_bonded_but_sequenced_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "units.csv").write_text("unit_id,unit_type\n1,structure\n2,structure\n")
            (Path(d) / "relations.csv").write_text(
                "from_unit,type,to_unit\n1,bonded_to,2\n1,covers,2\n")
            self.assertIn("R18", {i.code for i in verify(load_project(d))})

    def test_transitive_redundancy(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "units.csv").write_text("unit_id,unit_type\n1,deposit\n2,deposit\n3,deposit\n")
            (Path(d) / "relations.csv").write_text(
                "from_unit,type,to_unit\n1,covers,2\n2,covers,3\n1,covers,3\n")
            self.assertIn("R16", {i.code for i in verify(load_project(d))})

    def test_inverse_names_are_normalised(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "units.csv").write_text("unit_id,unit_type\n1,deposit\n2,deposit\n")
            (Path(d) / "relations.csv").write_text("from_unit,type,to_unit\n2,covered_by,1\n")
            rel = load_project(d).relations[0]
            self.assertEqual((rel.from_unit, rel.type, rel.to_unit), ("1", "covers", "2"))


class RenderTest(unittest.TestCase):
    def test_valid_svg_and_nodes(self):
        root = ET.fromstring(render_svg(load_project(EXAMPLES / "demo")))
        ids = {e.get("id") for e in root.iter() if e.get("id")}
        self.assertIn("unit-1", ids)
        self.assertIn("unit-10-12", ids)  # merged same_as units

    def test_labels_show_extra_fields(self):
        project = load_project(EXAMPLES / "demo")
        svg = render_svg(project, labels=["unit_id", "subtype", "period"])
        self.assertIn(">Late Roman<", svg)
        self.assertIn(">collapse<", svg)
        ET.fromstring(svg)  # still valid XML
        self.assertIn(">Iron Age<", render_svg(project, labels=["unit_id", "period"]))  # merged 10 = 12: one value

    def test_unknown_label_is_rejected(self):
        with self.assertRaises(ValueError):
            render_svg(load_project(EXAMPLES / "demo"), labels=["nonsense"])

    def test_bonded_units_share_a_row(self):
        root = ET.fromstring(render_svg(load_project(EXAMPLES / "bizarre")))
        y = {
            g.get("id"): g.find("{http://www.w3.org/2000/svg}rect").get("y")
            for g in root.iter("{http://www.w3.org/2000/svg}g")
            if g.get("id") in ("unit-W1", "unit-W3")
        }
        self.assertEqual(len(y), 2)
        self.assertEqual(y["unit-W1"], y["unit-W3"])

    def test_cycle_highlighted(self):
        svg = render_svg(load_project(EXAMPLES / "with-errors"))
        self.assertIn("node deposit error", svg)


class CliTest(unittest.TestCase):
    def test_exit_code(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["verify", str(EXAMPLES / "demo")]), 0)
            self.assertEqual(main(["verify", str(EXAMPLES / "with-errors")]), 1)

    def test_json(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(["verify", "--json", str(EXAMPLES / "with-errors")])
        self.assertIsInstance(json.loads(buf.getvalue()), list)


if __name__ == "__main__":
    unittest.main()
