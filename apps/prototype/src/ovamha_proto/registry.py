"""Women's register on this device (decision 9: Ovamha creates its own woman ID).

At first contact Ovamha creates a woman ID (UUID, the internal key) and a short
card code the worker writes on her ANC card. On later visits the worker types the
card code to find her. Stored on this device: the ANC.A4 registration details (name,
community, optional phone and emergency contact), her date of birth (exact or estimated),
the ANC.B6 first-contact profile and, with consent, that a national ID card was shown.
The national ID number is never stored.

Card code: 5 random characters + 1 check character (weighted mod 31 over an alphabet
without look-alikes 0/O, 1/I/L), shown as "K7P-3QZ". A single wrong or swapped
character is caught before any lookup.

Stored in OVAMHA_DATA (default ~/.ovamha/registry.json), never in the repo, encrypted at rest (secure_store).
"""
from __future__ import annotations

import json
import os
import secrets
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import secure_store

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
    episode_id: str = ""  # the current pregnancy (FHIR EpisodeOfCare)
    national_id: dict | None = None  # consented check only: document shown, never the number (ID-03, ID-04)
    birth_date: str | None = None  # "YYYY-MM-DD" when known; "YYYY" when estimated from her age
    birth_date_estimated: bool = False
    details: dict = field(default_factory=dict)  # ANC.A4 registration details (name, community, phone, contacts...)
    profile: dict = field(default_factory=dict)  # ANC.B6 first-contact profile answers
    profile_at: str | None = None
    privacy_notice_at: str | None = None  # when the privacy notice was read to her (draft DP Bill 2025 s.27(3))
    history: list = field(default_factory=list)  # one summary per finished check, oldest first (see visit_summary)


def _woman(rec: dict) -> Woman:
    """Build a Woman from a stored record, ignoring fields from older versions."""
    known = Woman.__dataclass_fields__
    return Woman(**{k: v for k, v in rec.items() if k in known})


def _load() -> dict[str, dict]:
    return secure_store.read_json(_path(), {})


def _save(data: dict) -> None:
    secure_store.write_json(_path(), data)  # encrypted at rest (DEV-02)


def register(worker_id: str, national_id: str = "none", consent: bool = False, birth_date: str | None = None,
             age_years: int | None = None, details: dict | None = None, today: date | None = None,
             notice_given: bool = True) -> Woman:
    """First visit: create her Ovamha woman ID and card code, always (ID-01).

    national_id: "nin" (she has a national ID card) or "none". With "nin" and her consent,
    Ovamha records only that the card was shown, never the number (ID-03, ID-04); the
    link is made later through the national ID service, against this same woman ID.
    Date of birth: exact (birth_date) or estimated from her age (age_years), stored as
    a year and flagged as estimated, as is common where birth dates are not known.
    """
    today = today or date.today()
    if not notice_given:
        raise ValueError("Read the privacy notice to her first.")
    if national_id not in ("nin", "none"):
        raise ValueError("Choose National NIN or No ID.")
    if national_id == "nin" and not consent:
        raise ValueError("Ask for her consent to link her national ID, or choose No ID.")
    dob, estimated = None, False
    if birth_date:
        try:
            d = date.fromisoformat(birth_date)
        except ValueError:
            raise ValueError("Date of birth is not a valid date.")
        age = (today - d).days / 365.25
        if not 10 <= age <= 60:
            raise ValueError("Date of birth gives an age outside 10 to 60 years. Please check.")
        dob = d.isoformat()
    elif age_years is not None:
        if not 10 <= int(age_years) <= 60:
            raise ValueError("Age should be between 10 and 60 years. Please check.")
        dob, estimated = str(today.year - int(age_years)), True
    else:
        raise ValueError("Enter her date of birth, or estimate her age.")

    data = _load()
    code = new_code()
    while code in data:
        code = new_code()
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    w = Woman(str(uuid.uuid4()), code, now, worker_id, episode_id=str(uuid.uuid4()),
              birth_date=dob, birth_date_estimated=estimated, details=dict(details or {}), privacy_notice_at=now)
    if national_id == "nin":
        w.national_id = {"document": "National ID (NIN)", "method": "document-shown", "verified": False, "consent_at": now}
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
    return _woman(rec), ""


def save_profile(code: str, profile: dict) -> Woman:
    """Store the ANC.B6 profile collected at her first contact."""
    data = _load()
    c = normalise(code)
    data[c]["profile"] = profile
    data[c]["profile_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    _save(data)
    return _woman(data[c])


DEMO_WOMEN = Path(__file__).resolve().parents[4] / "content" / "demo-women.json"


def seed_demo(today: date | None = None) -> list[str]:
    """Add the fictional demo women (content/demo-women.json) if they are missing, so a returning
    check can be tried on any fresh start. IDs are deterministic, so FHIR uploads match on retry."""
    if not DEMO_WOMEN.exists():
        return []
    today = today or date.today()
    data, added = _load(), []
    for d in json.loads(DEMO_WOMEN.read_text())["women"]:
        code = d["card_code"]
        if not is_valid(code):
            continue
        history = [{**{k: v for k, v in h.items() if k != "weeks_ago"},
                    "at": (today - timedelta(weeks=h.get("weeks_ago", 0))).isoformat()} for h in d.get("history", [])]
        if code in data:
            if history and not data[code].get("history"):  # backfill demo women seeded by an earlier version
                data[code]["history"] = history
                added.append(code)
            continue
        profile = dict(d["profile"])
        if d.get("lmp_weeks_ago") is not None:
            profile["lmp"] = (today - timedelta(weeks=d["lmp_weeks_ago"])).isoformat()
        w = Woman(str(uuid.uuid5(uuid.NAMESPACE_URL, f"ovamha-demo-woman/{code}")), code,
                  datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "demo-seed", visits=1,
                  episode_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"ovamha-demo-episode/{code}")),
                  birth_date=str(today.year - d["age_years"]), birth_date_estimated=True,
                  details=d.get("details", {}), profile=profile,
                  profile_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(), history=history)
        data[code] = asdict(w)
        added.append(code)
    if added:
        _save(data)
    return added


def record_visit(code: str, summary: dict | None = None) -> None:
    """Count a finished check and keep its summary, so a returning woman's earlier findings are available."""
    data = _load()
    c = normalise(code)
    if c in data:
        data[c]["visits"] += 1
        data[c]["last_visit"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        if summary:
            data[c].setdefault("history", []).append(summary)
        _save(data)


def her_record(w: Woman) -> dict:
    """Everything this device holds about her, to show or print for her (HIS Policy 2021 s.3.5.10(a);
    draft DP Bill 2025 s.43). Clinical encounter records live on the hub, not in this registry."""
    return {
        "card_code": display(w.card_code), "woman_id": w.woman_id, "registered": w.created_at,
        "registered_by": w.created_by, "visits": w.visits, "last_visit": w.last_visit,
        "birth_date": w.birth_date, "birth_date_estimated": w.birth_date_estimated,
        "national_id": "Card shown, with her consent; number not stored" if w.national_id else "Not linked",
        "details": w.details, "profile": w.profile, "profile_at": w.profile_at,
        "privacy_notice_at": w.privacy_notice_at,
        "history": list(reversed(w.history)),  # newest first
    }
