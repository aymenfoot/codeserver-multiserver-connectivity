# ORTA Storage Audit and Cleanup

Audit performed: 2026-11-20
ORTA workspace: `/home/coder/workspace/ORTA/`

## A. Disk measurements

| Measurement | Before cleanup | After cleanup |
|-------------|---------------|---------------|
| Root filesystem free | 6.0 GiB | 6.0 GiB |
| Root filesystem use | 85% | 85% |
| ORTA workspace total | 860 KiB | 860 KiB (bytecode removal did not change `du -sh` block rounding) |

Note: `du -sh` reports in 4 KiB block units; removing ~216 KiB of bytecode caches did not change the rounded workspace size. The meaningful recovery is the removal of regenerable bytecode, not a large change in `df` free space (dominated by the overlay image and unrelated workspace content under `/home/coder` at 27 GiB).

## B. Largest ORTA directories (after cleanup)

| Directory | Size | Contents |
|-----------|------|----------|
| storage/ | 264 KiB | orta.db (200 KiB), bridge.db (52 KiB) — PRESERVED |
| core/ | 228 KiB | source + alembic migration |
| bridge/ | 116 KiB | source + clients |
| docs/ | 128 KiB | 15 markdown files |
| ui/ | 80 KiB | server + static SPA |
| tests/ | 20 KiB | acceptance.py |

## C. Files removed (safe, reproducible)

| Location | Approx. size | Reason | Reproducible? |
|----------|-------------|--------|---------------|
| `core/__pycache__/` | 84 KiB | Python bytecode cache | Yes (re-import regenerates) |
| `bridge/__pycache__/` | 72 KiB | Python bytecode cache | Yes |
| `ui/__pycache__/` | 16 KiB | Python bytecode cache | Yes |
| `core/alembic/__pycache__/` | 8 KiB | Python bytecode cache | Yes |
| `core/alembic/versions/__pycache__/` | 36 KiB | Python bytecode cache | Yes |
| `core/logs/` | 0 B | Empty log directory | N/A (left in place, empty) |

Total removed: ~216 KiB of bytecode caches only.

## D. Files recommended for removal (NOT removed)

None. No additional disposable files were identified that are safe to remove without risk.

## E. Preservation rules honored

The following were NOT deleted or touched:
- ORTA source code (core/, bridge/, ui/, tests/)
- Project documentation (docs/)
- Configuration templates (config/, compose/ — empty, to be populated)
- Database files and contents (storage/orta.db, storage/bridge.db) — REAL DATA preserved
- User data, collected documents, evidence, indexes
- Persistent application storage
- Credentials or environment files (secrets/ — empty)
- Deployment assets (none yet)
- Test evidence (tests/acceptance.py)
- Logs directory (core/logs/ — empty, preserved)

No broad destructive commands were run (no recursive filesystem cleanup, no Docker volume pruning, no database resets). No Docker volumes or application storage were deleted.

## F. Cleanup verification

- ORTA workspace intact after cleanup (all directories and files present).
- Databases intact (orta.db 200 KiB, bridge.db 52 KiB).
- No `__pycache__` or `*.pyc` remain under ORTA.
- No uncertain files were deleted.
