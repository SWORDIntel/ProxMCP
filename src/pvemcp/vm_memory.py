"""
vm_memory.py — Unified persistent knowledge store.
Stores all VM context in a single JSON file at ~/.pvemcp/memory.json
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .crypto import encrypt, decrypt

def _resolve_memory_file() -> Path:
    for env_var in ("PVEMCP_MEMORY_FILE", "VM_MCP_MEMORY_FILE"):
        val = os.getenv(env_var)
        if val:
            try:
                p = Path(val).expanduser()
                p.parent.mkdir(parents=True, exist_ok=True)
                return p
            except Exception:
                pass

    path_str = "~/.pvemcp/memory.json"
    try:
        p = Path(path_str).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        pass

    import tempfile
    p = Path(tempfile.gettempdir()) / "pvemcp" / "memory.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


_MEMORY_FILE = _resolve_memory_file()
_MAX_HISTORY = 20
_MAX_STDOUT_LEN = 400


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_record(vmid: str) -> dict[str, Any]:
    return {
        "vmid": vmid,
        "notes": "",
        "paths": {},
        "services": [],
        "containers": [],
        "env": {},
        "tags": [],
        "secrets": {},
        "history": [],
        "created_at": _now(),
        "updated_at": _now(),
    }


def _load_all() -> dict[str, dict[str, Any]]:
    if not _MEMORY_FILE.exists():
        return {}
    try:
        with _MEMORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_all(data: dict[str, dict[str, Any]]) -> None:
    _MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _MEMORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_vm_memory(vmid: str) -> dict[str, Any]:
    """Load the memory record for a VM."""
    data = _load_all()
    record = data.get(str(vmid))
    if not record:
        return _empty_record(vmid)
    
    # Back-fill missing keys
    defaults = _empty_record(vmid)
    for key, default in defaults.items():
        record.setdefault(key, default)
    return record


def save_vm_memory(record: dict[str, Any]) -> None:
    """Persist a memory record to the unified store."""
    vmid = str(record.get("vmid", "unknown"))
    record["updated_at"] = _now()
    data = _load_all()
    data[vmid] = record
    _save_all(data)


def memory_context_summary(vmid: str) -> dict[str, Any]:
    """Return a compact summary of known VM context."""
    rec = load_vm_memory(vmid)
    return {
        "vmid": vmid,
        "notes": rec["notes"] or None,
        "known_paths": rec["paths"] or None,
        "known_services": rec["services"] or None,
        "known_containers": rec["containers"] or None,
        "tags": rec["tags"] or None,
        "env_hints": rec["env"] or None,
        "last_updated": rec["updated_at"],
    }


def record_history(vmid: str, cmd: str, stdout: str, ok: bool) -> None:
    """Append a command result snippet to the VM's history."""
    rec = load_vm_memory(vmid)
    entry = {
        "ts": _now(),
        "cmd": cmd[:200],
        "ok": ok,
        "stdout_snippet": stdout[:_MAX_STDOUT_LEN],
    }
    history: list[dict[str, Any]] = rec.get("history", [])
    history.append(entry)
    rec["history"] = history[-_MAX_HISTORY:]
    save_vm_memory(rec)


def annotate_vm(
    vmid: str,
    *,
    notes: str | None = None,
    paths: dict[str, str] | None = None,
    services: list[str] | None = None,
    containers: list[str] | None = None,
    env: dict[str, str] | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Merge new knowledge into a VM's memory record."""
    rec = load_vm_memory(vmid)
    if notes is not None:
        rec["notes"] = notes
    if paths:
        rec["paths"].update(paths)
    if services:
        existing = set(rec["services"])
        existing.update(services)
        rec["services"] = sorted(existing)
    if containers:
        existing = set(rec["containers"])
        existing.update(containers)
        rec["containers"] = sorted(existing)
    if env:
        rec["env"].update(env)
    if tags:
        existing = set(rec["tags"])
        existing.update(tags)
        rec["tags"] = sorted(existing)
    save_vm_memory(rec)
    return rec


def annotate_vm_secret(vmid: str, key: str, value: str) -> None:
    """Store an encrypted secret in VM memory."""
    rec = load_vm_memory(vmid)
    if "secrets" not in rec:
        rec["secrets"] = {}
    rec["secrets"][key] = encrypt(value)
    save_vm_memory(rec)


def get_vm_secret(vmid: str, key: str) -> str | None:
    """Retrieve and decrypt a secret from VM memory."""
    rec = load_vm_memory(vmid)
    token = rec.get("secrets", {}).get(key)
    if token:
        return decrypt(token)
    return None


def list_all_vm_memories() -> list[dict[str, Any]]:
    """Return a summary listing of all stored VM memory records."""
    data = _load_all()
    summaries = []
    for vmid, rec in sorted(data.items()):
        summaries.append({
            "vmid": vmid,
            "tags": rec.get("tags", []),
            "notes_preview": (rec.get("notes") or "")[:80],
            "known_paths": list(rec.get("paths", {}).keys()),
            "known_services": rec.get("services", []),
            "known_containers": rec.get("containers", []),
            "updated_at": rec.get("updated_at"),
        })
    return summaries

def clear_vm_memory(vmid: str) -> bool:
    """Remove a VM's record from the unified store."""
    data = _load_all()
    vmid_s = str(vmid)
    if vmid_s in data:
        del data[vmid_s]
        _save_all(data)
        return True
    return False
