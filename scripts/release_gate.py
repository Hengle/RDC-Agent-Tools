#!/usr/bin/env python3
"""Release gate checks for standalone rdx-tools package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


REQUIRED_DIRS = [
    "rdx",
    "mcp",
    "cli",
    "spec",
    "policy",
    "docs",
    "tests",
    "binaries/windows/x64/pymodules",
    "intermediate/runtime/rdx_cli",
    "intermediate/artifacts",
    "intermediate/pytest",
    "intermediate/logs",
]

CURRENT_REPORTS = [
    "intermediate/logs/rdx_bat_command_smoke.md",
    "intermediate/logs/tool_contract_report.md",
    "intermediate/logs/rdx_smoke_issues_blockers.md",
    "intermediate/logs/rdx_smoke_detailed_report.md",
]

LEGACY_REPORT_SUITES = {
    "native-smoke": [
        "intermediate/logs/native_smoke_report.md",
        "intermediate/logs/tool_contract_report.md",
    ],
}

BANNED_SUFFIXES = {".pdb", ".lib", ".exp", ".ilk", ".h"}
TEXT_SCAN_SUFFIXES = {
    ".bat",
    ".cmd",
    ".ini",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
SCAN_SKIP_PREFIXES = {
    ".git/",
    "intermediate/",
}


def _tools_root() -> Path:
    env_root = os.environ.get("RDX_TOOLS_ROOT", "").strip()
    if env_root:
        env_path = Path(env_root).expanduser().resolve()
        if env_path.is_dir():
            return env_path
    return Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = proc.returncode == 0
    detail = (proc.stdout or "") + (proc.stderr or "")
    return ok, detail.strip()


def _python_no_match(pattern: str, cwd: Path) -> tuple[bool, str]:
    compiled = re.compile(pattern)
    for path in cwd.rglob("*"):
        if path.is_dir():
            continue
        rel = str(path.relative_to(cwd)).replace("\\", "/")
        if any(rel.startswith(prefix) for prefix in SCAN_SKIP_PREFIXES):
            continue
        if compiled.search(rel):
            return False, rel
        if path.suffix.lower() not in TEXT_SCAN_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if compiled.search(line):
                return False, f"{rel}:{lineno}: {line.strip()}"
    return True, ""


def _rg_no_match(pattern: str, cwd: Path) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            [
                "rg",
                "-n",
                "--glob",
                "!.git/**",
                "--glob",
                "!intermediate/**",
                pattern,
                ".",
            ],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        ok, detail = _python_no_match(pattern, cwd)
        if ok:
            return True, ""
        return False, f"(python fallback after {exc.__class__.__name__}) {detail}"
    # rg: 0=matched, 1=no match, 2=error
    if proc.returncode == 1:
        return True, ""
    if proc.returncode == 0:
        return False, (proc.stdout or "").strip()
    ok, detail = _python_no_match(pattern, cwd)
    if ok:
        return True, ""
    rg_detail = ((proc.stdout or "") + (proc.stderr or "")).strip()
    prefix = f"(python fallback after rg exit {proc.returncode}: {rg_detail[:200]})"
    return False, f"{prefix} {detail}".strip()


def _check_manifest(root: Path) -> tuple[bool, str]:
    manifest_path = root / "binaries" / "windows" / "x64" / "manifest.runtime.json"
    if not manifest_path.is_file():
        return False, f"missing manifest: {manifest_path}"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"invalid manifest json: {exc}"
    files = payload.get("files")
    if not isinstance(files, list):
        return False, "manifest files field is missing or invalid"
    bin_root = root / "binaries" / "windows" / "x64"
    for entry in files:
        if not isinstance(entry, dict):
            return False, "manifest entry is not an object"
        rel = str(entry.get("path") or "").strip()
        size = entry.get("size")
        sha = str(entry.get("sha256") or "").strip().lower()
        if not rel:
            return False, "manifest entry has empty path"
        p = bin_root / rel
        if p.suffix.lower() in BANNED_SUFFIXES:
            return False, f"banned file suffix in manifest: {rel}"
        if not p.is_file():
            return False, f"missing runtime file: {rel}"
        if int(p.stat().st_size) != int(size):
            return False, f"size mismatch for {rel}"
        if _sha256(p) != sha:
            return False, f"sha256 mismatch for {rel}"
    return True, f"validated {len(files)} runtime files"


def _check_reports(root: Path) -> tuple[bool, str]:
    current_missing = [rel for rel in CURRENT_REPORTS if not (root / rel).is_file()]
    if not current_missing:
        return True, "using current smoke reports"

    for suite_name, report_paths in LEGACY_REPORT_SUITES.items():
        missing = [rel for rel in report_paths if not (root / rel).is_file()]
        if not missing:
            return True, f"using legacy report suite: {suite_name}"

    detail_parts = [f"missing current reports: {', '.join(current_missing)}"]
    for suite_name, report_paths in LEGACY_REPORT_SUITES.items():
        missing = [rel for rel in report_paths if not (root / rel).is_file()]
        detail_parts.append(f"legacy suite {suite_name} missing: {', '.join(missing)}")
    return False, " | ".join(detail_parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run release gate checks")
    parser.add_argument("--report", default="intermediate/logs/release_gate_report.md")
    args = parser.parse_args(argv)

    root = _tools_root()
    results: list[tuple[str, bool, str]] = []

    # structure
    for rel in REQUIRED_DIRS:
        p = root / rel
        results.append((f"structure:{rel}", p.is_dir(), "" if p.is_dir() else f"missing {p}"))

    # reference gates
    ext_pattern = "extens" + r"ions[/\\]"
    dbg_pattern = "debug" + "-agent|frame" + "works"
    ok_ext, out_ext = _rg_no_match(ext_pattern, cwd=root)
    results.append(("refs:no_extensions_path", ok_ext, out_ext))
    ok_fw, out_fw = _rg_no_match(dbg_pattern, cwd=root)
    results.append(("refs:no_debug_fw_terms", ok_fw, out_fw))

    # manifest
    ok_manifest, msg_manifest = _check_manifest(root)
    results.append(("manifest:integrity", ok_manifest, msg_manifest))

    # entry checks
    ok_mcp_help, mcp_help = _run([sys.executable, "mcp/run_mcp.py", "--help"], cwd=root)
    results.append(("entry:python mcp/run_mcp.py --help", ok_mcp_help, mcp_help))
    ok_cli_help, cli_help = _run([sys.executable, "cli/run_cli.py", "--help"], cwd=root)
    results.append(("entry:python cli/run_cli.py --help", ok_cli_help, cli_help))
    ok_bat_help, bat_help = _run(["cmd", "/c", "rdx.bat --help"], cwd=root)
    results.append(("entry:rdx.bat --help", ok_bat_help, bat_help))
    ok_md_health, md_health = _run([sys.executable, "scripts/check_markdown_health.py"], cwd=root)
    results.append(("docs:markdown-health", ok_md_health, md_health))

    # reports
    ok_reports, report_detail = _check_reports(root)
    results.append(("reports:smoke-suite", ok_reports, report_detail))

    ok_all = all(item[1] for item in results)

    report_path = (root / args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Release Gate Report", ""]
    for name, ok, detail in results:
        lines.append(f"- {'PASS' if ok else 'FAIL'} `{name}`")
        if detail:
            lines.append(f"  - {detail.strip()[:5000]}")
    lines.append("")
    lines.append(f"Overall: {'PASS' if ok_all else 'FAIL'}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[gate] report: {report_path}")
    print(f"[gate] overall: {'PASS' if ok_all else 'FAIL'}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
