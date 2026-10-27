# Methods and primary sources

## Data provenance and units

Default mode replays 12 explicit synthetic samples from `cyberdeck/metrics.py`, one every five trace seconds. The trace repeats after 60 seconds. It has a null collection timestamp and a synthetic source for each supplied value. Battery remains null. The chart contains received samples only, at most 60, and clears if the source mode changes. Its horizontal axis is observation order, not elapsed wall time.

Live mode reads fixed OS files without a subprocess. The supported paths are `/proc/loadavg`, `/proc/uptime`, `/proc/meminfo`, `/sys/class/thermal/thermal_zone0/{type,temp}`, and `/sys/class/power_supply/BAT0/{type,capacity}`. File reads are bounded. A missing, malformed, out-of-range or incompatible source stays null; there is no synthetic fallback. This is not a general hardware discovery service.

The [Linux proc documentation](https://docs.kernel.org/filesystems/proc.html) describes load, uptime and memory fields. Memory `kB` values are converted with a factor of 1024, and the UI explicitly uses GiB. Load is a one-minute load average, not a CPU percentage. Available memory must not exceed total. The thermal reader requires a CPU/SoC/BCM zone type and converts millidegrees to Celsius. BAT0 must identify as a Battery and supply a percentage from 0 to 100. Filesystem totals use Python's `shutil.disk_usage` for the app's filesystem, without exposing its actual directory, hostname or process IDs.

Tests use controlled Linux-file fixtures plus actual local HTTP requests. JSON Schema checks validate endpoint responses against the reviewed [OpenAPI contract](api/openapi.json). Fixtures do not prove a real Raspberry Pi sensor driver, boot or workload.

## Energy estimate

Let capacity be `C` Wh, conversion efficiency `e`, reserve fraction `r`, and constant output load `P` W. Full output energy is `C × e`; usable output energy is `C × e × (1 − r)`. Corresponding model runtimes are output energy divided by `P`. Reserve is applied to energy, not subtracted from an invented state of charge. Nominal supply headroom is declared source watts minus load watts; it is a separate comparison.

The sample capacity, efficiency and load are declarations. No battery, converter or workload was measured. Voltage drop, peak current, ageing, ambient temperature, conversion behaviour and shutdown limits are absent. Model runtime does not represent remaining charge or guarantee portable-source compatibility.

## Enclosure and official dimensions

The [official Raspberry Pi 4 mechanical drawing](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf) supplies its 85 × 56 mm board outline and 58 × 49 mm mounting pattern. The [official Touch Display 2 guide](https://www.raspberrypi.com/documentation/accessories/touch-display-2.html) supplies the selected **7-inch** display outline and viewing area. In landscape, these are 189.5 × 120 × 15 mm and 155.5 × 88 mm. Other sizes are not interchangeable with this enclosure.

The implementation is original parameterised geometry, not copied CAD. The Pi uses the manufacturer's display mounts. The enclosure model checks minimum walls, display margins, internal allowance, hole bounds and frame/post separation. SVG geometry uses physical millimetres; OpenSCAD source offers shell, face and retainer selections. The 54 mm component/cable allowance is explicit bookkeeping, not a complete CAD assembly or a measured stack. See [assembly checks](../hardware/ASSEMBLY.md).

No OpenSCAD engine was run, no mesh was certified, and nothing was printed or fitted. Vents do not prove cooling; nominal clearances do not prove retention or manufacturability. The cover is concept art. The SVG is actual generated source output, with annotation and guide lines that are not manufacturing toolpaths.

## Setup workflow

`prepare` generates text files only. It does not invoke a shell, install packages, flash media, enable a service, change networking or reboot. The target path is a fixed `/home/USERNAME/cyberdeck`, with a strict simple username. This template must be adapted if the actual target layout differs.

The user service follows [systemd.service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html). It is wanted by the user's default target without ordering itself after that same target; [systemd.target](https://www.freedesktop.org/software/systemd/man/latest/systemd.target.html) explains the relevant target ordering. The optional kiosk fragment follows the [official Raspberry Pi labwc/Chromium workflow](https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/). Append it to a backed-up target configuration; do not replace existing autostart content. Actual target installation and boot remain unverified.

## Reproduction boundary

`scripts/reproduce.py` runs the real CLI, generates exclusive temporary bundles, hashes source and outputs, and checks 11 recorded artifacts byte-for-byte. It does not store live host metrics or alter the OS. `--write` refreshes those artifacts intentionally after source review. The evidence is a repeatable software/model run, not a hardware demonstration.
