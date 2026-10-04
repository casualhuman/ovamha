"""Women's register on this device (decision 9: Ovamha creates its own woman ID).

At first contact Ovamha creates a woman ID (UUID, the internal key) and a short
card code the worker writes on her ANC card. On later visits the worker types the
card code to find her. No name, phone number or national ID is stored here.

Card code: 5 random characters + 1 check character (weighted mod 31 over an alphabet
without look-alikes 0/O, 1/I/L), shown as "K7P-3QZ". A single wrong or swapped
character is caught before any lookup.

Stored in OVAMHA_DATA (default ~/.ovamha/registry.json), never in the repo.
"""
from __future__ import annotations

import json
import os
import secrets
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # 31 characters
N = len(ALPHABET)


def _path() -> Path:
    return Path(os.environ.get("OVAMHA_DATA", Path.home() / ".ovamha")) / "registry.json"


def check_char(body: str) -> str:
    """Weighted check modulo 31 (prime): sum of (position x value) over all 6 characters is 0 mod 31.

    Because 31 is prime and the weights 1..6 differ, every single wrong character
    and every swap of two neighbouring characters changes the sum, so it is caught.
    """
    total = sum((i + 1) * ALPHABET.index(ch) for i, ch in enumerate(body))
    return ALPHABET[(-total * pow(6, -1, N)) % N]


def normalise(code: str) -> str:
    return "".join(ch for ch in (code or "").upper() if ch.isalnum()).replace("O", "0").replace("I", "1")


def is_valid(code: str) -> bool:
    c = normalise(code)
    return len(c) == 6 and all(ch in ALPHABET for ch in c) and check_char(c[:5]) == c[5]


def display(code: str) -> str:
    c = normalise(code)
    return f"{c[:3]}-{c[3:]}"


def new_code() -> str:
    body = "".join(secrets.choice(ALPHABET) for _ in range(5))
    return body + check_char(body)


@dataclass
class Woman:
    woman_id: str
    card_code: str
    created_at: str
    created_by: str
    visits: int = 0
    last_visit: str | None = None


def _load() -> dict[str, dict]:
    p = _path()
    return json.loads(p.read_text()) if p.exists() else {}


def _save(data: dict) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(p)


def register(worker_id: str) -> Woman:
    data = _load()
    code = new_code()
    while code in data:
        code = new_code()
    w = Woman(str(uuid.uuid4()), code, datetime.now(timezone.utc).replace(microsecond=0).isoformat(), worker_id)
    data[code] = asdict(w)
    _save(data)
    return w


def find(code: str) -> tuple[Woman | None, str]:
    c = normalise(code)
    if len(c) != 6:
        return None, "A card number has 6 characters, like K7P-3QZ."
    if not is_valid(c):
        return None, "That card number has a typo. Please check it on her card."
    rec = _load().get(c)
    if not rec:
        return None, "No woman with this card number on this device. If it is her first visit here, choose First visit."
    return Woman(**rec), ""


def record_visit(code: str) -> None:
    data = _load()
    c = normalise(code)
    if c in data:
        data[c]["visits"] += 1
        data[c]["last_visit"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        _save(data)
