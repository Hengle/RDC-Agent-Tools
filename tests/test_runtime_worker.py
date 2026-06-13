from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

from rdx.daemon import worker as daemon_worker


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _prepare_runtime_source(tmp_path: Path) -> Path:
    bin_root = tmp_path / "source" / "binaries" / "windows" / "x64"
    pymod_root = bin_root / "pymodules"
    pymod_root.mkdir(parents=True, exist_ok=True)
    files = {
        "renderdoc.dll": b"fake-runtime-dll",
        "renderdoc.json": b"{}",
        "pymodules/renderdoc.pyd": b"fake-runtime-pyd",
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


def test_worker_uses_source_runtime_directly(tmp_path: Path, monkeypatch) -> None:
    source_root = _prepare_runtime_source(tmp_path)
    monkeypatch.setenv("RDX_TOOLS_ROOT", str(ROOT))
    monkeypatch.setattr(daemon_worker, "binaries_root", lambda: source_root)
    monkeypatch.setattr(daemon_worker, "pymodules_dir", lambda: source_root / "pymodules")

    captured: dict[str, object] = {}

    class _FakeProcess:
        pid = 12345
        stdin = io.StringIO()
        stdout = io.StringIO('{"kind":"ready"}\n')

        def poll(self):  # type: ignore[no-untyped-def]
            return None

    def _fake_popen(cmd, **kwargs):  # type: ignore[no-untyped-def]
        captured["cmd"] = cmd
        captured["env"] = kwargs["env"]
        return _FakeProcess()

    monkeypatch.setattr(daemon_worker.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(daemon_worker.RuntimeWorkerProcess, "_save_state", lambda self: None)

    worker = daemon_worker.RuntimeWorkerProcess(context_id="pytest-worker")
    worker._spawn()
    try:
        env = captured["env"]
        assert isinstance(env, dict)
        assert env["RDX_RUNTIME_DLL_DIR"] == str(source_root.resolve())
        assert env["RDX_RENDERDOC_PATH"] == str((source_root / "pymodules").resolve())
        assert env["RDX_WORKER_SOURCE_MANIFEST"] == str((source_root / "manifest.runtime.json").resolve())

        worker_state = worker.snapshot()
        assert worker_state["binaries_dir"] == str(source_root.resolve())
        assert worker_state["pymodules_dir"] == str((source_root / "pymodules").resolve())
        removed_fields = {"runtime_" + "id", "cache_" + "root"}
        assert removed_fields.isdisjoint(worker_state)
    finally:
        worker._proc = None
        worker._runtime = None
