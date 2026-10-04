# Clinical guidelines

MaternalSave does not invent clinical rules. It checks only **confirmed** facts against WHO antenatal care
guidance and the country's own national guideline, and shows the exact source with every suggestion.
**The health worker decides.** This page lists every guideline used, how it is encoded and where.

MaternalSave does not invent clinical rules or data formats. Three layers are used (the third, data and identity standards, is in [../standards/README.md](../standards/README.md)), each cited inside the app and in the code:

1. **International clinical guidance:** WHO antenatal care recommendations, made computable through the WHO Digital Adaptation Kit (DAK).
2. **National guidelines:** the country's own clinical guideline, encoded as a content file. **Sierra Leone is the worked example**; another country plugs in its own file the same way.
3. **Health data and identity standards:** HL7 FHIR R4, LOINC, UCUM and HL7 terminologies, OpenHIE architecture patterns and World Bank ID4D identity principles.

## 1. WHO antenatal care: the Digital Adaptation Kit (DAK)

| WHO source | How MaternalSave uses it | Where |
| --- | --- | --- |
| [WHO recommendations on antenatal care for a positive pregnancy experience (2016)](https://www.who.int/publications/i/item/9789241549912) | Minimum of 8 contacts; the basis of the contact schedule | Next-contact date |
| [WHO DAK for antenatal care (2021)](https://www.who.int/publications/i/item/9789240020306), business process ANC.B | Order of the first contact: registration → quick check (danger signs) → history and profile **only at first contact and only if no danger sign** | [docs/decisions/dak-first-contact.md](../decisions/dak-first-contact.md) |
| DAK data elements ANC.A4 (registration) | Name, date of birth or estimated age, address, phone, SMS reminders, emergency contact, co-habitants | [content/questions/anc-registration.json](../../content/questions/anc-registration.json) |
| DAK data elements ANC.B4 and ANC.B6 (history and profile) | Every question cites its data element, e.g. gravida and outcomes `ANC.B6.DE23–DE26`, past pregnancy complications `ANC.B6.DE34–DE50`, chronic conditions `ANC.B6.DE83–DE99`, tetanus vaccine `ANC.B6.DE100–DE104`, partner HIV status `ANC.B6.DE156–DE161` | [content/questions/anc-profile.json](../../content/questions/anc-profile.json) |
| DAK decision logic ANC.DT.01, danger signs (Fig. 11 quick check) | Danger signs requiring referral | [rules.py](../../apps/prototype/src/ovamha_proto/rules.py) |
| DAK pre-eclampsia worked example (Table 12) | Pre-eclampsia rule with boundary tests (139/140, 159/160, 89/90, 109/110, protein + vs ++, missing repeat reading) | [tests/rules/test_rules.py](../../tests/rules/test_rules.py) |
| [WHO SMART ANC FHIR implementation guide](http://build.fhir.org/ig/WorldHealthOrganization/smart-anc/) | Resource model and the PlanDefinition reference `ANCDT01` in each rule result | [fhir_bundle.py](../../apps/prototype/src/ovamha_proto/fhir_bundle.py) |

## 2. National guideline: Sierra Leone as the worked example

The **Sierra Leone Integrated Obstetric and Newborn Care Guideline** (Ministry of Health, copy-edited draft of 19 January 2026) is encoded in [content/guidelines/sierra-leone-iong-2026.json](../../content/guidelines/sierra-leone-iong-2026.json). Only content MaternalSave can evaluate from confirmed data is encoded, and every item carries its table or section.

| Guideline section | What MaternalSave does with it |
| --- | --- |
| Table 3.2 Schedule of contacts (8 contacts: 12, 20, 26, 30, 34, 36, 38, 40 weeks) | Works out the next contact date from gestational age |
| Table 3.3 Danger signs in pregnancy | Suggests urgent referral when a listed sign is confirmed |
| Pre-eclampsia classification after 20 weeks | Classifies pre-eclampsia, severe pre-eclampsia and eclampsia; includes *"if severe pre-eclampsia is suspected, do not wait 4 hours to repeat the BP"* |
| Table 3.4 Referral pathway for high-risk pregnancy | Suggests the right action **for the worker's facility level** (MCHP, CHP, CHC, BEmONC vs CEmONC) |
| Referral section (minimum requirements; roles of the referring worker) | Referral pathway: informed consent, pre-referral actions, iSBAR call script, call and ambulance times, referral form with a feedback slip for the receiving facility |

**Cited examples, as the worker sees them:**

| Confirmed facts | Suggestion shown | Source cited |
| --- | --- | --- |
| Vaginal bleeding | "Danger sign in pregnancy: assess and stabilise, then consider urgent referral to a CEmONC facility." | Sierra Leone guideline, Table 3.3; WHO DAK ANC.DT.01 |
| BP 165/100 with urine protein ++ | "Life-threatening emergency. Stabilise and start magnesium sulphate per your level of care, then refer to a CEmONC facility for delivery and further management. Do not wait 4 hours to repeat BP." | Sierra Leone guideline, pre-eclampsia classification |
| Previous caesarean section, at a CHP | "If at a lower facility: refer to CEmONC for further assessment… counsel and prepare her for referral for delivery at a CEmONC facility." | Sierra Leone guideline, Table 3.4 |
| Sickle-cell disease, at a CHP | "If at a lower facility: referral to a CEmONC facility for advanced care." | Sierra Leone guideline, Table 3.4 |
| 22 weeks pregnant | "Contact 3 at 26 weeks, around …" | Sierra Leone guideline, Table 3.2 |

**Not just "refer": what the worker can do now.** With each suggestion, MaternalSave shows the guideline's own management steps, transcribed word for word and cited, labelled *"do only what you are trained and supplied to do at your level of care"*:

| Situation | Management shown (from the guideline) | Section |
| --- | --- | --- |
| Bleeding after 24 weeks | Shout for help; DR ABC; no vaginal examination; left lateral tilt if in shock; check fetal heart and movements; blood for Hb and group/screen, then IV fluids | Antepartum haemorrhage: initial resuscitation |
| Severe pre-eclampsia / eclampsia | Magnesium sulphate loading dose (4 g 20% IV + 5 g 50% IM each buttock), repeat dose, maintenance dose if transfer exceeds 4 hours, toxicity checks; hydralazine or labetalol for BP ≥160/110; dexamethasone at 24 to below 34 weeks | Pre-eclampsia and eclampsia: management |
| High risk of pre-eclampsia (e.g. previous PE) | Aspirin 75 mg daily; calcium 1.5–2.0 g daily; BP and urine protein every contact; birth at 37 weeks at a facility able to do caesarean birth | Tables 3.1 and 3.2; PE management |
| Every contact | Care due at this contact: IPTp-SP dose, Td vaccine, aspirin, MMS, anti-D at 28 weeks if Rh-negative, first-contact tests | Table 3.2 |

The guideline's annex on interventions by level of care is in images that could not be extracted, so the level-of-care note is shown on every management step instead of filtering by level.

Where the guideline does not define a threshold, MaternalSave states its assumption on screen and in the file (adolescent = under 20 years; high parity = 5 or more births; fetal heart rate normal range 110–160/min, from the guideline's intrapartum chapter). These need Ministry confirmation.


## 3. Adapting to another country

Add a guideline file in the same format as [content/guidelines/sierra-leone-iong-2026.json](../../content/guidelines/sierra-leone-iong-2026.json), with that country's tables and citations. The app, the rules engine and the referral workflow stay the same.

## 4. Nigeria (placeholder)

> **Not encoded yet.** Nigeria's national antenatal care guideline will be added as `content/guidelines/nigeria-<name>-<year>.json`, following section 3: source document and version, the tables used, and a citation on every item. Until then, the prototype applies the WHO DAK rules and the **Sierra Leone** guideline file to every user, including the Nigerian demo account (`funmi`); a Nigerian deployment needs its own file before use.

| To add | Status |
| --- | --- |
| National antenatal care guideline (source, version, date) | To be sourced |
| Danger signs and referral criteria | To be encoded |
| Contact schedule | To be encoded |
| Referral pathway and facility levels | To be encoded |
| Ministry contact for clinical review | To be identified |

## Related

- [docs/decisions/dak-first-contact.md](../decisions/dak-first-contact.md): element-by-element alignment with the WHO ANC DAK
- [docs/decisions/guideline-advice-not-fine-tuning.md](../decisions/guideline-advice-not-fine-tuning.md): why cited guideline rules instead of a generative model, and why the worker decides
