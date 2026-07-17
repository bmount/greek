"""Stitch a hands-free 'Audio Gym' lesson into ONE mp3 — AND publish each sentence and
its explanation as separately-playable clips (so the transcript is inspectable).

Format (per lesson):
  1. THE WORDS — for each word: Greek word (voice A) · English translation · Greek word.
  2. THE SENTENCES — for each: the Greek sentence (natural pauses), then a separate English
     narrator gives the translation + a one-point grammar explanation.

The Greek sentence clips (s-<lesson>-<i>) and explanation clips (x-<lesson>-<i>) are written
with deterministic ids, used in the stitch, AND uploaded individually so the app can play
them one at a time in the transcript. Word clips must exist first (run build_audio.py).

Usage: python3 scripts/build_gym.py [--upload]
"""

import hashlib
import json
import os
import subprocess
import sys

import google_tts
from voices import EN_VOICE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "audio_build", "google")
TMP = os.path.join(ROOT, "audio_build", "gym_tmp")
GYM_MANIFEST = os.path.join(DATA, "gym_manifest.json")
GCS_DEST = "gs://bmount-public-share/greek/gg/"

VERSION = 1
AUDIO_BASE = "https://storage.googleapis.com/bmount-public-share/greek/"
INTRO_VOICE = "charon"       # voice A that speaks each headword
TEACHER = EN_VOICE           # decided: a separate English narrator explains


def sh(*args):
    subprocess.run(args, check=True, capture_output=True)


def silence(sec):
    ms = int(round(sec * 1000))
    p = os.path.join(TMP, f"sil-{ms}.mp3")
    if not os.path.exists(p):
        sh("ffmpeg", "-y", "-f", "lavfi", "-i",
           "anullsrc=channel_layout=mono:sample_rate=24000", "-t", f"{sec}",
           "-c:a", "libmp3lame", "-b:a", "64k", p)
    return p


def cue(text, voice, slug):
    """Cached, disposable clip in TMP (cues, glosses) — not published individually."""
    key = hashlib.md5((voice + "|" + text).encode("utf-8")).hexdigest()[:10]
    p = os.path.join(TMP, f"{slug}-{key}.mp3")
    if not os.path.exists(p):
        with open(p, "wb") as f:
            f.write(google_tts.synthesize(text, voice))
    return p


def pub_clip(cid, text, voice):
    """A PUBLISHED clip (deterministic id) written to OUT — used in the stitch AND uploaded."""
    p = os.path.join(OUT, cid + ".mp3")
    if not os.path.exists(p):
        with open(p, "wb") as f:
            f.write(google_tts.synthesize(text, voice))
    return p


def word_clip(wid, vk):
    p = os.path.join(OUT, f"v-{wid}--{vk}.mp3")
    if not os.path.exists(p):
        raise SystemExit(f"missing word clip v-{wid}--{vk} — run build_audio.py first")
    return p


def build(lesson):
    """Return (segments, sentence_clip_ids)."""
    seg, pub = [], []

    def add(path, pause=0.0):
        seg.append(path)
        if pause:
            seg.append(silence(pause))

    add(cue("Lesson one. First, the words. Listen, and say each one aloud.", TEACHER, "cue-words"), 0.9)
    for w in lesson["words"]:
        add(word_clip(w["id"], INTRO_VOICE), 0.7)
        add(cue(w["en"].split(";")[0].split("(")[0].strip(), TEACHER, "g-" + w["id"]), 0.7)
        add(word_clip(w["id"], INTRO_VOICE), 1.2)

    add(cue("Now, sentences. I'll read the Greek, then explain it.", TEACHER, "cue-sent"), 1.0)
    clips = []
    for i, s in enumerate(lesson["sentences"]):
        gid, xid = f"s-{lesson['id']}-{i}", f"x-{lesson['id']}-{i}"
        add(pub_clip(gid, s["gr"], s.get("voice", INTRO_VOICE)), 0.9)
        add(pub_clip(xid, s["explain"], TEACHER), 1.3)
        clips.append({"gr": gid, "ex": xid})
        pub += [gid, xid]

    add(cue("That's lesson one. We'll hear these words again, in new sentences, soon.", TEACHER, "cue-end"), 0.0)
    return seg, clips, pub


def stitch(seg, out_path):
    listfile = os.path.join(TMP, "concat-" + os.path.basename(out_path) + ".txt")
    with open(listfile, "w") as f:
        for p in seg:
            f.write("file '%s'\n" % p.replace("'", "'\\''"))
    sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
       "-c:a", "libmp3lame", "-b:a", "64k", "-ar", "24000", "-ac", "1", out_path)


def duration(path):
    return round(float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path], text=True).strip()))


def upload(cid):
    sh("gsutil", "-h", "Content-Type:audio/mpeg", "-h", "Cache-Control:public, max-age=31536000",
       "cp", os.path.join(OUT, cid + ".mp3"), GCS_DEST)


def main():
    do_upload = "--upload" in sys.argv
    os.makedirs(TMP, exist_ok=True)
    vdoc = json.load(open(os.path.join(DATA, "vocab.json"), encoding="utf-8"))
    lessons_out = []
    for lesson in vdoc["lessons"]:
        gym_id = f"gym-{lesson['id']}"
        seg, clips, pub = build(lesson)
        out_path = os.path.join(OUT, gym_id + ".mp3")
        stitch(seg, out_path)
        secs = duration(out_path)
        print(f"  ✓ {gym_id}.mp3  {secs//60}m{secs%60:02d}s  (+{len(pub)} sentence clips)")
        if do_upload:
            upload(gym_id)
            for cid in pub:
                upload(cid)
            print(f"    uploaded lesson + {len(pub)} clips")
        lessons_out.append({
            "id": lesson["id"], "gym_id": gym_id, "title": lesson["title"],
            "seconds": secs, "words": len(lesson["words"]),
            "sentences": len(lesson["sentences"]), "sentence_clips": clips,
        })
    json.dump({"audio_base": AUDIO_BASE, "prefix": "gg", "version": VERSION,
               "lessons": lessons_out},
              open(GYM_MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"gym manifest: {len(lessons_out)} lesson(s)")


if __name__ == "__main__":
    main()
