"""Offline health-worker login: username + PIN, checked on the device.

PINs are stored only as salted PBKDF2-SHA256 hashes in a local JSON file
(content/demo-users.json for the demo; OVAMHA_USERS to override). No network
is used. After MAX_ATTEMPTS wrong PINs, the account is locked for LOCK_SECONDS.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

USERS_FILE = Path(os.environ.get("OVAMHA_USERS", Path(__file__).resolve().parents[4] / "content" / "demo-users.json"))
ITERATIONS = 200_000
MAX_ATTEMPTS = 5
LOCK_SECONDS = 300

_failures: dict[str, list[float]] = {}


@dataclass
class Worker:
    worker_id: str
    display_name: str  # e.g. "Nurse Fati"
    role: str
    facility: str
    languages: list[str]
    facility_level: str = "CHP"


def hash_pin(pin: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt), ITERATIONS).hex()
    return salt, digest


def _load() -> list[dict]:
    if not USERS_FILE.exists():
        return []
    return json.loads(USERS_FILE.read_text())["users"]


def workers() -> list[Worker]:
    return [Worker(u["worker_id"], u["display_name"], u["role"], u["facility"], u.get("languages", ["en"])) for u in _load()]


def login(username: str, pin: str) -> tuple[Worker | None, str]:
    """Returns (worker, "") on success, or (None, reason).

    Unknown usernames and wrong PINs give the same message, so the screen never
    reveals which usernames exist on this device.
    """
    key = (username or "").strip().lower()
    now = time.time()
    recent = [t for t in _failures.get(key, []) if now - t < LOCK_SECONDS]
    _failures[key] = recent
    if len(recent) >= MAX_ATTEMPTS:
        return None, f"Too many wrong tries. Try again in {int((LOCK_SECONDS - (now - recent[0])) / 60) + 1} minutes."
    user = next((u for u in _load() if u.get("username", "").lower() == key), None)
    salt = user["pin_salt"] if user else "00" * 16
    _, digest = hash_pin(pin or "", salt)  # hash even for unknown users: same timing either way
    if user is None or not hmac.compare_digest(digest, user["pin_hash"]):
        _failures[key].append(now)
        left = MAX_ATTEMPTS - len(_failures[key])
        return None, f"Username or PIN is wrong. {left} tries left." if left else "Too many wrong tries. Locked for 5 minutes."
    _failures.pop(key, None)
    return Worker(user["worker_id"], user["display_name"], user["role"], user["facility"], user.get("languages", ["en"]),
                  user.get("facility_level", "CHP")), ""
