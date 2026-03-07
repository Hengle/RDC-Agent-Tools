#!/usr/bin/env python3
"""Copy runtime binaries into rdx-tools/binaries and generate manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Iterable

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from scripts._shared import ensure_within_root, resolve_repo_path, tools_root, write_text


DENY_SUFFIXES = {".pdb", ".lib", ".exp", ".ilk", ".h"}
ALLOW_PATTERNS = (
    "*.dll",
    "*.json",
)
ALLOW_PYMODULE_PATTERNS = (
    "*.pyd",
    "*.dll",
    "*.json",
)


def _tools_root() -> Path:
    return tools_root(__file__)


def _iter_allowed_files(src: Path) -> Iterable[Path]:
    for pattern in ALLOW_PATTERNS:
        for p in sorted(src.glob(pattern)):
            if p.is_file():
                yield p
    pymod = src / "pymodules"
    if pymod.is_dir():
        for pattern in ALLOW_PYMODULE_PATTERNS:
            for p in sorted(pymod.glob(pattern)):
                if p.is_file():
                    yield p


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package runtime binaries for rdx-tools")
    parser.add_argument("--source", required=True, help="Repo-relative staging directory under the rdx-tools root")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    tools_root_path = _tools_root()
    src = ensure_within_root(tools_root_path, resolve_repo_path(tools_root_path, args.source), label="runtime source")
    if not src.is_dir():
        print(f"[pack] missing source directory: {src}")
        return 1

    out_root = tools_root_path / "binaries" / "windows" / "x64"
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "pymodules").mkdir(parents=True, exist_ok=True)

    packaged: list[Path] = []
    for src_file in _iter_allowed_files(src):
        if src_file.suffix.lower() in DENY_SUFFIXES:
            continue
        rel = src_file.relative_to(src)
        dst_file = out_root / rel
        if dst_file.suffix.lower() in DENY_SUFFIXES:
            continue
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src_file, dst_file)
        except PermissionError as exc:
            if dst_file.is_file():
                print(f"[pack] locked target kept as-is: {dst_file} ({exc})")
            else:
                print(f"[pack] copy failed: {src_file} -> {dst_file} ({exc})")
                return 1
        if dst_file.is_file():
            packaged.append(dst_file)

    manifest_entries: list[dict[str, object]] = []
    for p in sorted({x.resolve() for x in packaged}):
        rel = p.relative_to(out_root).as_posix()
        manifest_entries.append(
            {
                "path": rel,
                "size": int(p.stat().st_size),
                "sha256": _sha256(p),
            },
        )

    manifest = {
        "file_count": len(manifest_entries),
        "files": manifest_entries,
    }
    manifest_path = out_root / "manifest.runtime.json"
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"[pack] wrote {manifest_path} with {len(manifest_entries)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
