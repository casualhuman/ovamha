# First ANC contact: alignment with the WHO ANC DAK

Source: WHO Digital Adaptation Kit for Antenatal Care (2021), business process ANC.B and Table 7 (core data elements). Question wording, DAK IDs and read-aloud text live in `content/questions/anc-registration.json` and `content/questions/anc-profile.json`.

## Order of the first contact

| DAK step | MaternalSave screen | Notes |
| --- | --- | --- |
| ANC.A4 Gather client details | First visit (registration) | National ID asked first; MaternalSave woman ID and card code always created (spec ID-01) |
| ANC.B4 Confirm pregnancy | Her history | "Pregnancy confirmed?" |
| ANC.B5 Quick check (danger signs) | Describe, then Confirm | If a danger sign is confirmed: refer urgently and skip the profile (DAK step 2, spec decision 8) |
| ANC.B6 Collect woman's history and profile | Her history | First contact only, after the quick check, only when no danger sign |
| ANC.B8 Physical examination (part) | Measurements | BP, repeat BP, pulse, temperature, fetal heart rate, urine protein, severe pre-eclampsia symptoms |

## ANC.A4 data elements

| DAK element | MaternalSave |
| --- | --- |
| DE1 Unique identification | MaternalSave woman ID (UUID) + card code with check character |
| DE2 First name, DE3 Last name | Collected (family name optional) |
| DE4 Contact date | Encounter time |
| DE5 DOB, DE6 Age | Exact date, or estimated age stored as an estimated birth year |
| DE7 Address | Community or village (optional) |
| DE8 Mobile phone, DE9 Wants reminders | Optional; reminders asked only when a phone is given |
| DE10–DE11 Alternative contact | Optional emergency contact name and phone |
| DE12 Co-habitants | Optional, multi-select |

## ANC.B6 data elements

All groups in Table 7 are collected: education (DE1–6), occupation (DE7–13), gestational age and its source with LMP-derived GA and EDD (DE14–22), gravida and outcomes (DE23–26), last live birth preterm (DE27–33), past pregnancy complications (DE34–50), past substance use (DE51–56), allergies (DE57–71), past surgeries (DE72–82), chronic conditions (DE83–99), tetanus vaccine (DE100–104), flu vaccine (DE105–108), current medications (DE109–138), caffeine (DE139–144), alcohol and substances (DE145–152), tobacco (DE153–155), partner HIV status (DE156–161, marked confidential in FHIR).

"Don't know" is recorded as unknown (FHIR `dataAbsentReason = asked-unknown`), never as normal.

## Known gaps (stated, not hidden)

- **Answer options are drafts.** The exact option lists come from the DAK Annex A data dictionary, which is not yet extracted. Each question cites its DAK element range so the options can be replaced one for one.
- **Codes are MaternalSave placeholders** (`https://fhir.ovamha.org/CodeSystem/anc-profile`), except LMP (LOINC 8665-2). SMART ANC codes replace them after Annex extraction.
- **Not yet built from the ANC.B contact:** ANC.B7 symptoms follow-up and intimate partner violence enquiry, ANC.B8 full examination (height, weight, fundal height, etc.), ANC.B9 tests, ANC.B10 counselling and treatment, ANC.B11 referral details beyond the danger-sign referral, ANC.B12 scheduling.
- **Decision logic:** only ANC.DT.01 (danger signs) and the pre-eclampsia worked example are implemented as demo rules.
- **Krio and Yoruba read-aloud wording** must be written by native-speaker health workers; until then the app reads English and says so.
