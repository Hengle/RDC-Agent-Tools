from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from xml.etree import ElementTree


_TOOL_NAME_RE = re.compile(r"^rd\.[a-z]+\.[a-z0-9_]+$")
_HEADING_RE = re.compile(r"^3\.\d+")
_PARAM_NAME_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_SECTION_HEADING_RE = re.compile(r"^[\u4e00-\u9fff]+[\u3001\uff0c]")
_WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
_CONTEXT_GROUP = "3.17\uff0c\u4e0a\u4e0b\u6587\u5feb\u7167\u5de5\u5177 (Context Snapshot Tools)"
_CONTEXT_TOOLS = [
    {
        "name": "rd.session.get_context",
        "group": _CONTEXT_GROUP,
        "description": "\u8bfb\u53d6\u5f53\u524d context \u5feb\u7167\uff0c\u8fd4\u56de runtime\u3001remote\u3001focus \u4e0e recent artifacts \u7684\u7ed3\u6784\u5316\u72b6\u6001\u3002",
        "parameter_raw": "",
        "returns_raw": "success (bool)<br>context_id (str)<br>runtime (dict): {session_id, capture_file_id, frame_index, active_event_id, backend_type}<br>remote (dict): {state, remote_id, origin_remote_id, endpoint, consumed_by_session_id}<br>focus (dict): {pixel?, resource_id?, shader_id?}<br>last_artifacts (list)<br>updated_at_ms (int)<br>error_message (str, \u53ef\u9009)",
    },
    {
        "name": "rd.session.update_context",
        "group": _CONTEXT_GROUP,
        "description": "\u66f4\u65b0\u5f53\u524d context \u7684 user-owned \u5b57\u6bb5\uff0c\u4f8b\u5982 focus_pixel\u3001focus_resource_id\u3001focus_shader_id \u4e0e notes\u3002",
        "parameter_raw": "key (str)<br>value (json, \u53ef\u9009): \u4f20 null \u8868\u793a\u6e05\u9664\u5bf9\u5e94 user-owned \u5b57\u6bb5",
        "returns_raw": "success (bool)<br>context_id (str)<br>runtime (dict): {session_id, capture_file_id, frame_index, active_event_id, backend_type}<br>remote (dict): {state, remote_id, origin_remote_id, endpoint, consumed_by_session_id}<br>focus (dict): {pixel?, resource_id?, shader_id?}<br>notes (str)<br>last_artifacts (list)<br>updated_at_ms (int)<br>error_message (str, \u53ef\u9009)",
    },
]


def _extract_param_names(param_line: str) -> List[str]:
    names: List[str] = []
    for piece in param_line.replace("<2>", "<br>").split("<br>"):
        piece = piece.strip()
        if not piece:
            continue
        match = _PARAM_NAME_RE.match(piece)
        if match:
            name = match.group(1)
            if name not in names:
                names.append(name)
    return names


def _text_from_node(node: ElementTree.Element) -> str:
    texts = [t.text or "" for t in node.findall(".//w:t", _WORD_NS)]
    return "".join(texts).strip()


def _iter_docx_tool_rows(docx_path: Path) -> List[Dict[str, str]]:
    with zipfile.ZipFile(docx_path) as archive:
        xml = archive.read("word/document.xml")

    root = ElementTree.fromstring(xml)
    body = root.find("w:body", _WORD_NS)
    if body is None:
        return []

    current_group = ""
    rows: List[Dict[str, str]] = []

    for elem in body:
        if elem.tag == f"{{{_WORD_NS['w']}}}p":
            text = _text_from_node(elem)
            if _HEADING_RE.match(text):
                current_group = text
            continue

        if elem.tag != f"{{{_WORD_NS['w']}}}tbl":
            continue

        for row in elem.findall("w:tr", _WORD_NS):
            cells: List[str] = []
            for cell in row.findall("w:tc", _WORD_NS):
                cells.append(_text_from_node(cell))
            if len(cells) != 4:
                continue
            name = cells[0]
            if not _TOOL_NAME_RE.fullmatch(name):
                continue
            rows.append(
                {
                    "group": current_group,
                    "name": name,
                    "description": cells[1],
                    "parameter_raw": cells[2],
                    "returns_raw": cells[3],
                },
            )

    return rows


