"""Appointment reminder SMS: only with her phone and consent; date, facility and danger signs only."""
from ovamha_proto import sms
from ovamha_proto.encounter import Encounter


def enc(details):
    e = Encounter({}, {}, [], "en", "w1", "test")
    e.facility, e.details = "CHP Lumley", details
    e.next_contact = {"date": "2026-10-18", "week": 34}
    return e


def test_reminder_needs_phone_and_consent():
    assert sms.wants_reminder(enc({"phone": "+23276000102", "wants_reminders": "yes"}))
    assert not sms.wants_reminder(enc({"phone": "+23276000102", "wants_reminders": "no"}))
    assert not sms.wants_reminder(enc({"wants_reminders": "yes"}))


def test_reminder_text_has_date_and_facility_but_no_name():
    e = enc({"first_name": "Aminata", "family_name": "Demo", "phone": "+23276000102", "wants_reminders": "yes"})
    t = sms.reminder_text(e)
    assert "18 Oct 2026" in t and "CHP Lumley" in t and "come to the clinic" in t
    assert "Aminata" not in t and "Demo" not in t


def test_no_reminder_without_a_next_contact_date():
    e = enc({"phone": "+1", "wants_reminders": "yes"})
    e.next_contact = {"text": "Set the next contact once gestational age is known"}
    assert sms.reminder_text(e) is None
