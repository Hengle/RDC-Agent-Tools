from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_catalog_has_unique_tools_and_declared_count() -> None:
    catalog = ROOT / "spec" / "tool_catalog.json"
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    tools = payload.get("tools", [])
    names = [str(t.get("name", "")).strip() for t in tools]
    declared_count = int(payload.get("tool_count") or len(names))
    assert len(names) == declared_count
    assert len(set(names)) == len(names)
    assert all(n.startswith("rd.") for n in names)


def test_catalog_uses_repo_relative_source_path_and_readable_groups() -> None:
    catalog = ROOT / "spec" / "tool_catalog.json"
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    assert payload.get("source_path") == "spec/doc_extracted.txt"
    groups = payload.get("groups", {})
    assert isinstance(groups, dict)
    assert groups
    for group_name in groups:
        text = str(group_name)
        assert "?" not in text
        assert "\ufffd" not in text
        assert "Context Snapshot Tools" in text or "????" not in text


def test_required_directories_exist() -> None:
    required = [
        ROOT / "rdx",
        ROOT / "mcp",
        ROOT / "cli",
        ROOT / "spec",
        ROOT / "policy",
        ROOT / "docs",
        ROOT / "tests",
        ROOT / "binaries" / "windows" / "x64" / "pymodules",
        ROOT / "intermediate" / "runtime" / "rdx_cli",
        ROOT / "intermediate" / "artifacts",
        ROOT / "intermediate" / "pytest",
        ROOT / "intermediate" / "logs",
    ]
    for p in required:
        assert p.is_dir(), str(p)
