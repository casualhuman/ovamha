"""Danger-sign lexicon per language.

English terms are the baseline. Krio and Yoruba terms are a DRAFT and must be
reviewed by native-speaker health workers before any real use. Yoruba is matched
with tone marks stripped, because ASR output often omits them.
"""

# field -> {lang: [terms]}; a term is matched as a whole phrase in the normalised text.
FIELD_TERMS: dict[str, dict[str, list[str]]] = {
    "vaginal_bleeding": {
        "en": ["bleeding", "bleed", "bled", "blood coming", "losing blood", "vaginal bleeding", "blood", "bloody", "spotting",
               "seen her period", "saw her period", "seeing her period", "her period came", "red and wet"],
        "kri": ["blɔd", "blod", "bleed", "di blod de kam", "bleeding"],
        "yo": ["eje", "eje n jade", "bleeding"],
    },
    "dizziness": {
        "en": ["dizzy", "dizziness", "light headed", "lightheaded"],
        "kri": ["dizzy", "in ed de turn", "ed de turn"],
        "yo": ["oyi", "ori n yi", "dizzy"],
    },
    "fainting": {
        "en": ["fainted", "faint", "fainting", "passed out", "collapsed", "blacked out"],
        "kri": ["faint", "fainted", "fɔdɔm", "fodom"],
        "yo": ["daku", "o daku", "fainted"],
    },
    "headache": {
        "en": ["headache", "head ache", "head pain", "head is paining", "head is pounding", "head pounding", "pounding head",
               "head hurts", "head is hurting", "head is aching"],
        "kri": ["ed de at", "ed at", "headache"],
        "yo": ["ori fifo", "ori n fo", "efori", "headache"],
    },
    "visual_disturbance": {
        "en": ["blurred vision", "blurry", "blurred", "cannot see well", "can't see well", "seeing spots", "sees stars", "seeing stars",
               "flashes of light", "flashing lights", "eyes are dark", "vision is blurred", "vision is blurry"],
        "kri": ["in yay nɔ de si fayn", "yay de blur", "blurred"],
        "yo": ["oju n se baibai", "ko riran daadaa", "blurred"],
    },
    "convulsions": {
        "en": ["convulsion", "convulsions", "convulsing", "fits", "fitting", "seizure", "seizures"],
        "kri": ["fit", "fits", "konvulshɔn", "convulsion"],
        "yo": ["giri", "warapa", "convulsion"],
    },
    "fever": {
        "en": ["fever", "feverish", "hot body", "high temperature"],
        "kri": ["fiva", "fever", "skin at", "bɔdi at"],
        "yo": ["iba", "ara gbona", "fever"],
    },
    "abdominal_pain": {
        "en": ["abdominal pain", "belly pain", "stomach pain", "tummy pain", "pain in her belly", "pain in the abdomen"],
        "kri": ["bɛlɛ de at", "bele de at", "belle de at", "bɛlɛ at"],
        "yo": ["inu rirun", "inu n run", "irora inu"],
    },
    "breathing_difficulty": {
        "en": ["difficulty breathing", "short of breath", "shortness of breath", "can't breathe", "cannot breathe", "breathing fast"],
        "kri": ["nɔ de blo fayn", "in briz", "breathing"],
        "yo": ["ko le mi daadaa", "emi kuru", "breathing"],
    },
}

# Extra terms only the safety net looks for (no extraction field). Flags only; the worker decides.
SAFETY_NET_ONLY: dict[str, dict[str, list[str]]] = {
    "unconscious": {"en": ["unconscious", "not responding", "unresponsive"], "kri": ["nɔ de wek"], "yo": ["ko mo nnkan"]},
    "vomiting": {"en": ["vomiting", "vomit", "throwing up"], "kri": ["de vɔmit", "vomit"], "yo": ["eebi", "o n bi"]},
    "reduced_fetal_movement": {"en": ["baby not moving", "not feeling the baby", "baby stopped moving", "baby is not moving", "not kicking",
                                       "no kicks", "stopped kicking", "not moving like before", "not felt the baby", "not feeling kicks"], "kri": ["pikin nɔ de muv"], "yo": ["omo ko mi"]},
    "waters_broken": {"en": ["water broke", "waters broke", "leaking water", "water is running", "water running", "water coming out",
                              "water is coming", "fluid leaking", "leaking fluid", "draining liquor"], "kri": ["wata dɔn brok"], "yo": ["omi ti ja"]},
    "foul_discharge": {"en": ["foul smelling discharge", "smelly discharge", "bad smell discharge", "discharge smells"], "kri": ["discharge de smel"], "yo": ["isun olorun"]},
    "swelling": {"en": ["swelling", "swollen face", "swollen hands"], "kri": ["swɛl"], "yo": ["wiwu", "ese wu"]},
}

HEAVY_TERMS = {
    "en": ["heavy", "a lot", "lots of", "plenty", "soaking", "much blood", "heavily"],
    "kri": ["plenti", "bɔku", "boku", "tumɔs"],
    "yo": ["pupo", "opolopo"],
}
LIGHT_TERMS = {"en": ["light", "spotting", "a little", "small"], "kri": ["smɔl", "small"], "yo": ["die", "kekere"]}

NEGATIONS = {
    "en": ["no", "not", "denies", "without", "never", "none", "hasn't", "has not", "didn't", "doesn't"],
    "kri": ["nɔ", "no", "nor"],
    "yo": ["ko", "ki i", "ko si"],
}

# Mention is in the past or resolved: not captured as a current field; the safety net flags it.
PAST_OR_RESOLVED = {
    "en": ["yesterday", "last week", "last night", "earlier", "before", "but is fine now", "fine now", "is okay now", "ago", "previously"],
    "kri": ["yestade", "las wik", "bifo", "naw i fayn", "i dɔn bɛtɛ"],
    "yo": ["lanaa", "ose to koja", "teletele", "ara re ti ya"],
}

# Overrides PAST_OR_RESOLVED: "bleeding since yesterday" is current.
ONGOING = {"en": ["since", "still", "continues", "keeps", "right now", "now bleeding"], "kri": ["stil", "sins"], "yo": ["sibe", "lati"]}

WEEKS_WORDS ={"en": ["weeks", "week", "wks"], "kri": ["wik", "wiks", "weeks"], "yo": ["ose", "weeks"]}

NUMBER_WORDS_EN = {
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
}
UNITS_EN = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}

LANGUAGES = {"en": "English", "kri": "Krio", "yo": "Yoruba"}
