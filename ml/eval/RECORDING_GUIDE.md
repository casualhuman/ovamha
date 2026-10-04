# Recording the Krio and Yoruba evaluation set

Goal: measure how many danger signs MaternalSave catches when health workers describe a situation **in their own words**, and the speech-recognition error rate, in Krio, Yoruba and English. Report only what is measured, with the number of recordings.

## Who records

- Native speakers of Krio and of Yoruba, ideally nurses, midwives or CHWs (they know how symptoms are described in clinic).
- At least 2 speakers per language; 3 to 5 is better. Note each speaker's language, sex and age band only. No names in the files.
- Written consent from every speaker to use their voice for testing (template below). **Never record real patients.**
- **Ethics approval first:** recording people to test models is health research; get written ethical clearance from the Sierra Leone Ethics and Scientific Review Committee (MoHS HIS Policy 2021, s.3.5.10(d)). See [docs/privacy/voice-data.md](../../docs/privacy/voice-data.md).
- **Testing only, never training:** the consent below covers testing. Do not use these recordings to train or fine-tune a model unless the speaker signs a separate consent that says so.

## How

1. Open `scenario_cards.csv`. For each card, the speaker reads the situation silently, then describes it to the phone **as they would to a colleague**, in Krio or Yoruba. Do not translate word for word; paraphrase is the point. 10 to 30 seconds each.
2. Record on a phone like the ones in the field, 16 kHz mono if possible (any format is fine; MaternalSave converts). Record half in a quiet room and half with normal clinic background noise. No noise filtering.
3. Save as `<lang>_<speaker>_<card>.wav`, e.g. `kri_s1_S03.wav`, `yo_s2_S12.wav`.
4. The speaker (or another native speaker) types **exactly what was said**, in the language, into `manifest.csv`. This reference transcript gives the speech-recognition error rate.
5. If a speaker said something different from the card (e.g. forgot a sign), note it in `manifest.csv` so the expected answer matches what was actually said.

Minimum for the hackathon: 20 cards x 2 speakers x 2 languages = 80 clips (about 1 hour of recording). English: the same, if time allows.

## Files

- Audio goes in `data/eval/audio/` (git-ignored: **never commit audio**).
- `ml/eval/manifest.csv`: `file,lang,speaker,card,transcript,notes`.
- Results go in `ml/eval/results/` (only measured numbers, with the count of clips).

## Consent (read to the speaker, keep the signed copy)

"We are testing a voice assistant for maternal health. We will record you describing made-up situations, not real patients. Your recordings will only be used to test the assistant, will be stored without your name, and will not be published. You can stop at any time and ask us to delete your recordings."

Speaker code: ______  Language: ______  Signature: ______  Date: ______
