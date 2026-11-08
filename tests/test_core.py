import json
import tempfile
import unittest
from pathlib import Path

from harris_matrix import cargar_proyecto, renderizar_svg, verificar
from harris_matrix.cli import main

EJEMPLOS = Path(__file__).resolve().parents[1] / "examples"


def codigos(carpeta, idioma="es"):
    return {i.codigo for i in verificar(cargar_proyecto(EJEMPLOS / carpeta), idioma)}


class VerifyTest(unittest.TestCase):
    def test_demo_sin_errores(self):
        incs = verificar(cargar_proyecto(EJEMPLOS / "demo"))
        self.assertEqual([i for i in incs if i.severidad == "error"], [])

    def test_reglas_detectadas(self):
        self.assertTrue({"R01", "R02", "R03", "R04", "R05", "R10", "R11", "R14", "R15"} <= codigos("con-errores"))

    def test_idiomas(self):
        es = [i.mensaje for i in verificar(cargar_proyecto(EJEMPLOS / "con-errores"), "es")]
        en = [i.mensaje for i in verificar(cargar_proyecto(EJEMPLOS / "con-errores"), "en")]
        self.assertNotEqual(es, en)
        self.assertTrue(any("Duplicate" in m for m in en))

    def test_redundancia_transitiva(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "ues.csv").write_text("ue_id,tipo_unidad\n1,deposito\n2,deposito\n3,deposito\n")
            (Path(d) / "relaciones.csv").write_text(
                "ue_origen,tipo,ue_destino\n1,cubre,2\n2,cubre,3\n1,cubre,3\n")
            self.assertIn("R16", {i.codigo for i in verificar(cargar_proyecto(d))})


class RenderTest(unittest.TestCase):
    def test_svg_valido_y_nodos(self):
        import xml.etree.ElementTree as ET
        svg = renderizar_svg(cargar_proyecto(EJEMPLOS / "demo"))
        raiz = ET.fromstring(svg)
        ids = {e.get("id") for e in raiz.iter() if e.get("id")}
        self.assertIn("ue-1", ids)
        self.assertIn("ue-10-12", ids)  # igual_a fusionadas

    def test_ciclo_en_rojo(self):
        svg = renderizar_svg(cargar_proyecto(EJEMPLOS / "con-errores"))
        self.assertIn("nodo deposito error", svg)


class CliTest(unittest.TestCase):
    def test_codigo_salida(self):
        self.assertEqual(main(["verify", str(EJEMPLOS / "demo")]), 0)
        self.assertEqual(main(["--lang", "en", "verify", str(EJEMPLOS / "con-errores")]), 1)

    def test_json(self):
        import contextlib, io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(["verify", "--json", str(EJEMPLOS / "con-errores")])
        self.assertIsInstance(json.loads(buf.getvalue()), list)


if __name__ == "__main__":
    unittest.main()
