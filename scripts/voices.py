"""Voice registry for Ἑλληνικά.

Every voice carries a GENDER. Voice gender is structural, not cosmetic: a first-person
self-description must be spoken by a voice whose grammatical gender agrees with the form
(see gender_guard). Swap the two Chirp3-HD names to re-voice the whole course.

Modern Greek (el-GR) Chirp3-HD voices are used for ALL eras — one living sound-system
across Koine, Classical, and Modern, consistent with 'Greek as one continuous culture'.
"""

# key -> registry entry
VOICES = {
    "aoede":  {"name": "el-GR-Chirp3-HD-Aoede",  "gender": "f", "label": "Aoede"},   # a Muse
    "charon": {"name": "el-GR-Chirp3-HD-Charon", "gender": "m", "label": "Charon"},   # the ferryman
}

# default voice per grammatical gender — used for gendered self-description variants
BY_GENDER = {"f": "aoede", "m": "charon"}

# default narrator for third-person text (scripture, epic, history)
DEFAULT_NARRATOR = "charon"

# for variety when a clip has no assigned voice, alternate by index
ALTERNATE = ["charon", "aoede"]

LANGUAGE_CODE = "el-GR"


def voice_gender(key):
    return VOICES[key]["gender"]


def voice_name(key):
    return VOICES[key]["name"]
