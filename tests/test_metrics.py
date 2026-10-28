import json
from pathlib import Path
import tempfile
import unittest
from cyberdeck.metrics import collect_live, replay_status


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "proc").mkdir()
        sensor = self.root / "sys/class/thermal/thermal_zone0"
        sensor.mkdir(parents=True)
        (sensor / "type").write_text("cpu-thermal\n")
        (sensor / "temp").write_text("47500\n")
        battery = self.root / "sys/class/power_supply/BAT0"
        battery.mkdir(parents=True)
        (battery / "type").write_text("Battery\n")
        (battery / "capacity").write_text("72\n")
        (self.root / "proc/meminfo").write_text(
            "MemTotal: 1000 kB\nMemAvailable: 250 kB\n"
        )
        (self.root / "proc/uptime").write_text("120.5 80.2\n")
        (self.root / "proc/loadavg").write_text("0.50 0.30 0.20 1/100 9988\n")

    def tearDown(self):
        self.temp.cleanup()

    def test_live_values_have_units_and_source_metadata(self):
        result = collect_live(self.root, disk_usage=lambda _: (10000, 6000, 4000))
        self.assertEqual(result["mode"], "live")
        self.assertEqual(result["metrics"]["memory_total_bytes"], 1024000)
        self.assertEqual(result["metrics"]["memory_available_bytes"], 256000)
        self.assertEqual(result["metrics"]["temperature_c"], 47.5)
        self.assertEqual(result["metrics"]["uptime_seconds"], 120.5)
        self.assertEqual(result["metrics"]["load_1m"], 0.5)
        self.assertEqual(result["metrics"]["battery_percent"], 72)
        self.assertEqual(result["metrics"]["disk_free_bytes"], 4000)
        self.assertEqual(result["missing"], [])
        self.assertIsNone(result["trace_elapsed_seconds"])
        self.assertIn("/proc/meminfo", result["sources"]["memory_total_bytes"])
        self.assertNotIn("9988", json.dumps(result))  # no process IDs

    def test_missing_malformed_out_of_range_and_oversized_sources_stay_null(self):
        (self.root / "proc/meminfo").write_text(
            "MemTotal: 100 kB\nMemAvailable: 200 kB\n"
        )
        (self.root / "proc/loadavg").write_text("nan 0 0 1/1 1")
        (self.root / "proc/uptime").write_text("-1 0")
        (self.root / "sys/class/thermal/thermal_zone0/temp").write_text("999999")
        (self.root / "sys/class/power_supply/BAT0/capacity").write_text("101")
        result = collect_live(self.root, disk_usage=lambda _: (100, 0, 200))
        self.assertTrue(all(value is None for value in result["metrics"].values()))
        self.assertEqual(len(result["missing"]), 8)
        (self.root / "proc/loadavg").write_text("x" * 1025)
        self.assertIsNone(collect_live(self.root)["metrics"]["load_1m"])

    def test_python_only_numeric_syntax_is_not_treated_as_sensor_data(self):
        (self.root / "proc/loadavg").write_text("1_0 0 0 1/1 1")
        (self.root / "proc/uptime").write_text("1_200 0")
        (self.root / "proc/meminfo").write_text("MemTotal: 1_000 kB\nMemAvailable: 2_50 kB\n")
        (self.root / "sys/class/thermal/thermal_zone0/temp").write_text("47_500")
        (self.root / "sys/class/power_supply/BAT0/capacity").write_text("7_2")
        result = collect_live(self.root, disk_usage=lambda _: (10000, 6000, 4000))
        for key in ("load_1m", "uptime_seconds", "memory_total_bytes", "memory_available_bytes", "temperature_c", "battery_percent"):
            self.assertIsNone(result["metrics"][key], key)
            self.assertIsNone(result["sources"][key], key)
            self.assertIn(key, result["missing"])
        self.assertEqual(result["metrics"]["disk_free_bytes"], 4000)

    def test_replay_is_explicit_deterministic_and_never_claims_a_collection_time(self):
        a = replay_status(0)
        self.assertEqual(a, replay_status(0))
        self.assertEqual(a["mode"], "replay")
        self.assertIsNone(a["collected_at"])
        self.assertEqual(a["trace_elapsed_seconds"], 0)
        self.assertIn("synthetic", a["note"].lower())
        self.assertTrue(
            all(
                source in (None, "synthetic fixture")
                for source in a["sources"].values()
            )
        )
        self.assertNotEqual(
            a["metrics"]["temperature_c"], replay_status(10)["metrics"]["temperature_c"]
        )
        self.assertIsNone(a["metrics"]["battery_percent"])
        for elapsed in [-1, float("nan"), True]:
            with self.assertRaises(ValueError):
                replay_status(elapsed)


if __name__ == "__main__":
    unittest.main()
