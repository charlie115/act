# Legacy Optimization Tools

This directory stores historical optimization experiments and monitoring tools
that are not part of the active runtime path.

They are kept for reference, benchmarking, and migration archaeology only.

Moved here from the old top-level `services/info_core/` layout:

- `ALL_EXCHANGES_OPTIMIZED.md`
- `DEPLOYMENT_COMPLETE.md`
- `OPTIMIZATION_README.md`
- `check_optimization_status.py`
- `migrate_to_optimized.py`
- `monitor_optimization.py`
- `websocket_optimization_examples.md`

If any of these tools are needed again, promote them deliberately back into an
active workflow instead of calling them from production paths implicitly.
