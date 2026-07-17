"""Stitch a hands-free 'Audio Gym' lesson into ONE mp3 (Pimsleur-modernized).

Why pre-stitched: mobile browsers throttle JS timers when the screen is off, so a live
client-side sequencer dies in your pocket. A single mp3 plays through a locked phone.

Structure per lesson:
  1. Introduce each word — shadow rhythm: word (voice A) · English · word (voice A, pause
     to repeat aloud) · word (voice B).
  2. Recognition drills — English → (pause) → word.
  3. Simple sentences — the escalating phrases, in varied voices.
  4. Cumulative review — English → (pause) → word, for the whole set.

Needs the per-word/phrase clips already synthesized locally (run build_audio.py first).
Silences and short English cues are generated on the fly with ffmpeg / TTS.

Usage: python3 scripts/build_gym.py [--upload]
"""

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


def sh(*args):
    subprocess.run(args, check=True, capture_output=True)


def silence(sec):
    """Return path to a cached silence mp3 of `sec` seconds (matched encode params)."""
    ms = int(round(sec * 1000))
    p = os.path.join(TMP, f"sil-{ms}.mp3")
    if not os.path.exists(p):
        sh("ffmpeg", "-y", "-f", "lavfi", "-i",
           "anullsrc=channel_layout=mono:sample_rate=24000",
           "-t", f"{sec}", "-c:a", "libmp3lame", "-b:a", "64k", p)
    return p


def cue(text, slug):
    """Return path to a cached English instruction clip."""
    p = os.path.join(TMP, f"cue-{slug}.mp3")
    if not os.path.exists(p):
        with open(p, "wb") as f:
            f.write(google_tts.synthesize(text, EN_VOICE))
    return p


def clip(cid):
    p = os.path.join(OUT, cid + ".mp3")
    if not os.path.exists(p):
        raise SystemExit(f"missing clip {cid} — run build_audio.py first")
    return p


def build_lesson(lesson):
    words = lesson["words"]
    seg = []  # list of file paths (clips + silences), concatenated in order

    def add(path, pause=0.0):
        seg.append(path)
        if pause:
            seg.append(silence(pause))

    add(cue("Lesson one. Listen, and repeat each word aloud.", "intro"), 0.8)

    # 1) introduce each word (shadow rhythm)
    for w in words:
        wid = w["id"]
        add(clip(f"v-{wid}--charon"), 1.1)      # hear it
        add(clip(f"v-{wid}--en"), 1.1)          # meaning
        add(clip(f"v-{wid}--charon"), 1.7)      # hear it again — say it aloud now
        add(clip(f"v-{wid}--aoede"), 1.0)       # a second voice

    # 2) recognition drills — English, then (pause), then the word
    add(cue("Now, can you say these in Greek?", "recog"), 0.9)
    for i, w in enumerate(words):
        wid = w["id"]
        vk = ["charon", "aoede", "kore"][i % 3]
        add(clip(f"v-{wid}--en"), 1.9)          # think...
        add(clip(f"v-{wid}--{vk}"), 0.9)        # ...answer

    # 3) simple sentences — the escalating phrases
    add(cue("Some sentences.", "sent"), 0.9)
    for w in words:
        wid = w["id"]
        for pi, ph in enumerate(w.get("phrases", []), 1):
            vk = ["charon", "aoede", "kore"][pi % 3]
            pth = os.path.join(OUT, f"v-{wid}-p{pi}--{vk}.mp3")
            if os.path.exists(pth):
                add(pth, 1.4)

    # 4) cumulative review
    add(cue("Let's review. What do these mean?", "review"), 0.9)
    for i, w in enumerate(words):
        wid = w["id"]
        vk = ["aoede", "kore", "charon"][i % 3]
        add(clip(f"v-{wid}--{vk}"), 1.8)        # hear Greek...
        add(clip(f"v-{wid}--en"), 0.8)          # ...meaning
    add(cue("End of lesson one. Well done.", "outro"), 0.0)

    return seg


def stitch(seg, out_path):
    listfile = os.path.join(TMP, "concat.txt")
    with open(listfile, "w") as f:
        for p in seg:
            f.write("file '%s'\n" % p.replace("'", "'\\''"))
    sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
       "-c:a", "libmp3lame", "-b:a", "64k", "-ar", "24000", "-ac", "1", out_path)


def duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path], text=True).strip()
    return round(float(out))


def main():
    upload = "--upload" in sys.argv
    os.makedirs(TMP, exist_ok=True)
    vdoc = json.load(open(os.path.join(DATA, "vocab.json"), encoding="utf-8"))
    lessons_out = []
    for lesson in vdoc["lessons"]:
        gym_id = f"gym-{lesson['id']}"
        out_path = os.path.join(OUT, gym_id + ".mp3")
        seg = build_lesson(lesson)
        stitch(seg, out_path)
        secs = duration(out_path)
        print(f"  ✓ {gym_id}.mp3  {secs//60}m{secs%60:02d}s  ({len(seg)} segments)")
        lessons_out.append({
            "id": lesson["id"], "gym_id": gym_id, "title": lesson["title"],
            "seconds": secs, "words": len(lesson["words"]),
        })
        if upload:
            sh("gsutil", "-h", "Content-Type:audio/mpeg",
               "-h", "Cache-Control:public, max-age=31536000",
               "cp", out_path, GCS_DEST)
            print(f"    uploaded {gym_id}.mp3")

    json.dump({"audio_base": "https://storage.googleapis.com/bmount-public-share/greek/",
               "prefix": "gg", "lessons": lessons_out},
              open(GYM_MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"gym manifest: {len(lessons_out)} lesson(s)")


if __name__ == "__main__":
    main()
