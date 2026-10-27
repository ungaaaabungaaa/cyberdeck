"""Reproduce the recorded synthetic outputs through the real CLI; no hardware writes."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cyberdeck.cli import main
from cyberdeck.metrics import replay_status


def run():
    artifacts = {}
    artifacts["web/assets/bom.csv"] = (ROOT / "hardware/BOM.csv").read_bytes()
    with tempfile.TemporaryDirectory(prefix="cyberdeck-reproduction-") as temporary:
        temporary = Path(temporary)
        for command, destination, prefix in [
            ("enclosure", "design", "web/assets"),
            ("prepare", "setup", "docs/setup"),
        ]:
            args = [command, "--out", str(temporary / destination)]
            if command == "prepare":
                args += ["--user", "deck"]
            with redirect_stdout(io.StringIO()):
                assert main(args) == 0
            for file in sorted((temporary / destination).iterdir()):
                artifacts[f"{prefix}/{file.name}"] = file.read_bytes()
        for command in ["budget", "status"]:
            output = io.StringIO()
            with redirect_stdout(output):
                assert main([command]) == 0
            artifacts[
                f"docs/results/{'budget' if command == 'budget' else 'replay-status'}.json"
            ] = output.getvalue().encode()
        artifacts["docs/results/replay-series.json"] = (
            json.dumps([replay_status(tick * 5) for tick in range(12)], indent=2) + "\n"
        ).encode()
    sha = lambda data: hashlib.sha256(data).hexdigest()
    sources = ["models.py", "metrics.py", "files.py", "cli.py"]
    manifest = {
        "kind": "synthetic-model-and-enclosure-export",
        "date": "2026-10-27",
        "source_files_sha256": {
            **{
                f"cyberdeck/{name}": sha((ROOT / "cyberdeck" / name).read_bytes())
                for name in sources
            },
            "hardware/BOM.csv": sha((ROOT / "hardware/BOM.csv").read_bytes()),
        },
        "artifacts_sha256": {
            name: sha(data) for name, data in sorted(artifacts.items())
        },
        "unverified": [
            "Raspberry Pi boot and live sensors",
            "systemd/kiosk installation",
            "OpenSCAD rendering",
            "physical fit and retention",
            "electrical load and runtime",
            "thermal operation",
        ],
    }
    artifacts["docs/results/manifest.json"] = (
        json.dumps(manifest, indent=2) + "\n"
    ).encode()
    write = sys.argv[1:] == ["--write"]
    if sys.argv[1:] not in ([], ["--write"]):
        raise ValueError(
            "Use no arguments to verify, or --write to update recorded artifacts."
        )
    for name, data in artifacts.items():
        target = ROOT / name
        if write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        else:
            assert target.read_bytes() == data, f"Reproduction differs: {name}"
    print(
        f"{'Wrote' if write else 'Reproduced byte-for-byte'} {len(artifacts)} actual synthetic/model/setup artifacts."
    )


if __name__ == "__main__":
    run()
