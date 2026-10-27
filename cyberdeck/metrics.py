"""Bounded, read-only metrics. No subprocesses and no fake live fallbacks."""

from datetime import datetime, timezone
import math
from pathlib import Path
import shutil

RANGES = {
    "load_1m": (0, 1_000_000),
    "memory_total_bytes": (0, 2**53 - 1),
    "memory_available_bytes": (0, 2**53 - 1),
    "temperature_c": (-30, 150),
    "uptime_seconds": (0, 1e12),
    "disk_total_bytes": (0, 2**53 - 1),
    "disk_free_bytes": (0, 2**53 - 1),
    "battery_percent": (0, 100),
}


def _read(root, path, limit=1024):
    try:
        with (root / path.lstrip("/")).open("rb") as stream:
            data = stream.read(limit + 1)
        return data.decode("utf-8", errors="strict") if len(data) <= limit else None
    except (OSError, UnicodeError):
        return None


def _number(value, key):
    try:
        number = float(value)
        low, high = RANGES[key]
        return number if math.isfinite(number) and low <= number <= high else None
    except (TypeError, ValueError, OverflowError):
        return None


def _result(mode, metrics, sources, elapsed=None):
    return {
        "schema_version": 1,
        "mode": mode,
        "collected_at": (
            datetime.now(timezone.utc).isoformat() if mode == "live" else None
        ),
        "trace_elapsed_seconds": elapsed,
        "metrics": metrics,
        "sources": sources,
        "missing": [key for key, value in metrics.items() if value is None],
        "note": (
            "Synthetic fixture replay; no hardware is being measured."
            if mode == "replay"
            else "Read-only local OS values. Unsupported or malformed sensors stay null; no fixture fallback. Load is a one-minute load average, not CPU utilisation."
        ),
    }


def collect_live(root=Path("/"), disk_usage=shutil.disk_usage):
    root = Path(root)
    metrics = dict.fromkeys(RANGES)
    sources = dict.fromkeys(RANGES)

    def put(key, value, source):
        value = _number(value, key)
        metrics[key] = value
        sources[key] = source if value is not None else None

    for key, path in [("load_1m", "/proc/loadavg"), ("uptime_seconds", "/proc/uptime")]:
        data = _read(root, path)
        put(key, data.split()[0] if data and data.split() else None, path)
    data = _read(root, "/proc/meminfo", 65536)
    if data:
        memory = {}
        for line in data.splitlines():
            cells = line.split()
            if (
                len(cells) == 3
                and cells[0] in ("MemTotal:", "MemAvailable:")
                and cells[2] == "kB"
            ):
                value = _number(cells[1], "memory_total_bytes")
                memory[cells[0]] = value * 1024 if value is not None else None
        total, available = memory.get("MemTotal:"), memory.get("MemAvailable:")
        if total is None or available is None or available <= total:
            put("memory_total_bytes", total, "/proc/meminfo: MemTotal × 1024")
            put(
                "memory_available_bytes",
                available,
                "/proc/meminfo: MemAvailable × 1024",
            )
    sensor = "/sys/class/thermal/thermal_zone0"
    kind = _read(root, sensor + "/type", 128)
    if kind and any(name in kind.lower() for name in ("cpu", "soc", "bcm")):
        raw = _read(root, sensor + "/temp", 128)
        try:
            put("temperature_c", float(raw) / 1000, sensor + "/temp ÷ 1000")
        except (ValueError, TypeError):
            pass
    battery = "/sys/class/power_supply/BAT0"
    kind = _read(root, battery + "/type", 128)
    if kind and kind.strip() == "Battery":
        put(
            "battery_percent",
            _read(root, battery + "/capacity", 128),
            battery + "/capacity",
        )
    try:
        total, _used, free = disk_usage(Path(__file__).resolve().parent)
        if 0 <= free <= total:
            put("disk_total_bytes", total, "shutil.disk_usage: project filesystem")
            put("disk_free_bytes", free, "shutil.disk_usage: project filesystem")
    except (OSError, ValueError, TypeError):
        pass
    return _result("live", metrics, sources)


def replay_status(elapsed):
    if (
        isinstance(elapsed, bool)
        or not isinstance(elapsed, (float, int))
        or not math.isfinite(elapsed)
        or elapsed < 0
    ):
        raise ValueError("Replay elapsed time must be finite and non-negative.")
    temperatures = (42, 43, 44.5, 46, 48, 49.5, 48.5, 47, 45.5, 44, 43, 42.5)
    loads = (0.12, 0.25, 0.48, 0.72, 1.1, 1.35, 1.2, 0.85, 0.55, 0.3, 0.2, 0.15)
    index = int(elapsed // 5) % len(temperatures)
    metrics = {
        "load_1m": loads[index],
        "memory_total_bytes": 4 * 1024**3,
        "memory_available_bytes": (3100 - index * 20) * 1024**2,
        "temperature_c": temperatures[index],
        "uptime_seconds": 3600 + index * 5,
        "disk_total_bytes": 32 * 1024**3,
        "disk_free_bytes": 24 * 1024**3,
        "battery_percent": None,
    }
    return _result(
        "replay",
        metrics,
        {
            key: "synthetic fixture" if value is not None else None
            for key, value in metrics.items()
        },
        index * 5,
    )
