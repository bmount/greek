"""Voice-gender safeguard.

The structural rule: a voice may only speak a first-person self-description whose
grammatical gender agrees with the voice's gender. A male voice must never utter the
feminine self-form (κουρασμένη), and a female voice never the masculine (κουρασμένος).

A clip declares its requirement explicitly with `require_gender: "m"|"f"`. Third-person
narration (scripture, epic, history) has no requirement and is always allowed. The build
runs assert_gender_ok on EVERY clip and fails loudly on any mismatch — we never ship an
unguarded clip.

As a second, defensive net, KNOWN_FEMININE / KNOWN_MASCULINE catch a few high-frequency
first-person predicate adjectives even if a clip forgot to declare require_gender.
"""

from voices import voice_gender

# High-frequency first-person predicate adjective self-forms (extend as content grows).
KNOWN_FEMININE = {
    "κουρασμένη", "έτοιμη", "σίγουρη", "χαρούμενη", "λυπημένη",
    "καινούρια", "μόνη", "ελεύθερη", "κουρασμενη",
}
KNOWN_MASCULINE = {
    "κουρασμένος", "έτοιμος", "σίγουρος", "χαρούμενος", "λυπημένος",
    "καινούριος", "μόνος", "ελεύθερος", "κουρασμενος",
}


class GenderGuardError(AssertionError):
    pass


def assert_gender_ok(clip, voice_key):
    """Raise GenderGuardError if voice_key may not speak this clip. Return True otherwise."""
    vg = voice_gender(voice_key)
    text = clip.get("text", "")

    req = clip.get("require_gender")
    if req and req != vg:
        raise GenderGuardError(
            f"clip {clip.get('id')!r} requires a {req!r} voice for its self-description "
            f"but was assigned {voice_key!r} ({vg!r}): {text!r}"
        )

    tokens = set(text.replace(",", " ").replace(".", " ").replace(";", " ").split())
    if vg == "m" and tokens & KNOWN_FEMININE:
        raise GenderGuardError(
            f"clip {clip.get('id')!r}: male voice {voice_key!r} would speak a feminine "
            f"self-form {sorted(tokens & KNOWN_FEMININE)} in: {text!r}"
        )
    if vg == "f" and tokens & KNOWN_MASCULINE:
        raise GenderGuardError(
            f"clip {clip.get('id')!r}: female voice {voice_key!r} would speak a masculine "
            f"self-form {sorted(tokens & KNOWN_MASCULINE)} in: {text!r}"
        )
    return True
