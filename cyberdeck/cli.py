"""Local CLI. Setup commands generate files; they never apply host changes."""

import argparse
import json
from pathlib import Path
import re
import sys
from .files import read_config, write_bundle
from .metrics import collect_live, replay_status
from .models import budget, enclosure, panel_svg, enclosure_scad
from .server import make_server


def setup_files(username):
    if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", username):
        raise ValueError("Use a simple Linux username of at most 32 characters.")
    target = f"/home/{username}/cyberdeck"
    return {
        "cyberdeck.service": f"""[Unit]
Description=CyberDeck read-only local dashboard

[Service]
Type=simple
WorkingDirectory={target}
ExecStart=/usr/bin/python3 -m cyberdeck serve --live --port 8794
Environment=PYTHONDONTWRITEBYTECODE=1
Restart=on-failure
RestartSec=5
NoNewPrivileges=yes
UMask=0077

[Install]
WantedBy=default.target
""",
        "labwc-autostart.fragment": "# Review and append this to the target user's existing labwc autostart.\nchromium http://127.0.0.1:8794/ --kiosk --no-first-run &\n",
        "DEPLOYMENT.md": f"""# Manual target setup

Nothing was installed or enabled by this generator. These templates target a Raspberry Pi OS 64-bit desktop with labwc and Chromium. Hardware boot and kiosk operation are not yet verified.

1. Set up Raspberry Pi OS with the official Imager. Choose your own credentials. Do not put credentials in this repository.
2. Place the checked-out project at `{target}`. Confirm Python 3.11+ and Chromium are installed on the target. Run `python3 -m cyberdeck status --live` there. Missing sensors stay null.
3. Review `cyberdeck.service`. Copy it to the target user's `~/.config/systemd/user/`, then run `systemctl --user daemon-reload` and `systemctl --user enable --now cyberdeck.service` as that user. Check `systemctl --user status cyberdeck.service`.
4. Open http://127.0.0.1:8794/ on the target. Verify the LIVE label and each reading against the OS before using the display.
5. For optional kiosk startup, back up `~/.config/labwc/autostart` and append the reviewed fragment. Do not replace its existing content. Log out/in and test. The service starts at user login, not as an installed system image.
6. Roll back with `systemctl --user disable --now cyberdeck.service`, remove only this service and the added autostart line, and restore the saved configuration if needed. No data partition is changed.

Official guide: https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/
""",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="CyberDeck software and unbuilt enclosure workbench"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser(
        "serve", help="Read-only loopback viewer; fixture replay by default"
    )
    serve.add_argument("--live", action="store_true")
    serve.add_argument("--disk-path", type=Path)
    serve.add_argument("--port", type=int, default=8794)
    status = commands.add_parser(
        "status", help="Read-only local OS metrics or labeled fixture snapshot"
    )
    status.add_argument("--live", action="store_true")
    status.add_argument("--disk-path", type=Path)
    power = commands.add_parser(
        "budget", help="Nominal energy/supply model, not battery telemetry"
    )
    power.add_argument("--config")
    design = commands.add_parser(
        "enclosure", help="Write prototype OpenSCAD/SVG/metadata in a new directory"
    )
    design.add_argument("--config")
    design.add_argument("--out", required=True)
    prepare = commands.add_parser(
        "prepare", help="Generate target setup templates without applying them"
    )
    prepare.add_argument("--out", required=True)
    prepare.add_argument("--user", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in ("serve", "status") and args.disk_path is not None:
            if not args.live or not args.disk_path.is_dir():
                raise ValueError("--disk-path requires --live and an existing directory.")
        if args.command == "serve":
            if not 1 <= args.port <= 65535:
                raise ValueError("Port must be from 1 to 65535.")
            server = make_server(args.port, args.live, disk_path=args.disk_path)
            print(
                f"http://127.0.0.1:{args.port}/ — {'live local reads' if args.live else 'synthetic replay'}",
                flush=True,
            )
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
        elif args.command == "status":
            print(
                json.dumps(
                    collect_live(disk_path=args.disk_path)
                    if args.live
                    else replay_status(0),
                    indent=2,
                    allow_nan=False,
                )
            )
        elif args.command == "budget":
            print(
                json.dumps(
                    budget(read_config(args.config)) if args.config else budget(),
                    indent=2,
                    allow_nan=False,
                )
            )
        elif args.command == "enclosure":
            model = enclosure(read_config(args.config)) if args.config else enclosure()
            write_bundle(
                args.out,
                {
                    "enclosure.scad": enclosure_scad(model),
                    "panel.svg": panel_svg(model),
                    "enclosure.json": json.dumps(model, indent=2) + "\n",
                },
            )
            print(
                "Wrote analytic prototype source. CAD render, physical fit and thermal tests remain pending."
            )
        elif args.command == "prepare":
            write_bundle(args.out, setup_files(args.user))
            print(
                "Wrote setup templates only. No host settings or services were changed."
            )
        return 0
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    except OSError:
        print(
            "I/O failed; use existing input files and a new output directory whose parent exists.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
