from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


RISKY_PATTERNS = (
    "\u93c4",
    "\u935a",
    "\u951b",
    "\u9286",
    "\u9225",
    "\ufffd",
)
SCAN_SKIP_PREFIXES = (
    ".git/",
    "intermediate/",
)
REQUIRED_DOCS = (
    "README.md",
    "docs/README.md",
    "docs/quickstart.md",
    "docs/session-model.md",
    "docs/agent-model.md",
    "docs/doc-governance.md",
    "docs/configuration.md",
    "docs/troubleshooting.md",
    "docs/tools.md",
)
REQUIRED_NAV_LINKS = {
    "README.md": (
        "docs/session-model.md",
        "docs/agent-model.md",
        "docs/doc-governance.md",
        "docs/tools.md",
    ),
    "docs/README.md": (
        "session-model.md",
        "agent-model.md",
        "doc-governance.md",
        "tools.md",
    ),
    "docs/tools.md": (
        "session-model.md",
        "agent-model.md",
    ),
    "docs/doc-governance.md": (
        "../AGENTS.md",
    ),
}
LOCAL_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def tools_root() -> Path:
    env_root = os.environ.get("RDX_TOOLS_ROOT", "").strip()
    if env_root:
        env_path = Path(env_root).expanduser().resolve()
        if env_path.is_dir():
            return env_path
    return Path(__file__).resolve().parents[1]


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        rel = path.relative_to(root).as_posix()
        if any(rel.startswith(prefix) for prefix in SCAN_SKIP_PREFIXES):
            continue
        files.append(path)
    return sorted(files)


def has_utf8_bom(data: bytes) -> bool:
    return data.startswith(b"\xef\xbb\xbf")


def scan_file(root: Path, path: Path) -> tuple[list[str], set[str]]:
    issues: list[str] = []
    seen_links: set[str] = set()
    rel = path.relative_to(root).as_posix()
    data = path.read_bytes()
    if not has_utf8_bom(data):
        issues.append(f"{rel}: missing UTF-8 BOM")

    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        issues.append(f"{rel}: invalid UTF-8 ({exc})")
        return issues, seen_links

    root_resolved = root.resolve()
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern in RISKY_PATTERNS:
            if pattern in line:
                issues.append(f"{rel}:{lineno}: suspicious mojibake fragment `{pattern}`")
                break
        for match in LOCAL_LINK_RE.finditer(line):
            target = match.group(1).strip()
            if (not target) or "://" in target or target.startswith("#") or target.startswith("mailto:"):
                continue
            base_target = target.split("#", 1)[0].strip()
            if not base_target:
                continue
            seen_links.add(base_target.replace("\\", "/"))
            resolved = (path.parent / base_target).resolve()
            try:
                resolved.relative_to(root_resolved)
            except ValueError:
                issues.append(f"{rel}:{lineno}: link escapes tools root `{target}`")
                continue
            if not resolved.exists():
                issues.append(f"{rel}:{lineno}: broken local link `{target}`")
    return issues, seen_links


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Markdown encoding health")
    parser.parse_args(argv)

    root = tools_root()
    files = iter_markdown_files(root)
    issues: list[str] = []
    link_map: dict[str, set[str]] = {}
    for rel in REQUIRED_DOCS:
        if not (root / rel).is_file():
            issues.append(f"{rel}: required markdown document is missing")
    for path in files:
        file_issues, seen_links = scan_file(root, path)
        issues.extend(file_issues)
        link_map[path.relative_to(root).as_posix()] = seen_links

    for rel, required_links in REQUIRED_NAV_LINKS.items():
        seen = link_map.get(rel, set())
        for target in required_links:
            if target not in seen:
                issues.append(f"{rel}: missing required link `{target}`")

    if issues:
        print("[md] Markdown health check failed")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print(f"[md] Markdown health check passed ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
