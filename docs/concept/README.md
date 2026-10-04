# MaternalSave: offline voice assistant for maternal healthcare in Africa (concept note)

The project's concept: the problem, the proposed solution, its users and components, two illustrative scenarios, and how it fits digital public infrastructure. It describes the **intended product**. What the hackathon prototype implements today is in the [main README](../../README.md#what-works-now-all-offline). The labour-care workflow below is proposed and not yet built.

> Numbers in square brackets refer to the concept note's reference list (to be added to this page).

## Problem statement

Maternal mortality remains a major health challenge in Africa. The 2025 United Nations inter-agency estimates indicate that sub-Saharan Africa accounted for 182,000 maternal deaths in 2023, approximately 70% of the global total [1, 2]. Its maternal mortality ratio was 454 deaths per 100,000 live births, compared with the global Sustainable Development Goal target of fewer than 70 by 2030 [3].

Many maternal deaths are preventable through timely, appropriate care. WHO identifies severe bleeding, infection, hypertensive disorders, delivery complications and unsafe abortion as collectively responsible for approximately 75% of maternal deaths globally. However, shortages of qualified personnel, essential supplies and accessible, good-quality services limit effective care, particularly for poorer women in remote communities [2].

Sierra Leone illustrates these service constraints. The World Bank's 2025 health project paper reports 6.4 skilled health workers per 10,000 people, with particularly low availability in rural areas [4, p. 5]. Its 2021 diagnostic reports that only 4.8% of primary healthcare facilities had the resources to provide Basic Emergency Obstetric and Neonatal Care [5, p. 6]. These are historical findings cited in the reports, rather than current estimates for Africa.

Weak information and coordination further complicate care. World Bank diagnostics describe paper-based records, unreliable connectivity and weak information feedback in Sierra Leone, alongside continuing referral and reporting difficulties [4, p. 4; 5, p. 6]. Nigeria's Ministry of Health similarly identifies fragmented services and poor data infrastructure [6].

These constraints underline the need for frontline workers to access pregnancy history, document concerns, recognise when further assessment is required and communicate findings and actions to receiving providers. We propose an offline voice assistant that supports confirmed information capture, approved maternal guidance and structured handovers linked to existing pregnancy records. Its intended contribution is stronger continuity of information during care; its effects on documentation, referral completion and clinical outcomes require local evaluation.

During labour, continuity also depends on repeated assessment, timely recording and appropriate responses to changing observations. The WHO Labour Care Guide structures this process through assessment, documentation, comparison with reference thresholds and care planning with the woman [12]. This creates a further question for local investigation: whether frontline maternity personnel face difficulties applying these practices consistently, and whether accessible guidance and documentation support could help.

## Solution

The proposed intervention is an offline voice assistant that makes existing maternal health information usable at the point of care. It would support community health workers, nurses and midwives as they document encounters, consult approved guidance and communicate with pregnant women.

During an encounter, the worker could describe the woman's concern through speech. The assistant would structure the account, read back critical details for confirmation and incorporate available, authorised pregnancy history, gestational age and previous findings.

It would present approved questions and role-appropriate guidance to support the next action, including permitted local care, qualified assessment or established referral. Spoken explanations in a validated local language would help the woman understand the advice. A reviewed handover would distinguish reported symptoms, measured observations, previous findings and actions taken, making the reason for referral explicit.

For skilled maternity personnel managing active labour, a dedicated workflow would support the WHO Labour Care Guide through confirmed, time-stamped observations, timely assessment prompts, alerts requiring clinical review and documentation of assessments, actions and discussions with the woman. Its content and behaviour would follow nationally approved practice and require validation before clinical use [12, 13].

Documentation, available pregnancy records and approved guidance would remain accessible offline, with confirmed updates synchronised when connectivity returns. Remote consultation and digital referral delivery would require connectivity or alternative communication arrangements.

The intended contribution is stronger continuity across maternal care. Authorised professionals retain responsibility for clinical assessment and decisions; effective care also depends on transport, diagnostics, medicines and receiving-facility capacity.

## Intended users and language accessibility

MaternalSave would support community health workers, midwives, nurses, doctors and other trained maternity personnel, with guidance appropriate to their professional scope.

The product would be designed to accommodate multiple languages rather than depend on a single language. Users could switch between supported languages for spoken interaction, written guidance and patient explanations, including when the worker and woman prefer different languages. Switching languages would preserve the encounter context and confirmed information.

Each supported language would require validation of speech recognition, clinical terminology, translations and guidance retrieval. Uncertain interpretations would prompt clarification, with critical information read back for confirmation.

Approved guidance would remain accessible without creating a patient record. Optional case notes would support documentation and handover without delaying access to instructions.

## Proposed solution components

