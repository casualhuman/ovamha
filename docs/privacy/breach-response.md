# Breach response plan: MaternalSave

**Status: DRAFT**, 2026-10-04. A breach is any loss, theft, or access by the wrong person to
information about a woman or a health worker: for example a lost phone, a shared PIN, an SMS sent
to the wrong number, or records copied without permission.

## Who to tell, and when

| When | Who acts | Tell | Source |
|---|---|---|---|
| Immediately | The health worker who notices | Head of facility | SL-HIS 3.7(c); NHA s.29 |
| Immediately | Head of facility (Sierra Leone) | DMO, Medical Superintendent, programme manager, Director of DPPI | SL-HIS 3.5.2(d), 3.7(c) |
| Immediately | Head of facility (Nigeria) | State Ministry of Health / facility management, as the controller's procedure sets | NHA s.29 (head of facility responsible for records) |
| Within 48 hours | Any processor (e.g. a support contractor) | The controller | Bill s.60(3) |
| Within 72 hours | Controller (Nigeria) | Nigeria Data Protection Commission (NDPC) | NDPA s.40(2) |
| Within 72 hours | Controller (Sierra Leone) | Data Protection Commission, once established; after 72 hours, give reasons for the delay | SL-Bill s.60(1)(a), (2) |
| Without undue delay / as soon as practical | Controller | Each affected woman, in writing (in person by her health worker where safer) | NDPA s.40; SL-Bill s.60(1)(b) |
| If an offence is suspected | Facility / ministry | Law enforcement (in Nigeria, unauthorised access to records is an offence, NHA s.29) | SL-HIS 3.7(b); NHA s.29 |

## Steps

1. **Contain.** Lost or stolen phone: sign the worker out on the hub, change their PIN, and remote-wipe
   the device (production). Wrong SMS recipient: ask them to delete it, and record the number.
   Shared PIN: reset it.
2. **Assess.** Which women, what data (health, HIV, adolescent?), was it encrypted, is there a real
   risk of harm? Use the audit log (`audit.py`; production: hub AuditEvents) to see what was accessed.
3. **Notify** as in the table. The notice must say what data was involved, what has been done, and
   what she can do to protect herself (NDPA s.40; SL-Bill s.60(5)). ECOWAS members must keep data
   protected from unauthorised third parties (ECOWAS Art. 43).
4. **Fix the cause** and record it.
5. **Record every breach,** even small ones, with the date, what happened, who was told and when,
   and what changed.

## What limits the damage today

Encrypted storage (`secure_store.py`), automatic sign-out after 15 minutes without use, no voice
recordings kept, no names in the audit log or SMS, national ID numbers never stored. See
[README.md](README.md).

## Sources

- ECOWAS, *Supplementary Act A/SA.1/01/10*, 2010: Art. 43.
- *Nigeria Data Protection Act*, 2023: s.40. *National Health Act* (Nigeria), 2014: s.29.
- MoHS Sierra Leone, *Health Information System Policy*, 2021: s.3.5.2(d), 3.7(b)-(c).
- *The Data Protection and Right to Access Information Regulatory Commission Act, 2025* (Bill, not yet law): s.60.
