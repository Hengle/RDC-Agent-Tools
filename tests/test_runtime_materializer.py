from __future__ import annotations

import hashlib
import json
from pathlib import Path

from rdx import runtime_materializer


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _prepare_source(tmp_path: Path) -> Path:
    bin_root = tmp_path / "tools" / "binaries" / "windows" / "x64"
    pymod_root = bin_root / "pymodules"
    pymod_root.mkdir(parents=True, exist_ok=True)
    files = {
        "renderdoc.dll": b"renderdoc-dll",
        "renderdoc.json": b"{}",
        "pymodules/renderdoc.pyd": b"renderdoc-pyd",
    }
    entries = []
    for rel, content in files.items():
        path = bin_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        entries.append(
            {
                "path": rel.replace("\\", "/"),
                "size": len(content),
                "sha256": _sha256(path),
            }
        )
    (bin_root / "manifest.runtime.json").write_text(
        json.dumps({"file_count": len(entries), "files": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return bin_root


def test_materialize_runtime_is_stable_and_copies_files(tmp_path: Path, monkeypatch) -> None:
    source_root = _prepare_source(tmp_path)
    cache_root = tmp_path / "cache"

    monkeypatch.setattr(runtime_materializer, "binaries_root", lambda: source_root)
    monkeypatch.setattr(runtime_materializer, "pymodules_dir", lambda: source_root / "pymodules")
    monkeypatch.setattr(runtime_materializer, "worker_cache_dir", lambda: cache_root)

    first = runtime_materializer.materialize_runtime()
    second = runtime_materializer.materialize_runtime()

    assert first.runtime_id == second.runtime_id
    assert first.cache_root == second.cache_root
    assert (first.binaries_dir / "renderdoc.dll").read_bytes() == b"renderdoc-dll"
    assert (first.pymodules_dir / "renderdoc.pyd").read_bytes() == b"renderdoc-pyd"
    assert (first.cache_root / ".materialized.json").is_file()
