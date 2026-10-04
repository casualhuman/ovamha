# Point-of-care demo: one woman, two moments (about 5 minutes)

**The idea in one line:** Ovamha is not a referral button. At every contact it tells the health worker what the national guideline expects her to do, for this woman, today; referral is one of those suggestions, and the worker decides.

**The woman:** card **`ANC-24T`**, *Aminata Demo* (fictional), 24 years old, **32 weeks pregnant**, second pregnancy, **had pre-eclampsia in her first pregnancy**. Her history is already on the device, so the history step is skipped. Pre-eclampsia is chosen because it is a leading cause of maternal death and the guideline has clear actions for prevention, monitoring and emergency care.

**Setup:** app at http://localhost:8000 (internet off) or https://r8086-ovamha.hf.space. Sign in `fati` / `769131`.

---

## Part A: a routine visit, where the suggestions do the work (3 minutes)

| # | Do | What appears | Say |
| --- | --- | --- | --- |
| 1 | **Guide me → Returning**, type `anc-24t` → **Continue** | Card found: Aminata Demo, born about 2002, history recorded | "Every woman gets her own card number. No national ID number is ever stored." |
| 2 | Tap the mic and say: *"Routine visit. She feels well, she only has some back pain. No bleeding, no headache, and the baby is moving well."* → **Replay guidance** to hear it → **Next** | **What we understood:** Vaginal bleeding · No, Headache · No | "Speech is turned into text on this device. The AI works out the meaning, and 'no bleeding' is recorded as a real answer, not as missing." |
| 3 | Tap **Correct** on both → **Next: measurements** | History step skipped (already recorded) | "Her full history was taken at her first visit, as the WHO DAK requires." |
| 4 | Gestational age is filled in from her history (32 weeks) → **Confirm**. Blood pressure: tap the mic and say *"one twenty-eight over eighty-two"* → **Confirm**. Open **More measurements**: fetal heart rate `142` → **Confirm** | Numbers filled from voice, read back, confirmed | "Numbers are typed or spoken, then read back. Nothing counts until she confirms it." |
| 5 | **Check the guidelines** | Banner: *High-risk pregnancy: the guidelines suggest planning delivery at a CEmONC facility. You decide.* | "No emergency today, but the guideline still has a lot to say about this woman." |
| 6 | Tap the row **Previous pre-eclampsia or eclampsia** | *If at a lower facility: refer to CEmONC for further assessment. She can have ANC follow-up here; counsel and prepare her for delivery at a CEmONC facility.* (Sierra Leone guideline, Table 3.4) | "Every suggestion cites the national guideline table it comes from, and depends on this facility's level: a CHP." |
| 7 | Open **What you can do now → High risk of pre-eclampsia: prevention and monitoring** (tap 🔊) | Aspirin 75 mg daily; calcium 1.5–2.0 g daily; BP and urine protein every contact; birth at 37 weeks at a facility able to do caesarean birth | "This is what the nurse can do **today**, from the guideline, word for word. Prevention, not just referral." |
| 8 | Scroll to **Care due at this contact** | Contact 4 (about 30–32 weeks): IPTp-4 SP, aspirin 75 mg daily, MMS, retest HIV if negative before, repeat full haemogram | "The eight-contact schedule tells her exactly what is due today: malaria prevention, supplements, tests." |
| 9 | Point to **Next contact** | Contact 5 at 34 weeks, with a date | |
| 10 | **Your decision → Plan a referral → Confirm my decision** | Result: Planned referral recorded; no emergency SMS; the record is saved and syncs to the hub | "The worker decides. A planned referral is recorded; no ambulance is called." |

## Part B: the same woman, two weeks later, an emergency (2 minutes)

| # | Do | What appears | Say |
| --- | --- | --- | --- |
| 11 | **New check → Returning** `anc-24t` → say: *"Since this morning she has a very bad headache and her eyes are blurry. Her face and hands are swollen."* | Headache, Visual disturbance, Swelling; headache asks **Severe / Mild** | "It understood three danger signs from everyday words." |
| 12 | Headache **Severe**, others **Correct**. BP: say *"one sixty-five over one hundred and twelve"*; urine protein **++** → **Check the guidelines** | *The guidelines suggest urgent referral. You decide.* Rows: danger signs (Table 3.3), **BP 165/112 with proteinuria ++ → severe pre-eclampsia**, previous pre-eclampsia (Table 3.4) | "Severe pre-eclampsia is defined exactly as in the national guideline: BP 160/110 or above with protein." |
| 13 | Open **What you can do now → Severe pre-eclampsia / eclampsia** (🔊) | Magnesium sulphate loading dose with exact amounts; repeat and maintenance doses; **withhold if** breathing below 16, no reflexes or low urine; hydralazine or labetalol; dexamethasone at 24 to below 34 weeks; *do only what you are trained and supplied to do at your level* | "The nurse sees the guideline's treatment protocol at the bedside, including when to stop. This is what saves lives before the ambulance arrives." |
| 14 | **Refer urgently → Confirm** → *She agrees* → tick *Assess and stabilise*, *IV line*, *pre-referral treatment* → 🔊 on **Call the call centre** → **I called just now** | The iSBAR script is read aloud for the phone call | "The national guideline requires consent, stabilisation and an iSBAR call. Ovamha walks her through it." |
| 15 | **Refer digitally and prepare the letter** → **Preview the letter** → tap **ACK** in the SMS card | Referral letter with reasons, findings, treatment given and a feedback slip; SMS to the hospital; ACK turns the status to **accepted** | "Digital referral by SMS and a standards-based FHIR record; a paper letter when needed. All offline." |

## Closing line (20 seconds)

"Everything you saw ran on this device with the internet off. The AI only listens and proposes; the national guideline decides what is suggested; and the health worker decides what happens."

---

**Before filming:** run through it once; switch the internet off and show it on camera; on the hosted copy, open the link a minute early to wake it. If a recording is misunderstood, the worker can tap **Not true** or type the description; that is part of the design, not a failure.
