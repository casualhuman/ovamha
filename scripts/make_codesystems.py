"""Write FHIR CodeSystem definitions for every Ovamha placeholder code system to fhir/ig/.

Generated from the app's own data (labels, question sets), so the definitions cannot
drift from what the app emits. They are loaded into the HL7 validator (scripts/validate_fhir.sh)
and can be loaded into a FHIR server. All are status 'draft' and experimental: they are
placeholders until WHO SMART ANC codes replace them after DAK Annex extraction.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/prototype/src"))

from ovamha_proto import questionnaire  # noqa: E402
from ovamha_proto.confirm import label  # noqa: E402
from ovamha_proto.fhir_bundle import (  # noqa: E402
    CAPTURE_CS, DANGER_CS, DANGER_FIELDS, FHIR, NUMERIC_UNITS, OBS_CS, PROFILE_CS,
)

OUT = ROOT / "fhir" / "ig"


def codesystem(url: str, title: str, description: str, concepts: list[tuple[str, str]]) -> dict:
    cid = url.rsplit("/", 1)[-1]
    rows = "".join(f"<tr><td>{c}</td><td>{d}</td></tr>" for c, d in concepts)
    return {
        "resourceType": "CodeSystem", "id": cid, "url": url, "version": "0.1.0",
        "name": "".join(w.capitalize() for w in cid.replace("-", " ").split()), "title": title,
        "status": "draft", "experimental": True, "publisher": "Ovamha",
        "description": description, "caseSensitive": True, "content": "complete", "count": len(concepts),
        "text": {"status": "generated", "div": f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{title}</p><table>{rows}</table></div>'},
        "concept": [{"code": c, "display": d} for c, d in concepts],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    placeholder = " Placeholder until WHO SMART ANC codes are mapped after DAK Annex extraction."
    systems = [
        codesystem(DANGER_CS, "Ovamha danger signs", "Danger signs captured by Ovamha, named after the WHO DAK quick check and national guideline danger signs." + placeholder,
                   [(f.replace("_", "-"), label(f)) for f in sorted(DANGER_FIELDS)]),
        codesystem(OBS_CS, "Ovamha observations", "Other observations captured by Ovamha." + placeholder,
                   [(f.replace("_", "-"), label(f)) for f in sorted(list(NUMERIC_UNITS) + ["bleeding_amount", "urine_protein", "severe_pe_symptoms"])]
                   + [("referral-decision", "Referral decision by health worker")]),
        codesystem(CAPTURE_CS, "Ovamha capture method", "How a value was captured and confirmed (architecture specification section 12).",
                   [("keyed", "Entered on keypad by the health worker"),
                    ("spoken-ai-extracted-confirmed", "Spoken, extracted by AI, confirmed by the health worker"),
                    ("ai-flag-confirmed", "Raised by the AI safety net, confirmed by the health worker"),
                    ("rule-prompt-confirmed", "Asked because a rule needed it, confirmed by the health worker")]),
        codesystem(f"{FHIR}/CodeSystem/referral-decision", "Ovamha referral decision", "The health worker's decision after guideline advice.",
                   [("urgent", "Urgent referral"), ("planned", "Planned referral"), ("none", "No referral at this contact")]),
        codesystem(PROFILE_CS, "Ovamha ANC profile items", "First-contact history and profile items, each citing its WHO DAK data element (ANC.B4, ANC.B6)." + placeholder,
                   [(q["id"], f"{q['label']} ({q['dak']})") for q in questionnaire.questions("anc-profile")]
                   + [("edd", "Estimated date of delivery (LMP + 280 days)")]),
    ]
    for q in questionnaire.questions("anc-profile"):
        if q.get("options"):
            url = f"{PROFILE_CS}-{q['id'].replace('_', '-')}"
            systems.append(codesystem(url, f"Ovamha answers: {q['label']}", f"Answer options for '{q['label']}' ({q['dak']})." + placeholder,
                                      [(o["value"], o["label"]) for o in q["options"]]))
    for cs in systems:
        (OUT / f"CodeSystem-{cs['id']}.json").write_text(json.dumps(cs, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(systems)} CodeSystems to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
