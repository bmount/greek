"""Voice registry for Ἑλληνικά.

Every voice carries a GENDER and a language. Voice gender is structural, not cosmetic:
a first-person self-description must be spoken by a voice whose grammatical gender agrees
with the form (see gender_guard).

We use THREE Greek speakers so the learner acquires the WORD, not one recording — people
often understand one voice and stumble on another. (A true child voice does not exist in
the el-GR catalogue, so the three are distinct adult timbres: a deeper man, a woman, and a
brighter/younger woman.) Modern Greek (el-GR) pronunciation is used for ALL eras.

An en-US voice supplies the English glosses for the shadowing / recall audio format.
"""

VOICES = {
    "charon": {"name": "el-GR-Chirp3-HD-Charon", "gender": "m", "lang": "el-GR", "label": "Charon", "role": "older man"},
    "aoede":  {"name": "el-GR-Chirp3-HD-Aoede",  "gender": "f", "lang": "el-GR", "label": "Aoede",  "role": "woman"},
    "kore":   {"name": "el-GR-Chirp3-HD-Kore",   "gender": "f", "lang": "el-GR", "label": "Kore",   "role": "younger woman"},
    "en":     {"name": "en-US-Chirp3-HD-Charon", "gender": "m", "lang": "en-US", "label": "English", "role": "gloss"},
}

# the three Greek speakers rotated across vocabulary audio
SPEAKERS = ["charon", "aoede", "kore"]

# default voice per grammatical gender (for gendered self-description variants)
BY_GENDER = {"f": "aoede", "m": "charon"}

# default narrator for third-person text (scripture, epic, history)
DEFAULT_NARRATOR = "charon"

EN_VOICE = "en"


def voice_gender(key):
    return VOICES[key]["gender"]


def voice_name(key):
    return VOICES[key]["name"]


def voice_lang(key):
    return VOICES[key]["lang"]
