# Decision: national guidelines as cited rules, not a fine-tuned model; the health worker decides

## MaternaSave suggests, the health worker decides

The Sierra Leone Integrated Obstetric and Newborn Care Guideline (2026 draft) makes referral the referring health worker's responsibility: assess, stabilise, explain and obtain consent, communicate with iSBAR, complete the standard referral form, record call and ambulance times. MaternaSave therefore never refers on its own:

1. **Assess** (`/api/finish`): confirmed data only; WHO DAK demo rules plus national guideline advice, each item with its table citation.
2. **Decide** (`/api/decision`): the worker chooses urgent referral, planned referral or no referral. Declining a suggested referral, or downgrading an urgent one, requires a written reason. The advice is never hidden or removed (decision 1).
3. **Refer** (`/api/referral/complete`, urgent only): the woman's consent (a refusal is recorded), the pre-referral checklist, an iSBAR script for the call centre, call and ambulance times. Only then is the referral SMS sent and a ServiceRequest created.

FHIR records the advice (GuidanceResponse per item, with citation), the worker's decision (Observation `referral-decision`, with reason), consent to referral (Consent), and a ServiceRequest/Task only when the worker referred.

## Why not fine-tune a model on the guideline

| | Fine-tuning a language model on the guideline | Encoding the guideline as cited rules (chosen) |
| --- | --- | --- |
| Correctness | Can produce fluent but wrong advice; no guarantee a threshold (e.g. BP 160/110) is applied exactly | Deterministic; unit-tested on boundary values |
| Traceability | Cannot show which table an answer came from | Every suggestion cites its table or section |
| Updates | Retrain when the guideline changes | Edit `content/guidelines/*.json`; reviewed like any document |
| Offline, low-cost devices | Needs a large model to be reliable | Runs instantly on a phone or Raspberry Pi |
| Responsible AI | Generated clinical advice (excluded by decision 4) | No generated advice; AI only transcribes, extracts and flags |

AI stays where it helps: speech recognition (worth fine-tuning on clinical speech in Krio, Yoruba and English), extraction, and the add-only safety net. The guideline text can also seed the speech model's clinical vocabulary without any training.

## What is encoded now (content/guidelines/sierra-leone-iong-2026.json)

- Table 3.3 danger signs in pregnancy
- Pre-eclampsia classification (PE, severe PE, eclampsia) from "Classification after 20 weeks of pregnancy", including "do not wait 4 hours to repeat BP"
- Table 3.4 referral pathway for high-risk pregnancy, by facility level (MCHP, CHP, CHC, BEmONC vs CEmONC)
- Table 3.2 eight-contact schedule (next contact date)
- Referral section: consent, pre-referral actions, iSBAR, documentation

Thresholds the guideline does not define are stated as assumptions in the content file and shown to the worker (adolescent under 20; high parity 5 or more; fetal heart rate outside 110 to 160, which the guideline gives in the intrapartum chapter). The guideline file itself is not committed; it is a Ministry draft.
