"""Generate template training sentences for the danger-sign text classifier.

Written from our own phrase banks (not copied from the evaluation set). Covers the
label rules in ml/eval/text/README.md: a sign counts when the pregnant woman has it
now or had it recently; denied signs, other people's signs, hypothetical risks,
health education and look-alike words ("blood pressure", "blood sample") do not.

Output: ml/textclf/data/generated.jsonl, one {"text", "labels"} per line.
Usage: .venv/bin/python ml/textclf/make_training_data.py [--n 4000] [--seed 7]
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data/generated.jsonl"

# sign -> noun phrases (for negation / education), present verb phrases, recent-past verb phrases.
# Verb phrases are 3rd person and follow a subject ("She ...").
BANK: dict[str, dict[str, list[str]]] = {
    "vaginal_bleeding": {
        "np": ["vaginal bleeding", "bleeding from the vagina", "blood from her private part", "any bleeding", "spotting"],
        "vp": ["is bleeding from her vagina", "has blood coming from her private part", "is losing blood from below",
               "has bright red blood on her cloth", "is passing blood clots from the vagina", "has blood running down her legs",
               "keeps soaking her pads with blood", "has some spotting of blood on her underwear", "is seeing her period even though she is pregnant",
               "has fresh blood from the birth canal"],
        "past": ["bled from her vagina", "saw blood on her wrapper", "passed some blood from below", "found blood on her pad"],
    },
    "fainting": {
        "np": ["fainting", "any fainting spells", "blackouts"],
        "vp": ["keeps fainting", "faints when she stands up", "collapses when she tries to walk"],
        "past": ["fainted", "passed out for a short time", "blacked out and fell", "collapsed and woke up after a minute",
                 "fell down and lost consciousness briefly", "went limp and fell to the ground"],
    },
    "dizziness": {
        "np": ["dizziness", "any dizziness", "a spinning feeling"],
        "vp": ["feels dizzy", "says the room is spinning", "feels light headed when she stands", "feels her head turning",
               "is unsteady and needs to hold the wall", "feels giddy all the time"],
        "past": ["felt dizzy", "felt the room spin", "became light headed"],
    },
    "headache": {
        "np": ["headache", "head pain", "any pain in the head"],
        "vp": ["has a severe headache", "has a pounding headache", "says her head is paining her badly", "has pain all over her head",
               "complains of a throbbing pain in her forehead", "has a headache that will not go away", "holds her head because it hurts"],
        "past": ["had a strong headache", "woke up with a bad headache", "had head pain all night"],
    },
    "visual_disturbance": {
        "np": ["blurred vision", "any problem with her eyes", "changes in her eyesight"],
        "vp": ["has blurred vision", "cannot see clearly", "is seeing flashing lights", "sees spots in front of her eyes",
               "says everything looks blurry", "says her eyes are seeing double", "says her sight has become dim"],
        "past": ["had blurred vision", "saw flashing lights", "could not see clearly"],
    },
    "convulsions": {
        "np": ["convulsions", "fits", "seizures", "any jerking"],
        "vp": ["is convulsing", "is having fits", "is shaking and jerking all over", "is having a seizure"],
        "past": ["had a fit", "had a convulsion", "had a seizure", "shook and jerked with her eyes rolled up",
                 "stiffened and jerked on the floor", "had fits two times"],
    },
    "fever": {
        "np": ["fever", "a high temperature", "any hotness of the body"],
        "vp": ["has a fever", "has a high fever", "feels very hot", "has a hot body", "is shivering with fever",
               "has a temperature of thirty nine degrees", "is burning hot to touch", "is feverish"],
        "past": ["had a fever", "had a high temperature", "was hot and shivering"],
    },
    "abdominal_pain": {
        "np": ["abdominal pain", "belly pain", "stomach pain", "pain in the abdomen"],
        "vp": ["has severe abdominal pain", "has strong belly pain", "says her stomach is paining her", "has sharp pain in her lower belly",
               "is crying with pain in her abdomen", "has cramping pain across her belly", "holds her belly because of the pain"],
        "past": ["had bad belly pain", "had sharp pain in her abdomen", "had stomach pain"],
    },
    "breathing_difficulty": {
        "np": ["difficulty breathing", "shortness of breath", "breathing problems"],
        "vp": ["is struggling to breathe", "is short of breath", "is breathing very fast", "cannot catch her breath",
               "says she cannot breathe well", "gasps for air even when resting", "is breathless after a few steps"],
        "past": ["struggled to breathe", "was short of breath", "could not catch her breath"],
    },
    "unconscious": {
        "np": ["loss of consciousness", "unconsciousness"],
        "vp": ["is unconscious", "is not responding", "does not wake up when we call her", "is unresponsive",
               "lies still and does not answer", "cannot be woken"],
        "past": ["became unconscious", "was found unresponsive", "stopped responding"],
    },
    "vomiting": {
        "np": ["vomiting", "any vomiting"],
        "vp": ["is vomiting", "keeps vomiting", "is throwing up everything she eats", "cannot keep food down",
               "vomits after every meal", "is vomiting again and again"],
        "past": ["vomited", "threw up", "vomited many times", "brought up all her food"],
    },
    "reduced_fetal_movement": {
        "np": ["reduced baby movement", "any change in the baby's movement"],
        "vp": ["says the baby is not moving", "has not felt the baby kick today", "feels the baby moving much less",
               "says the baby has stopped moving", "cannot feel the baby moving", "says the baby is quiet and not kicking"],
        "past": ["stopped feeling the baby move", "noticed the baby moving less", "did not feel any kicks"],
    },
    "waters_broken": {
        "np": ["leaking of water", "broken waters", "fluid from the vagina"],
        "vp": ["has water running from her vagina", "is leaking fluid from below", "has clear liquid coming out",
               "says her water is draining", "is wet with fluid from the birth canal"],
        "past": ["felt her waters break", "had a gush of water from her vagina", "noticed water pouring out"],
    },
    "foul_discharge": {
        "np": ["foul smelling discharge", "smelly discharge", "bad smelling fluid"],
        "vp": ["has a smelly vaginal discharge", "has discharge with a bad smell", "has a rotten smelling discharge",
               "says the fluid from her private part smells bad", "has yellow discharge that smells offensive"],
        "past": ["noticed a smelly discharge", "had a bad smelling discharge"],
    },
    "swelling": {
        "np": ["swelling", "swollen feet", "puffiness of the face"],
        "vp": ["has swollen feet", "has swelling of her face", "has puffy hands", "says her legs are swollen",
               "has swelling around her eyes", "cannot wear her shoes because her feet are swollen", "has swelling of her hands and face"],
        "past": ["noticed her feet swelling", "had a swollen face", "woke up with puffy eyes and hands"],
    },
}
SIGNS = list(BANK)

SUBJ = ["She", "The woman", "The mother", "My client", "This pregnant woman", "Madam", "The patient"]
REPORT = ["", "", "She says she ", "She told me she ", "Her husband says she ", "She reports that she "]
NOW = ["", "", " since this morning", " today", " right now", " for two days", " since last night", " now"]
RECENT = [" yesterday", " last night", " this morning", " two days ago", " earlier today", " on the way here"]
OTHER = ["Her sister", "Her mother", "Her child", "Her neighbour", "Her husband", "Another woman in the village", "Her friend"]
NEG_FRAMES = ["She denies {np}.", "There is no {np}.", "She has not had any {np}.", "No {np} today.",
              "She does not have {np}.", "She says there is no {np}.", "We checked and found no {np}."]
EDU_FRAMES = ["We explained that {np} is a danger sign.", "Come back quickly if you notice {np}.",
              "Tell her to watch out for {np}.", "If she gets {np}, she must go to the hospital.",
              "The poster lists {np} as a warning sign.", "We discussed {np} during the health talk."]
DISTRACTORS = ["We took a blood sample for her routine tests.", "Her blood pressure is normal today.",
               "Her blood group is O positive.", "The baby moved well during the examination.",
               "She drinks plenty of water every day.", "Her temperature is normal.", "She is breathing normally.",
               "She came for her routine antenatal visit.", "She is 24 weeks pregnant and feels well.",
               "The laboratory needs another blood tube.", "She took her iron tablets this morning.",
               "She walked to the clinic with her sister.", "Her last visit was four weeks ago.",
               "She wants to know when to come back.", "The baby's heart rate is normal."]


def pos_sentence(sign: str, r: random.Random) -> str:
    b = BANK[sign]
    if r.random() < 0.3:
        return f"{r.choice(SUBJ)} {r.choice(b['past'])}{r.choice(RECENT)}."
    rep = r.choice(REPORT)
    vp = r.choice(b["vp"]) + r.choice(NOW)
    return f"{rep}{vp}." if rep else f"{r.choice(SUBJ)} {vp}."


def neg_sentence(sign: str, r: random.Random) -> str:
    return r.choice(NEG_FRAMES).format(np=r.choice(BANK[sign]["np"]))


def neg_list_sentence(signs: list[str], r: random.Random) -> str:
    nps = [r.choice(BANK[s]["np"]) for s in signs]
    return f"She denies {', '.join(nps[:-1])} and {nps[-1]}." if r.random() < 0.5 else f"No {', no '.join(nps)}."


def other_sentence(sign: str, r: random.Random) -> str:
    vp = r.choice(BANK[sign]["vp"] + BANK[sign]["past"])
    tail = r.choice(["", " but she herself is well", " but this woman feels fine"])
    return f"{r.choice(OTHER)} {vp}{tail}."


def edu_sentence(sign: str, r: random.Random) -> str:
    return r.choice(EDU_FRAMES).format(np=r.choice(BANK[sign]["np"]))


def example(r: random.Random) -> dict:
    kind = r.choices(["pos", "pos2", "neg", "neglist", "other", "edu", "distract", "mixed"],
                     weights=[30, 10, 12, 6, 10, 8, 8, 16])[0]
    a, b, c = r.sample(SIGNS, 3)
    if kind == "pos":
        return {"text": pos_sentence(a, r), "labels": [a]}
    if kind == "pos2":
        return {"text": f"{pos_sentence(a, r)} {pos_sentence(b, r)}", "labels": [a, b]}
    if kind == "neg":
        return {"text": neg_sentence(a, r), "labels": []}
    if kind == "neglist":
        return {"text": neg_list_sentence([a, b, c][: r.choice([2, 3])], r), "labels": []}
    if kind == "other":
        return {"text": other_sentence(a, r), "labels": []}
    if kind == "edu":
        return {"text": edu_sentence(a, r), "labels": []}
    if kind == "distract":
        return {"text": r.choice(DISTRACTORS), "labels": []}
    # mixed: one real sign next to a negated, other-person or education sentence
    noise = r.choice([neg_sentence(b, r), other_sentence(b, r), edu_sentence(b, r), r.choice(DISTRACTORS)])
    parts = [pos_sentence(a, r), noise]
    r.shuffle(parts)
    return {"text": " ".join(parts), "labels": [a]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    r = random.Random(a.seed)
    seen, rows = set(), []
    while len(rows) < a.n:
        ex = example(r)
        if ex["text"] not in seen:
            seen.add(ex["text"]); rows.append(ex)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for ex in rows:
            f.write(json.dumps(ex) + "\n")
    print(f"wrote {len(rows)} examples to {OUT}")


if __name__ == "__main__":
    main()