def _iter_text_tool_rows(text_path: Path) -> List[Dict[str, str]]:
    current_group = ""
    rows: List[Dict[str, str]] = []
    lines: List[str] = []
    for raw in text_path.read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"^\d+:\s*(.*)$", raw)
        if not match:
            continue
        line = match.group(1).strip()
        if line:
            lines.append(line)

    index = 0
    while index < len(lines):
        line = lines[index]
        if _HEADING_RE.match(line):
            current_group = line
            index += 1
            continue
        if _TOOL_NAME_RE.fullmatch(line):
            name = line
            if index + 1 >= len(lines):
                break
            description = lines[index + 1].strip()
            index += 2

            param_parts: List[str] = []
            while index < len(lines):
                if lines[index].startswith("success (bool)"):
                    break
                if _TOOL_NAME_RE.fullmatch(lines[index]) or _HEADING_RE.match(lines[index]) or _SECTION_HEADING_RE.match(lines[index]):
                    break
                param_parts.append(lines[index].strip())
                index += 1

            return_parts: List[str] = []
            while index < len(lines):
                if _TOOL_NAME_RE.fullmatch(lines[index]) or _HEADING_RE.match(lines[index]) or _SECTION_HEADING_RE.match(lines[index]):
                    break
                return_parts.append(lines[index].strip())
                index += 1

            rows.append(
                {
                    "group": current_group,
                    "name": name,
                    "description": description,
                    "parameter_raw": "<br>".join(part for part in param_parts if part),
                    "returns_raw": "<br>".join(part for part in return_parts if part),
                },
            )
            continue
        index += 1

    return rows


def _normalize_source_path(source_path: Path, repo_root: Path) -> str:
    try:
        return source_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return source_path.name


def build_catalog(source_path: Path, output_path: Path) -> Dict[str, Any]:
    repo_root = output_path.resolve().parents[1]
    if source_path.suffix.lower() == ".docx":
        rows = _iter_docx_tool_rows(source_path)
    else:
        rows = _iter_text_tool_rows(source_path)

    tools: List[Dict[str, Any]] = []
    for row in rows:
        parameter_raw = row["parameter_raw"]
        tools.append(
            {
                "name": row["name"],
                "group": row["group"],
                "description": row["description"],
                "parameter_raw": parameter_raw,
                "returns_raw": row["returns_raw"],
                "param_names": _extract_param_names(parameter_raw),
            },
        )

    existing = {tool["name"] for tool in tools}
    for row in _CONTEXT_TOOLS:
        if row["name"] in existing:
            continue
        parameter_raw = row["parameter_raw"]
        tools.append(
            {
                "name": row["name"],
                "group": row["group"],
                "description": row["description"],
                "parameter_raw": parameter_raw,
                "returns_raw": row["returns_raw"],
                "param_names": _extract_param_names(parameter_raw),
            },
        )

    payload: Dict[str, Any] = {
        "source_path": _normalize_source_path(source_path, repo_root),
        "tool_count": len(tools),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "groups": dict(Counter(tool["group"] for tool in tools)),
        "tools": tools,
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build tool catalog for rdx-tools")
    parser.add_argument("--source", default="spec/doc_extracted.txt", help="Source text/docx path. Defaults to the repo-local extracted text.")
    parser.add_argument("--out", default="spec/tool_catalog.json", help="Catalog output path. Defaults to spec/tool_catalog.json.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    source_arg = Path(args.source)
    out_arg = Path(args.out)
    source = (repo_root / source_arg).resolve() if not source_arg.is_absolute() else source_arg.resolve()
    output = (repo_root / out_arg).resolve() if not out_arg.is_absolute() else out_arg.resolve()
    if not source.is_file():
        print(f"[spec] Missing source file: {source}")
        return 1

    payload = build_catalog(source, output)
    count = int(payload["tool_count"])
    print(f"[spec] Built catalog: {count} tools -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
