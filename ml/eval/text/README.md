# Mixed maternal-health text evaluation dataset

File: maternal_health_afrispeech_mixed_500.csv

## Composition

- E001–E400: the original 400 synthetic maternal-health examples, with their text, labels and categories preserved.
- E401–E500: 100 distinct original AfriSpeech-200 test transcripts: 70 labelled clinical and 30 labelled general in the upstream metadata. Upstream domain labels are retained, even when a sentence reads differently.
- The AfriSpeech addition has one positive example (maternal vaginal bleeding) and 99 negative/distractor examples. It does not attempt to balance all maternal symptom labels.
- All 500 ids and normalized texts are unique. All texts contain 8–40 whitespace-separated words. Text fields are quoted; labels use semicolons.
- No audio files are included. The source audio identifiers and paths refer to upstream recordings.

## Label interpretation

Apply the original task definitions: a target symptom must be present or recently experienced by the pregnant woman. Denied signs, other people's signs, hypothetical risks, educational descriptions and unrelated anatomy do not count. `none` means no target sign is established by this text; it does not mean that any patient mentioned is healthy or that a sentence provides safe clinical advice.

The positive AfriSpeech transcript reports maternal vaginal bleeding and fetal bradycardia. Only vaginal_bleeding is assigned: fetal bradycardia does not establish reduced_fetal_movement. Its reported admission event is treated as recent in the episode described; the source gives no calendar date.

Source categories were assigned during this curation and are not original AfriSpeech annotations. The five negation examples are explicit negatives. The remaining negative AfriSpeech rows are distractors, including textbook descriptions of bleeding, fever, seizures and swelling. No additional maternal symptoms are inferred from clinical terms.

AfriSpeech text was retained verbatim, including spacing, transcription artifacts and any embedded line breaks. CSV readers support quoted multiline fields; physical line counts may exceed record counts. The original synthetic text is preserved.

## Provenance fields

- `source`: synthetic_maternal or afrispeech_200_original.
- `source_row_id`: original E id for synthetic rows; original `idx` for AfriSpeech.
- `source_split`, `source_domain`, `source_accent`, `source_audio_id`, `source_audio_path`: retained upstream metadata for AfriSpeech. Blank accent/audio fields for synthetic examples.
- `source_url`, `source_license`: upstream location and licence for AfriSpeech rows. Blank synthetic licence fields do not assert a licence for that subset.

An accent is recording metadata, not something reliably inferred from written wording. These are English transcripts, not translations into the languages named in the accent field.

## Intended use and limits

Use this file to evaluate text-based sign extraction and false positives. To evaluate the entire voice workflow, obtain the corresponding audio, run speech recognition and compare symptom predictions from recognized text against these labels. The AfriSpeech recordings are prompted read speech; this sample does not establish performance on spontaneous community-health encounters.

Keep the original AfriSpeech test split out of training and prompt tuning if reporting held-out AfriSpeech results. The synthetic and original subsets should also be reported separately. Semantic and clinical labels here are assistant-curated; clinician adjudication has not been performed.

## Source and licence

Dataset: Intron / AfriSpeech-200.

Dataset card: https://huggingface.co/datasets/intronhealth/afrispeech-200

Transcript source: https://huggingface.co/datasets/intronhealth/afrispeech-200/resolve/main/transcripts/test.csv

Retrieved: 2026-10-04. Upstream test file contained 6,319 records. Local source-file SHA-256: `cf4df58547e137bc40be53001104ceca4bead21dc3a0617fae889bf4c90e8215`.

AfriSpeech original text is licensed CC BY-NC-SA 4.0. Attribution, noncommercial use and applicable share-alike requirements apply to that subset; this notice does not relicense it. Licence: https://creativecommons.org/licenses/by-nc-sa/4.0/

Citation: Olatunji et al. (2023), AfriSpeech-200: Pan-African Accented Speech Dataset for Clinical and General Domain ASR. https://aclanthology.org/2023.tacl-1.93/

## Label counts

Counts indicate records containing each label. Multi-label rows contribute to multiple symptom counts.

| Label | E001–E100 | E101–E200 | E201–E300 | E301–E400 | E401–E500 | Total |
|---|---:|---:|---:|---:|---:|---:|
| vaginal_bleeding | 6 | 5 | 7 | 5 | 1 | 24 |
| fainting | 5 | 5 | 6 | 5 | 0 | 21 |
| dizziness | 6 | 5 | 6 | 6 | 0 | 23 |
| headache | 7 | 6 | 7 | 5 | 0 | 25 |
| visual_disturbance | 5 | 7 | 5 | 6 | 0 | 23 |
| convulsions | 5 | 6 | 5 | 5 | 0 | 21 |
| fever | 6 | 6 | 7 | 7 | 0 | 26 |
| abdominal_pain | 7 | 7 | 5 | 7 | 0 | 26 |
| breathing_difficulty | 6 | 6 | 6 | 5 | 0 | 23 |
| unconscious | 6 | 5 | 5 | 6 | 0 | 22 |
| vomiting | 7 | 6 | 6 | 7 | 0 | 26 |
| reduced_fetal_movement | 5 | 6 | 6 | 7 | 0 | 24 |
| waters_broken | 5 | 6 | 6 | 6 | 0 | 23 |
| foul_discharge | 6 | 5 | 6 | 5 | 0 | 22 |
| swelling | 6 | 7 | 7 | 7 | 0 | 27 |
| none | 25 | 25 | 25 | 25 | 99 | 199 |

