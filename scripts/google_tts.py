"""Google Cloud Text-to-Speech — Chirp3-HD (highest quality), stdlib only.

Auth via `gcloud auth print-access-token`; project header bmount-public-share.
The voice's languageCode (el-GR) forces Modern-Greek pronunciation structurally, so an
isolated cognate can't be read with the wrong language's phonetics.
"""

import base64
import json
import subprocess
import urllib.request

from voices import voice_lang, voice_name

ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"
PROJECT = "bmount-public-share"

_token_cache = {"tok": None}


def _access_token():
    if _token_cache["tok"] is None:
        _token_cache["tok"] = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"], text=True
        ).strip()
    return _token_cache["tok"]


def synthesize(text, voice_key, rate=1.0):
    """Return MP3 bytes for `text` spoken by the registry voice `voice_key`.

    rate < 1.0 is slower (careful learner speech), > 1.0 faster (toward natural pace).
    """
    audio_cfg = {"audioEncoding": "MP3", "sampleRateHertz": 24000}
    if rate and rate != 1.0:
        audio_cfg["speakingRate"] = rate
    body = {
        "input": {"text": text},
        "voice": {"languageCode": voice_lang(voice_key), "name": voice_name(voice_key)},
        "audioConfig": audio_cfg,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_access_token()}",
            "x-goog-user-project": PROJECT,
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    return base64.b64decode(data["audioContent"])
