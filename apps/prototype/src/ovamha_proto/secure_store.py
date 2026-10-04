"""Encryption at rest for everything Ovamha writes about a woman (architecture DEV-02, DB-02, SEC-01;
WHO ANC DAK ANC.NFXNREQ.002; MoHS HIS Policy 2021 s.3.6(c); draft Data Protection Bill 2025 s.55(4)(c)).

Files are encrypted with Fernet (AES-128-CBC + HMAC-SHA256, from the `cryptography` package).
The key comes from OVAMHA_KEY (a Fernet key) or, if unset, a device key file created on first
use at OVAMHA_DATA/device.key with owner-only permissions.

Prototype limit: a key file on the same disk protects against copied files and casual access,
not against someone who has the whole unlocked device. The Android app keeps the key in the
Android Keystore and uses the FHIR SDK's encrypted database instead.

Files written by earlier versions in plain JSON are still read, and are encrypted the next
time they are saved.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

MAGIC = b"OVAMHA1:"  # marks an encrypted file


def data_dir() -> Path:
    return Path(os.environ.get("OVAMHA_DATA", Path.home() / ".ovamha"))


def _key_file() -> Path:
    return data_dir() / "device.key"


@lru_cache(maxsize=4)
def _fernet(key_path: str, env_key: str | None) -> Fernet:
    if env_key:
        return Fernet(env_key.encode())
    p = Path(key_path)
    if not p.exists():
        _private_dir(p.parent)
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(Fernet.generate_key())
    return Fernet(p.read_bytes().strip())


def fernet() -> Fernet:
    return _fernet(str(_key_file()), os.environ.get("OVAMHA_KEY"))


def encrypt(obj) -> bytes:
    return MAGIC + fernet().encrypt(json.dumps(obj).encode())


def decrypt(blob: bytes):
    if blob.startswith(MAGIC):
        return json.loads(fernet().decrypt(blob[len(MAGIC):]))
    return json.loads(blob)  # plain JSON from an earlier version


def _private_dir(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)
    try:
        d.chmod(0o700)  # owner only
    except OSError:
        pass


def write_json(path: Path, obj) -> None:
    """Atomic, encrypted write, readable by the owner only."""
    _private_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(encrypt(obj))
    tmp.replace(path)


def read_json(path: Path, default=None):
    return decrypt(path.read_bytes()) if path.exists() else default


def append_jsonl(path: Path, obj) -> None:
    """One encrypted record per line (append-only logs)."""
    _private_dir(path.parent)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "ab") as fh:
        fh.write(encrypt(obj) + b"\n")


def read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    out = []
    for line in path.read_bytes().splitlines():
        if line.strip():
            try:
                out.append(decrypt(line))
            except (InvalidToken, ValueError):
                out.append({"unreadable": True})  # wrong key or damaged line: never crash the reader
    return out


def is_encrypted(path: Path) -> bool:
    return path.exists() and path.read_bytes().startswith(MAGIC)
