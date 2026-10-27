import math
import unittest
import xml.etree.ElementTree as ET
from cyberdeck.models import budget, enclosure, panel_svg, enclosure_scad


class BudgetTests(unittest.TestCase):
    def test_wh_efficiency_and_reserve_have_distinct_denominators(self):
        result = budget(
            {
                "capacity_wh": 100,
                "load_w": 10,
                "efficiency": 0.8,
                "reserve_fraction": 0.25,
                "supply_w": 15,
            }
        )
        self.assertEqual(result["full_output_wh"], 80)
        self.assertEqual(result["usable_output_wh"], 60)
        self.assertEqual(result["full_runtime_hours"], 8)
        self.assertEqual(result["usable_runtime_hours"], 6)
        self.assertEqual(result["supply_headroom_w"], 5)
        self.assertTrue(result["within_nominal_supply"])
        self.assertFalse(
            budget({"load_w": 20, "supply_w": 15})["within_nominal_supply"]
        )

    def test_scaling_and_invalid_explicit_values(self):
        self.assertAlmostEqual(
            budget({"load_w": 20})["usable_runtime_hours"] * 2,
            budget({"load_w": 10})["usable_runtime_hours"],
        )
        for key in [
            "capacity_wh",
            "load_w",
            "efficiency",
            "reserve_fraction",
            "supply_w",
        ]:
            for value in [True, None, math.nan, math.inf, "10", 10**1000]:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    budget({key: value})
        for value in [
            {"unknown": 1},
            {"capacity_wh": 0},
            {"efficiency": 1.1},
            {"reserve_fraction": 1},
            {"load_w": -0.1},
            [],
        ]:
            with self.assertRaises(ValueError):
                budget(value)


class EnclosureTests(unittest.TestCase):
    def test_dimensions_are_mm_and_all_cutouts_remain_inside_panel(self):
        result = enclosure()
        self.assertEqual(result["unit"], "mm")
        self.assertEqual(result["viewing_window_mm"], [156.5, 89])
        self.assertEqual(result["display_outline_mm"], [189.5, 120, 15])
        self.assertEqual(result["inner_size_mm"], [234, 154, 64])
        for x, y in result["panel_hole_centres_mm"]:
            radius = result["settings"]["hole_diameter_mm"] / 2
            self.assertGreater(x - radius, 2)
            self.assertGreater(y - radius, 2)
            self.assertLess(x + radius, result["settings"]["width_mm"] - 2)
            self.assertLess(y + radius, result["settings"]["height_mm"] - 2)
        svg = ET.fromstring(panel_svg(result))
        self.assertEqual(svg.attrib["width"], "240mm")
        self.assertEqual(svg.attrib["height"], "160mm")
        outer = svg.find(".//{http://www.w3.org/2000/svg}rect")
        self.assertEqual(float(outer.attrib["x"]), 0)
        self.assertEqual(float(outer.attrib["width"]), 240)
        self.assertIn('part = "assembly"', enclosure_scad(result))
        self.assertEqual(panel_svg(result), panel_svg(enclosure()))

    def test_invalid_and_extreme_geometry_fails_before_export(self):
        for value in [
            {"wall_mm": 1},
            {"width_mm": 100},
            {"depth_mm": 20},
            {"clearance_mm": 9},
            {"height_mm": math.nan},
            {"width_mm": True},
            {"x": 1},
            [],
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                enclosure(value)
        # Individual field limits are further constrained by assembly clearance.
        with self.assertRaises(ValueError):
            enclosure({"width_mm": 220, "height_mm": 145, "wall_mm": 5})
        for w, h, wall in [(240, 160, 5), (360, 260, 2)]:
            result = enclosure({"width_mm": w, "height_mm": h, "wall_mm": wall})
            self.assertGreaterEqual(min(result["display_margin_mm"]), 6)


if __name__ == "__main__":
    unittest.main()
