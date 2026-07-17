"""Stitch a hands-free 'Audio Gym' lesson into ONE mp3.

Format (per lesson):
  1. THE WORDS — for each word: Greek word (voice A) · English translation · Greek word again.
  2. THE SENTENCES — a long graded series. For each: the Greek sentence (natural pauses),
     then an English teacher gives the translation and a one-point grammar explanation.

Why pre-stitched: mobile browsers throttle JS timers when the screen is off, so a live
client sequencer dies in a pocket. A single mp3 plays through a locked phone.

The teacher voice is configurable (--teacher en|charon|aoede|kore) so we can A/B an English
narrator vs. a Greek speaker reading the English (tighter Greek, slightly accented English).
Word clips must already exist (run build_audio.py first); sentence + explanation clips are
synthesized here and cached.

Usage:
    python3 scripts/build_gym.py --upload            # full lesson, English teacher
    python3 scripts/build_gym.py --sample --upload   # also a short Greek-voice-teacher sample
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

INTRO_VOICE = "charon"       # voice A that speaks each headword
ECHO_VOICE = "aoede"         # a second voice for variety in review


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


def synth(text, voice, slug):
    """Synthesize (cached) an arbitrary line; return its mp3 path."""
    key = hashlib.md5((voice + "|" + text).encode("utf-8")).hexdigest()[:10]
    p = os.path.join(TMP, f"{slug}-{key}.mp3")
    if not os.path.exists(p):
        with open(p, "wb") as f:
            f.write(google_tts.synthesize(text, voice))
    return p


def word_clip(wid, vk):
    p = os.path.join(OUT, f"v-{wid}--{vk}.mp3")
    if not os.path.exists(p):
        raise SystemExit(f"missing word clip v-{wid}--{vk} — run build_audio.py first")
    return p


def build_segments(lesson, teacher, sample=None):
    """Return an ordered list of mp3 paths (clips + silences) to concatenate."""
    seg = []

    def add(path, pause=0.0):
        seg.append(path)
        if pause:
            seg.append(silence(pause))

    if not sample:
        add(synth("Lesson one. First, the words. Listen, and say each one aloud.",
                  teacher, "cue-words"), 0.9)
        for w in lesson["words"]:
            add(word_clip(w["id"], INTRO_VOICE), 0.7)             # hear it
            add(synth(w["en"].split(";")[0].split("(")[0].strip(), teacher,
                      "g-" + w["id"]), 0.7)                        # meaning
            add(word_clip(w["id"], INTRO_VOICE), 1.2)             # again — say it

    add(synth("Now, sentences. I'll read the Greek, then explain it.",
              teacher, "cue-sent"), 1.0)
    sents = lesson["sentences"]
    if sample:
        sents = sents[:sample]
    for i, s in enumerate(sents):
        gv = s.get("voice", INTRO_VOICE)
        add(synth(s["gr"], gv, f"s-{lesson['id']}-{i}"), 0.9)     # Greek sentence
        add(synth(s["explain"], teacher, f"x-{lesson['id']}-{i}"), 1.3)  # teacher explains

    if not sample:
        add(synth("That's lesson one. We'll hear these words again, in new sentences, soon.",
                  teacher, "cue-end"), 0.0)
    return seg


def stitch(seg, out_path):
    listfile = os.path.join(TMP, "concat-" + os.path.basename(out_path) + ".txt")
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


def make(lesson, gym_id, teacher, upload, sample=None):
    out_path = os.path.join(OUT, gym_id + ".mp3")
    stitch(build_segments(lesson, teacher, sample), out_path)
    secs = duration(out_path)
    print(f"  ✓ {gym_id}.mp3  {secs//60}m{secs%60:02d}s  (teacher={teacher}"
          + (f", sample={sample} sentences" if sample else "") + ")")
    if upload:
        sh("gsutil", "-h", "Content-Type:audio/mpeg",
           "-h", "Cache-Control:public, max-age=31536000", "cp", out_path, GCS_DEST)
        print(f"    uploaded {gym_id}.mp3")
    return secs


def main():
    upload = "--upload" in sys.argv
    do_sample = "--sample" in sys.argv
    teacher = EN_VOICE
    if "--teacher" in sys.argv:
        teacher = sys.argv[sys.argv.index("--teacher") + 1]
    os.makedirs(TMP, exist_ok=True)

    vdoc = json.load(open(os.path.join(DATA, "vocab.json"), encoding="utf-8"))
    lessons_out = []
    for lesson in vdoc["lessons"]:
        secs = make(lesson, f"gym-{lesson['id']}", teacher, upload)
        entry = {"id": lesson["id"], "gym_id": f"gym-{lesson['id']}",
                 "title": lesson["title"], "seconds": secs,
                 "words": len(lesson["words"]), "sentences": len(lesson["sentences"]),
                 "teacher": teacher}
        if do_sample:
            sid = f"gym-{lesson['id']}-grvoice"
            ssecs = make(lesson, sid, "charon", upload, sample=4)
            entry["sample"] = {"gym_id": sid, "seconds": ssecs,
                               "teacher": "charon",
                               "label": "A/B: Greek voice reads the English"}
        lessons_out.append(entry)

    json.dump({"audio_base": "https://storage.googleapis.com/bmount-public-share/greek/",
               "prefix": "gg", "lessons": lessons_out},
              open(GYM_MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"gym manifest: {len(lessons_out)} lesson(s)")


if __name__ == "__main__":
    main()
