"""Anonymised export of the device registry, for reporting and evaluation
(WHO ANC DAK ANC.NFXNREQ.004 "Anonymize data that is exported from the system";
draft Data Protection Bill 2025 s.36(2), s.39(3)(i); MoHS HIS Policy 2021 s.3.5.10).

Dropped: names, address, phone numbers, alternative contact, card code, woman ID, national ID
details, exact dates (date of birth, last menstrual period, registration day) and any free text.
Kept: a random per-export pseudonym, 5-year age band, registration month, visit count, and the
coded (single-choice, multi-choice, count) answers of the ANC.B6 profile.

The pseudonym is random for every export, so two exports cannot be joined on it. Small groups
can still identify someone in a small community: review counts below 5 before sharing.

Usage: .venv/bin/python scripts/export_anonymised.py [-o export.csv]
"""
from __future__ import annotations

import argparse
import csv
import secrets
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/prototype/src"))
from ovamha_proto import audit, questionnaire, registry  # noqa: E402

KEEP_TYPES = {"single", "multi", "count"}


def age_band(birth_date: str | None, today: date) -> str:
    if not birth_date:
        return "unknown"
    age = today.year - int(birth_date[:4])
    lo = age // 5 * 5
    return f"{lo}-{lo + 4}"


def rows(today: date | None = None) -> list[dict]:
    today = today or date.today()
    coded = [q["id"] for q in questionnaire.questions("anc-profile") if q["type"] in KEEP_TYPES]
    out = []
    for rec in registry._load().values():
        w = registry._woman(rec)
        row = {"pseudonym": secrets.token_hex(6), "age_band": age_band(w.birth_date, today),
               "age_estimated": w.birth_date_estimated, "registered_month": w.created_at[:7],
               "visits": w.visits, "national_id_linked": bool(w.national_id), "profile_done": bool(w.profile)}
        for qid in coded:
            v = w.profile.get(qid, "")
            row[qid] = ";".join(map(str, v)) if isinstance(v, list) else v
        out.append(row)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", help="CSV file (default: stdout)")
    a = ap.parse_args()
    data = rows()
    fh = open(a.out, "w", newline="") if a.out else sys.stdout
    if data:
        w = csv.DictWriter(fh, fieldnames=list(data[0]))
        w.writeheader(); w.writerows(data)
    if a.out:
        fh.close()
    audit.log("export-anonymised", count=len(data))
    print(f"exported {len(data)} anonymised rows", file=sys.stderr)


if __name__ == "__main__":
    main()
