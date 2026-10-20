import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from car_spec_explainer import CarSpec, explain, load_spec
from car_spec_explainer.cli import main
from car_spec_explainer.explain import compare, metrics

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class MetricsTests(unittest.TestCase):
    def test_unit_conversions_and_ratios(self):
        m = metrics(CarSpec("Test", hp=200, torque_lbft=200, weight_lb=3000))
        self.assertAlmostEqual(m["kw"], 149.1, places=1)
        self.assertAlmostEqual(m["torque_nm"], 271.2, places=1)
        self.assertEqual(m["weight_kg"], 1361)
        self.assertEqual(m["lb_per_hp"], 15.0)
        self.assertEqual(m["torque_to_hp"], 1.0)

    def test_lighter_car_is_estimated_quicker(self):
        heavy = metrics(CarSpec("Heavy", 200, 200, 4000))
        light = metrics(CarSpec("Light", 200, 200, 2500))
        self.assertLess(light["est_0_60_s"], heavy["est_0_60_s"])

    def test_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            CarSpec("Bad", hp=0, torque_lbft=100, weight_lb=3000)
        with self.assertRaises(ValueError):
            CarSpec("Bad", hp=100, torque_lbft=100, weight_lb=3000, drivetrain="hover")


class ExplainTests(unittest.TestCase):
    def test_turbo_style_torque_is_called_out(self):
        text = explain(load_spec(EXAMPLES / "hot-hatch.json"))
        self.assertIn("strong low in the rev range", text)
        self.assertIn("Front-wheel drive", text)
        self.assertIn("comes early", text)

    def test_balanced_and_revvy_engines(self):
        text = explain(load_spec(EXAMPLES / "roadster.json"))
        self.assertIn("balanced", text)
        self.assertIn("Rear-wheel drive", text)
        revvy = explain(CarSpec("Revvy", hp=300, torque_lbft=200, weight_lb=2800, drivetrain="rwd"))
        self.assertIn("makes its power by revving", revvy)

    def test_compare_picks_better_power_to_weight(self):
        a = CarSpec("A", 300, 250, 3000, "rwd")
        b = CarSpec("B", 200, 300, 3000, "awd")
        out = compare(a, b)
        self.assertIn("A has the better power-to-weight ratio", out)
        self.assertIn("B has more torque", out)


class CliTests(unittest.TestCase):
    def test_cli_json_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--hp", "300", "--torque", "280", "--weight", "3300", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue())["lb_per_hp"], 11.0)


if __name__ == "__main__":
    unittest.main()
