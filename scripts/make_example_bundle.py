"""Write fhir/examples/referral-bundle.json from the demo scenario (bleeding at 28 weeks).

Runs the real pipeline (extract -> safety net -> confirm -> rules -> Bundle) on the
scenario transcript, with the worker's confirmations scripted. Identifiers are random.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/prototype/src"))

from ovamha_proto.confirm import Session  # noqa: E402
from ovamha_proto.encounter import Encounter  # noqa: E402
from ovamha_proto.extract import extract  # noqa: E402
from ovamha_proto.fhir_bundle import build_bundle, validate  # noqa: E402
from ovamha_proto.rules import evaluate  # noqa: E402
from ovamha_proto.safety_net import scan  # noqa: E402
from ovamha_proto.asr import model_name  # noqa: E402

TRANSCRIPT = ("She is 28 weeks pregnant and she has heavy vaginal bleeding since this morning. "
              "She fainted yesterday but is fine now. No fever.")

s = Session()
ex = extract(TRANSCRIPT, "en")
s.propose_from_extraction(ex)
s.propose_flags(scan(ex))
for f in ("vaginal_bleeding", "bleeding_amount", "fainting"):  # worker confirms; "fever" left unconfirmed
    s.confirm(f)
for f, v in (("gestational_age_weeks", 28), ("systolic", 90), ("diastolic", 60)):
    s.propose_keypad(f, v)
    s.confirm(f)
confirmed = s.finalise()
e = Encounter(confirmed, dict(s.sources), evaluate(confirmed), "en", s.worker_id, model_name("en"))
bundle = build_bundle(e)
validate(bundle)
out = ROOT / "fhir/examples/referral-bundle.json"
out.write_text(json.dumps(bundle, indent=2) + "\n")
print(f"wrote {out.relative_to(ROOT)} ({len(bundle['entry'])} entries, encounter code {e.code}); fhir.resources validation passed")
