from __future__ import annotations

import json
from pathlib import Path

from rdx.daemon import client as daemon_client


def _configure_runtime_dir(monkeypatch, tmp_path: Path) -> None:
    state_dir = tmp_path / "runtime"
    state_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(daemon_client, "STATE_DIR", state_dir)
    monkeypatch.setattr(daemon_client, "DAEMON_STATE_FILE", state_dir / "daemon_state.json")
    monkeypatch.setattr(daemon_client, "SESSION_STATE_FILE", state_dir / "session_state.json")


def test_session_state_isolated_by_context(monkeypatch, tmp_path: Path) -> None:
    _configure_runtime_dir(monkeypatch, tmp_path)

    daemon_client.save_session_state({"session_id": "sess-default"}, context="default")
    daemon_client.save_session_state({"session_id": "sess-custom"}, context="demo ctx")

    default_path = daemon_client.session_state_path("default")
    custom_path = daemon_client.session_state_path("demo ctx")

    assert default_path.name == "session_state.json"
    assert custom_path.name == "session_state_demo_ctx.json"
    assert daemon_client.load_session_state(context="default")["session_id"] == "sess-default"
    assert daemon_client.load_session_state(context="demo ctx")["session_id"] == "sess-custom"


def test_cleanup_stale_daemon_state_removes_dead_pid(monkeypatch, tmp_path: Path) -> None:
    _configure_runtime_dir(monkeypatch, tmp_path)

    state_path = daemon_client.STATE_DIR / "daemon_state_dead.json"
    state_path.write_text(
        json.dumps(
            {
                "context_id": "dead",
                "daemon_context": "dead",
                "pipe_name": "pipe-dead",
                "token": "token-dead",
                "pid": 99999,
                "started_at": "2026-03-06T00:00:00+00:00",
                "last_activity_at": "2026-03-06T00:00:00+00:00",
                "owner_pid": 0,
                "lease_timeout_seconds": 120,
                "idle_timeout_seconds": 900,
                "attached_clients": [],
            },
        ),
        encoding="utf-8",
    )
    daemon_client.save_session_state({"session_id": "stale"}, context="dead")

    monkeypatch.setattr(daemon_client, "_is_process_running", lambda pid: False)

    cleaned = daemon_client.cleanup_stale_daemon_states()

    assert "daemon_state_dead.json" in cleaned["state_files"]
    assert "session_state_dead.json" in cleaned["session_files"]
    assert not state_path.exists()
    assert not daemon_client.session_state_path("dead").exists()


def test_clear_context_without_daemon_clears_session(monkeypatch, tmp_path: Path) -> None:
    _configure_runtime_dir(monkeypatch, tmp_path)

    daemon_client.save_session_state({"session_id": "sess-x"}, context="ctx-x")
    ok, message, details = daemon_client.clear_context("ctx-x")

    assert ok is True
    assert "context cleared" in message
    assert details["state"] == {}
    assert not daemon_client.session_state_path("ctx-x").exists()
