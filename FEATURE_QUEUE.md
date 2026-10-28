# Feature queue

Delivered 28 October 2026: Live sensor readers reject Python-only numeric notation such as `47_500` instead of reporting it as a measured value. Invalid load, uptime, memory, thermal and battery values stay null with no source label; healthy sources still work. Temperature scaling now follows the same validated reader.

Next useful work:
- Add a read-only storage telemetry adapter for a documented target path.
- Repeat setup/kiosk checks on the actual Raspberry Pi target.

Synthetic replay, model power budgets and actual host telemetry remain distinct. Hardware acceptance remains pending.
