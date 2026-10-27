# Security

This is a local read-only workbench, not an authenticated multi-user service. The server binds to 127.0.0.1, requires a matching loopback Host, rejects writes, and serves only fixed public assets. Requests, calculator values, config reads, and asset reads are bounded. The browser loads no external scripts, fonts or analytics and sends no telemetry. Keep it on a trusted local machine.

Live mode reads fixed OS metric paths. It does not scan a network, expose a terminal, invoke subprocesses, or control GPIO. Missing fields stay null. Reports expose aggregate metrics without hostname, process IDs or file paths. The setup command writes new template files only; a person must review and apply them on the target. It does not change authentication or open network access.

The energy calculator is not battery telemetry or an electrical approval. No battery-cell, charging or mains circuit is designed here. Enclosure source is an unbuilt prototype; CAD rendering, fit, retention and thermal/electrical validation remain pending.

Use GitHub private vulnerability reporting if available. Otherwise open a general issue requesting a private reporting route. Do not post credentials or personal host data. No response-time guarantee is offered.
