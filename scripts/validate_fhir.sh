#!/usr/bin/env bash
# Validate Ovamha FHIR output with the official HL7 FHIR Validator against base R4 (4.0.1).
# Needs: tools/validator_cli.jar and Java 17 (tools/jdk-17*/ or JAVA17 env var). First run downloads the R4 core package.
# Usage: scripts/validate_fhir.sh [bundle.json ...]   (default: fhir/examples/referral-bundle.json)
set -euo pipefail
cd "$(dirname "$0")/.."
JAVA="${JAVA17:-$(ls -d tools/jdk-17*/Contents/Home 2>/dev/null | head -1)/bin/java}"
FILES=("${@:-fhir/examples/referral-bundle.json}")
mkdir -p ml/eval/results
"$JAVA" -jar tools/validator_cli.jar "${FILES[@]}" -version 4.0.1 -ig fhir/ig -output ml/eval/results/fhir-validation.xml -level hints
