# Contributing

Runtime is Python standard library only. Use Python 3.11+; create a development virtual environment and install `requirements-dev.txt` for JSON Schema contract tests. Node 22+ runs the small UI-model suite. Run Python unit tests, Node tests, `python3 scripts/reproduce.py`, and a browser review before a pull request.

Keep source boundaries clear. OS readers remain read-only and bounded. Unsupported live sources must remain null. Never hide missing sensors with replay values. The browser must retain visible source labels, history gaps, sample-order semantics, stale states, and distinct energy/charge concepts.

Update the OpenAPI/data contract before changing an endpoint. Test invalid query syntax and repeated fields as well as valid output. Add focused tests for model units, reserve denominators, dimensions, minimum features, file ownership, and setup safety. Do not turn the local viewer into a command console or hosted multi-user service without a separate design.

After a reviewed source change, use `python3 scripts/reproduce.py --write` to update generated artifacts, inspect their changes, then run reproduction without `--write`. `hardware/BOM.csv` is the canonical parts list; the public copy is generated and compared by that script.

Keep hardware evidence separate. Record a real target, software versions, instruments, conditions and measured results before closing assembly or performance checks. Do not call an unrendered source printable, an illustrative battery tested, or a generated cover a physical build. Do not backdate work or infer project age from repository history.

Submit the problem, resulting behaviour, actual validation, and remaining limits. Keep dependencies, caches, credentials, personal host details and local output directories out of Git.
