PY := .venv/bin/python
SRC := apps/prototype/src

.PHONY: setup test run run-https bundle

setup:            ## create venv and install the prototype
	python3 -m venv .venv && .venv/bin/pip install -r apps/prototype/requirements.txt

test:             ## rule boundary tests + confirmation gate + FHIR/SMS
	.venv/bin/pytest -q

run:              ## start the UI on http://<this-machine>:7860
	cd $(SRC) && ../../../$(PY) -m ovamha_proto.app

run-https:        ## same, with self-signed HTTPS so phone microphones work
	cd $(SRC) && ../../../$(PY) -m ovamha_proto.app --https

bundle:           ## regenerate fhir/examples/referral-bundle.json
	$(PY) scripts/make_example_bundle.py
