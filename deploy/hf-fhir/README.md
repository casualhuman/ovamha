---
title: MaternaSave FHIR hub (demo)
emoji: 🏥
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8080
pinned: false
short_description: HAPI FHIR R4 server receiving MaternaSave referral records (demo)
---

# MaternaSave demo hub: HAPI FHIR R4

The [MaternaSave](https://github.com/casualhuman/ovamha) demo app syncs its FHIR R4 records here, as a facility hub would. **Fictional demo data only; the in-memory database resets when the Space restarts.**

Browse the records: `/fhir/Patient`, `/fhir/ServiceRequest`, `/fhir/Task`, or `/fhir/Patient/{id}/$everything`.
