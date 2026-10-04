# Breach response plan: Ovamha

**Status: DRAFT**, 2026-10-04. A breach is any loss, theft, or access by the wrong person to
information about a woman or a health worker: for example a lost phone, a shared PIN, an SMS sent
to the wrong number, or records copied without permission.

## Who to tell, and when

| When | Who acts | Tell | Source |
|---|---|---|---|
| Immediately | The health worker who notices | Head of facility | HIS 3.7(c) |
| Immediately | Head of facility | DMO, Medical Superintendent, programme manager, Director of DPPI | HIS 3.5.2(d), 3.7(c) |
| Within 48 hours | Any processor (e.g. a support contractor) | The controller | Bill s.60(3) |
| Within 72 hours | Controller | Data Protection Commission (once established); after 72 hours, give reasons for the delay | Bill s.60(1)(a), (2) |
| As soon as practical | Controller | Each affected woman, in writing (in person by her health worker where safer) | Bill s.60(1)(b) |
| If an offence is suspected | Facility / MoHS | Law enforcement | HIS 3.7(b) |

## Steps

1. **Contain.** Lost or stolen phone: sign the worker out on the hub, change their PIN, and remote-wipe
   the device (production). Wrong SMS recipient: ask them to delete it, and record the number.
   Shared PIN: reset it.
2. **Assess.** Which women, what data (health, HIV, adolescent?), was it encrypted, is there a real
   risk of harm? Use the audit log (`audit.py`; production: hub AuditEvents) to see what was accessed.
3. **Notify** as in the table. The notice must say what data was involved, what has been done, and
   what she can do to protect herself (Bill s.60(5)).
4. **Fix the cause** and record it.
5. **Record every breach,** even small ones, with the date, what happened, who was told and when,
   and what changed.

## What limits the damage today

Encrypted storage (`secure_store.py`), automatic sign-out after 15 minutes without use, no voice
recordings kept, no names in the audit log or SMS, national ID numbers never stored. See
[README.md](README.md).

## Sources

- MoHS Sierra Leone, *Health Information System Policy*, 2021: s.3.5.2(d), 3.7(b)-(c).
- *The Data Protection and Right to Access Information Regulatory Commission Act, 2025* (Bill, not yet law): s.60.