| Component | Proposed function |
| --- | --- |
| Voice-based documentation | Structure spoken symptoms, history and observations, with read-back confirmation, correction and timestamps |
| Pregnancy context | Present authorised pregnancy history, gestational age and previous findings, including their dates and sources |
| Approved maternal guidance | Present relevant questions, explanations and next-action prompts consistent with national protocols and the worker's professional scope |
| Labour care support | Support skilled maternity personnel using the locally approved WHO Labour Care Guide workflow through scheduled assessment prompts, confirmed observations and alerts requiring clinical review |
| Referral and handover support | Present established referral contacts and prepare reviewed summaries of findings, actions and reasons for referral or transfer of care |
| Patient communication and shared decisions | Explain approved information in validated local languages and document discussions with the woman and agreed actions |
| Offline continuity | Keep available records and approved guidance accessible offline, retaining confirmed updates for authorised synchronisation |

WHO's Digital Adaptation Kit for Antenatal Care would inform antenatal workflows and information requirements, while the WHO Labour Care Guide would inform the dedicated labour care workflow. Both would require adaptation to nationally approved practice and clinical validation before use.

AI would support speech recognition, information structuring, handover drafting and explanation of approved content. Fine-tuning would be considered where it improves a demonstrated task or language need. Clinical recommendations must remain traceable to approved guidance, and patient information would require separate authorisation before use in model training.

## Illustrative maternal care scenarios

### Example 1: supporting urgent access and referral

A pregnant woman presents with vaginal bleeding. She has not undergone ultrasound assessment, and the cause is unknown.

The assistant guides the worker through the approved assessment questions, including gestational age, bleeding onset and amount, associated pain, dizziness or fainting, and relevant history. Critical responses are read back for confirmation. Heavy bleeding, severe abdominal pain, dizziness or fainting can indicate the need for immediate treatment [11].

When the confirmed information meets an approved escalation criterion, the assistant displays and speaks the required next action. It presents the established referral contact and destination from a maintained local directory, and any immediate instructions authorised for that worker's role. It cannot assume that a facility has accepted the referral or that its capacity information is current.

The assistant also prepares a handover containing the complaint, pregnancy stage, observations and actions already taken. The worker confirms it, initiates the referral through existing arrangements and records the outcome when available. Urgent action proceeds without waiting for connectivity.

**The assistant's contribution:** gathering relevant information, applying approved escalation criteria, presenting the next action and preparing a useful clinical handover.

### Example 2: supporting assessment and clinical review during labour

A woman is receiving care in active labour from a trained midwife. The midwife uses the assistant to record observations required by the locally approved Labour Care Guide workflow. The assistant reads back critical values for confirmation and records the time of each assessment.

When the next assessment is due, the assistant prompts the midwife to obtain and record the relevant observations. If a confirmed finding meets a Guide alert criterion, it explains which observation requires attention and prompts clinical review through the established escalation pathway.

The assistant presents the relevant approved guidance and helps document the clinician's assessment, the discussion with the woman and the agreed action. If responsibility passes to another provider, it prepares a reviewed summary of the observations over time and actions already taken.

**The assistant's contribution:** helping the midwife apply the Guide's assessment–recording–review–planning workflow consistently. Measurements, examinations and clinical decisions remain the responsibility of qualified personnel [12].

## Digital public infrastructure and interoperability

The assistant should operate within the existing health information ecosystem. Relevant foundations include recognised patient identifiers, facility directories, shared data definitions and authorised exchange between care systems. These enable information captured during one encounter to contribute to subsequent care without creating another disconnected register.

Existing initiatives demonstrate the institutional basis for this approach. At PReSTrack's July 2024 launch in Sierra Leone, UNFPA reported a pilot across 39 health facilities involving more than 10,000 registered pregnant women. Its documented capabilities include pregnancy tracking, early risk flagging and hybrid online/offline operation [5]. Nigeria's Digital in Health Initiative describes an architecture intended to connect DHIS2, electronic medical records and other platforms through interoperable services and health information exchange [3]. These examples establish relevant systems and policy directions, although they do not confirm that every required interface is currently available.

DHIS2's documented integration capabilities and South Africa's MomConnect implementation provide further precedents for connecting maternal services to wider health infrastructure [6, 7].

Within this architecture, the proposed assistant would serve as a voice interface and documentation capability for existing maternal care workflows. Country-specific connections would determine how records are retrieved and updated, while local clinical protocols, languages and referral arrangements would determine how the service behaves.

This approach is consistent with the World Bank-supported emphasis on stronger maternal services and connections between lower-level facilities and referral hubs [1, p. 2]. That alignment supports the rationale for investigation; it does not establish World Bank endorsement of the proposed product.

## References

To be added from the concept note. Note: the same numbers are used for different sources in different sections (for example [3] and [5]); the list should be checked when it is added.
