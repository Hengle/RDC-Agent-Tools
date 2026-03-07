from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_MOJIBAKE_FRAGMENTS = (
    "\u93c4",
    "\u935a",
    "\u951b",
    "\u9286",
    "\u9225",
    "\u95c2",
    "\u953a",
    "\u9470",
    "\ufffd",
)
_PLACEHOLDER_RE = re.compile(r"\?{4,}")


def _iter_readability_errors(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    source_path = str(payload.get("source_path") or "").strip()
    if not source_path:
        issues.append("missing source_path")
    if source_path and (":\\" in source_path or source_path.startswith("/") or source_path.startswith("\\")):
        issues.append(f"source_path must be repo-relative, got: {source_path}")

    groups = payload.get("groups")
    if not isinstance(groups, dict) or not groups:
        issues.append("groups must be a non-empty object")
    else:
        for group_name in groups:
            text = str(group_name or "")
            if _PLACEHOLDER_RE.search(text) or any(fragment in text for fragment in _MOJIBAKE_FRAGMENTS):
                issues.append(f"unreadable group label: {text}")

    for item in payload.get("tools", []):
        if not isinstance(item, dict):
            issues.append("tool entry is not an object")
            continue
        name = str(item.get("name") or "").strip()
        for field in ("group", "description", "parameter_raw", "returns_raw"):
            text = str(item.get(field) or "")
            if _PLACEHOLDER_RE.search(text) or any(fragment in text for fragment in _MOJIBAKE_FRAGMENTS):
                issues.append(f"{name}:{field} contains unreadable text")
    return issues


def main() -> int:
    root = Path(__file__).resolve().parent
    catalog_path = root / "tool_catalog.json"
    if not catalog_path.is_file():
        print(f"[spec] Missing catalog: {catalog_path}")
        return 1

    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    tools = data.get("tools", [])
    names = [str(item.get("name", "")).strip() for item in tools]
    unique = set(names)
    declared_count = int(data.get("tool_count") or len(tools))

    if len(tools) != declared_count:
        print(f"[spec] Catalog tool_count mismatch: declared {declared_count}, got {len(tools)}")
        return 2
    if len(unique) != len(names):
        print(f"[spec] Tool names must be unique: {len(unique)} unique / {len(names)} total")
        return 3
    if any(not name.startswith("rd.") for name in unique):
        print("[spec] Invalid tool name prefix found (must start with rd.)")
        return 4

    readability_issues = _iter_readability_errors(data)
    if readability_issues:
        print("[spec] Catalog readability validation failed")
        for issue in readability_issues[:20]:
            print(f"- {issue}")
        return 5

    print(f"[spec] Catalog validation passed ({len(unique)} unique rd.* tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
