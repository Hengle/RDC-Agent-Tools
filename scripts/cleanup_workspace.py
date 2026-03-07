#!/usr/bin/env python3
"""Safe cleanup helper for rdx-tools temporary files."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from scripts._shared import tools_root


TARGET_NAMES = {".venv", ".pytest_cache", "__pycache__"}
TARGET_SUFFIXES = {".pyc"}
TARGET_GLOBS = ("*.egg-info",)


def _tools_root() -> Path:
    return tools_root(__file__)


def _collect_targets(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*"):
        if p.name in TARGET_NAMES:
            out.append(p)
            continue
        if p.suffix.lower() in TARGET_SUFFIXES:
            out.append(p)
            continue
    for pattern in TARGET_GLOBS:
        for p in root.rglob(pattern):
            out.append(p)
    dedup = sorted({p.resolve() for p in out})
    safe: list[Path] = []
    root_resolved = root.resolve()
    for p in dedup:
        try:
            p.relative_to(root_resolved)
        except Exception:
            continue
        safe.append(p)
    return safe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean temporary files inside rdx-tools")
    parser.add_argument("--apply", action="store_true", help="Delete after printing candidate list")
    args = parser.parse_args(argv)

    root = _tools_root()
    targets = _collect_targets(root)
    print("[cleanup] candidates")
    for t in targets:
        print(str(t))

    removed = 0
    if args.apply:
        for t in targets:
            if t.is_dir():
                shutil.rmtree(t, ignore_errors=True)
                removed += 1
            else:
                try:
                    t.unlink(missing_ok=True)
                    removed += 1
                except Exception:
                    pass
        print(f"[cleanup] removed {removed} paths")
    else:
        print("[cleanup] dry-run only (use --apply to delete)")

    summary = {
        "ok": True,
        "applied": bool(args.apply),
        "root": str(root),
        "target_count": len(targets),
        "removed_count": removed,
        "targets": [str(path) for path in targets],
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
