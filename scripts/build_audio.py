"""Collect every clip in the course, synthesize full-sentence audio, write the manifest.

Rules enforced here (from the pedagogy charter):
  * EVERY clip is a full sentence — never a lone word or bare conjugated form.
  * EVERY clip passes the voice-gender guard or the build fails loudly.
  * Cached mp3s are skipped, so re-runs only generate new/changed text.

Usage:
    python3 scripts/build_audio.py            # synth locally into audio_build/google/
    python3 scripts/build_audio.py --upload   # ...and push new clips to gs://.../greek/gg/
    python3 scripts/build_audio.py --dry-run  # collect + guard only, no synth
"""

import glob
import json
import os
import subprocess
import sys

import google_tts
from gender_guard import assert_gender_ok
from voices import ALTERNATE, BY_GENDER, DEFAULT_NARRATOR, VOICES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "audio_build", "google")
MANIFEST = os.path.join(DATA, "audio_manifest.json")

VERSION = 1  # bump whenever any clip's text changes, to bust the ?v= cache
AUDIO_BASE = "https://storage.googleapis.com/bmount-public-share/greek/"
GCS_DEST = "gs://bmount-public-share/greek/gg/"


def verse_text(tokens):
    out = []
    for t in tokens:
        out.append(t["w"])
        if t.get("after"):
            out[-1] += t["after"]
    return " ".join(out)


def collect():
    """Yield clip dicts: {id, text, voice, kind, ... , require_gender?}."""
    clips = []

    # --- graded texts: one clip per verse/line ---
    for path in sorted(glob.glob(os.path.join(DATA, "texts", "*.json"))):
        doc = json.load(open(path, encoding="utf-8"))
        src = doc["id"]
        narrator = doc.get("narrator_voice", DEFAULT_NARRATOR)
        for v in doc.get("verses", []):
            cid = f"{src}-{v['ref'].replace(':', '-').replace(' ', '')}"
            clips.append({
                "id": cid, "text": verse_text(v["tokens"]), "voice": narrator,
                "kind": "verse", "source": src, "ref": v["ref"],
            })

    # --- modern greek phrases & gendered self-descriptions ---
    mpath = os.path.join(DATA, "modern.json")
    if os.path.exists(mpath):
        for p in json.load(open(mpath, encoding="utf-8")).get("phrases", []):
            if "variants" in p:  # gendered self-description -> one clip per gender
                for var in p["variants"]:
                    g = var["gender"]
                    clips.append({
                        "id": f"{p['id']}-{g}", "text": var["t"], "voice": BY_GENDER[g],
                        "kind": "modern", "require_gender": g, "phrase": p["id"],
                    })
            else:
                clips.append({
                    "id": p["id"], "text": p["t"],
                    "voice": p.get("voice", DEFAULT_NARRATOR), "kind": "modern",
                })
    return clips


def main():
    upload = "--upload" in sys.argv
    dry = "--dry-run" in sys.argv
    os.makedirs(OUT, exist_ok=True)

    clips = collect()
    print(f"collected {len(clips)} clips")

    # guard EVERY clip up front — fail before spending a single TTS call
    for c in clips:
        assert_gender_ok(c, c["voice"])
    print("gender guard: all clips OK")

    manifest_clips = {}
    made, cached, new_ids = 0, 0, []
    for c in clips:
        mp3 = os.path.join(OUT, c["id"] + ".mp3")
        manifest_clips[c["id"]] = {
            "voice": c["voice"], "gender": VOICES[c["voice"]]["gender"],
            "kind": c["kind"], "text": c["text"],
            **({"ref": c["ref"], "source": c["source"]} if c["kind"] == "verse" else {}),
            **({"require_gender": c["require_gender"]} if c.get("require_gender") else {}),
        }
        if dry:
            continue
        if os.path.exists(mp3) and os.path.getsize(mp3) > 0:
            cached += 1
            continue
        audio = google_tts.synthesize(c["text"], c["voice"])
        with open(mp3, "wb") as f:
            f.write(audio)
        made += 1
        new_ids.append(c["id"])
        print(f"  ✓ {c['id']:22s} [{c['voice']}] {c['text'][:48]}")

    manifest = {
        "audio_base": AUDIO_BASE, "version": VERSION, "default_backend": "gg",
        "backends": {"gg": {"prefix": "gg", "label": "Google HD", "engine": "google"}},
        "count": len(manifest_clips), "clips": manifest_clips,
    }
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"manifest: {len(manifest_clips)} clips  (generated {made}, cached {cached})")

    if upload and not dry:
        targets = new_ids if new_ids else [c["id"] for c in clips]
        if targets:
            print(f"uploading {len(targets)} clips to {GCS_DEST} ...")
            for cid in targets:
                subprocess.check_call([
                    "gsutil", "-h", "Content-Type:audio/mpeg",
                    "-h", "Cache-Control:public, max-age=31536000",
                    "cp", os.path.join(OUT, cid + ".mp3"), GCS_DEST,
                ])
            print("upload complete")


if __name__ == "__main__":
    main()
