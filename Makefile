PY := .venv/bin/python
SRC := apps/prototype/src

.PHONY: setup test run run-https bundle phones run-phones

setup:            ## create venv and install the prototype
	python3 -m venv .venv && .venv/bin/pip install -r apps/prototype/requirements.txt

test:             ## rule boundary tests + confirmation gate + FHIR/SMS
	.venv/bin/pytest -q

run:              ## start the UI on http://<this-machine>:8000
	cd $(SRC) && HF_HUB_OFFLINE=1 ../../../$(PY) -m ovamha_proto.server

phones:           ## start two Android emulators (her phone, hospital phone) that receive Ovamha's SMS
	scripts/sms_phones.sh

run-phones: phones ## start the phones, then the UI sending SMS to them
	cd $(SRC) && HF_HUB_OFFLINE=1 OVAMHA_SMS_EMULATOR=1 ../../../$(PY) -m ovamha_proto.server

run-https:        ## same, with self-signed HTTPS so phone microphones work
	cd $(SRC) && HF_HUB_OFFLINE=1 ../../../$(PY) -m ovamha_proto.server --https

bundle:           ## regenerate fhir/examples/referral-bundle.json
	$(PY) scripts/make_example_bundle.py
