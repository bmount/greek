# Language Course Creator — Reference & Playbook

A reusable blueprint for spinning up a new **bridge-language course** app fast, reusing
the exact cloud + hosting stack behind *Français pour bébas*. Hand this file to an
assistant (or yourself) at the start of a new project. It replaces the hardcoded
"teen girl going to Nice, Spanish→French" assumptions with a short **intake interview**,
then lays out the architecture, schemas, scripts, pedagogy rules, and deploy flow so the
next course is mostly assembly, not invention.

> **The core idea.** Teach a *target language* by leaning on a *bridge language* the
> learner already knows well, exploiting cognates so reading/understanding feels
> immediately possible. The bridge language is the language of instruction. Everything
> below is parameterized on that pair plus the learner's profile.

---

## Phase 0 — Audience intake (do this FIRST, before any content)

Ask these questions and record the answers as the **project spec**. Everything else keys
off them. Prefer to infer sensible defaults and confirm, rather than interrogate; if the
user gives answers as prose, extract the intent.

**Languages**
1. **Target language** — what are they learning? (locale, e.g. `it-IT`, `pt-BR`, `de-DE`)
2. **Bridge language** — their strongest language, used for all instruction/glosses and
   cognate leverage. (e.g. Spanish, English, Portuguese)
3. **Second gloss language?** — optional toggle shown on demand (default off/secondary).
   In *frances* this was English behind an ES/EN toggle, ES default.

**Learner**
4. **Who** — age, reading level, interests (drives themes: teen slang vs. professional).
5. **Grammatical gender of the learner** — load-bearing for the voice-gender safeguard
   and first-person self-descriptions ("je suis fatiguée"). If multiple users, note it.
6. **Register** — colloquial/spoken, formal, or both? Sets the "charter" (below).

**Goal & scope**
7. **Why / context** — trip, exam, heritage, work. Gives the culture modules and
   place-based readings a spine (destination city, domain vocab).
8. **Timeframe & size** — target vocabulary (e.g. >1000 words), number of modules,
   difficulty ceiling for readings (levels 1–5).

**Production**
9. **Target-language TTS voices** — pick 1 male + 1 female high-quality voice in the
   target locale (see *Cloud* below to list them). Voice gender is structural, not cosmetic.
10. **Naming** — `<slug>` (kebab-case project + repo name), `<PREFIX>` (short cache prefix
    for the service worker, e.g. `fpb`). Live URL becomes
    `https://<github-user>.github.io/<slug>/`.

Output of Phase 0 is a small table of these values. Treat them as the only things that
change between projects; the machinery below is language-agnostic.

---

## Reused cloud & hosting (no new accounts needed)

Everything runs on the **existing** GCP project and GitHub account.

### GCP — audio hosting on Google Cloud Storage
- **Project & bucket:** `bmount-public-share` (bucket of the same name).
- **Per-project path:** `gs://bmount-public-share/<slug>/`, with **backend subfolders**:
  - `gg/` — Google Chirp3-HD (default, exclusive for new content)
  - `el/` — ElevenLabs (legacy/optional swappable backend)
- **Public read + CORS** (one-time per bucket, already done for this bucket — repeat only
  on a fresh bucket):
  ```bash
  # public read
  gcloud storage buckets add-iam-policy-binding gs://bmount-public-share \
    --member=allUsers --role=roles/storage.objectViewer
  # CORS (GET from anywhere)
  printf '[{"origin":["*"],"method":["GET"],"responseHeader":["Content-Type"],"maxAgeSeconds":3600}]' > /tmp/cors.json
  gcloud storage buckets update gs://bmount-public-share --cors-file=/tmp/cors.json
  ```
- **Served URL base:** `https://storage.googleapis.com/bmount-public-share/<slug>/`
- **Upload clips** (long cache; content-type matters for iOS Safari):
  ```bash
  gcloud storage cp audio_build/google/*.mp3 \
    gs://bmount-public-share/<slug>/gg/ \
    --content-type=audio/mpeg --cache-control="public, max-age=31536000"
  ```

### GCP — Text-to-Speech (Chirp3-HD, highest quality)
- REST endpoint: `https://texttospeech.googleapis.com/v1/text:synthesize`
- Auth: `gcloud auth print-access-token`; header `x-goog-user-project: bmount-public-share`.
- Voice names are locale-specific Chirp3-HD, e.g. French used
  `fr-FR-Chirp3-HD-Aoede` (f) and `fr-FR-Chirp3-HD-Charon` (m).
- **List available voices for a new target locale** (pick one per gender):
  ```bash
  curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "x-goog-user-project: bmount-public-share" \
    "https://texttospeech.googleapis.com/v1/voices?languageCode=<xx-XX>" \
  | python3 -c "import sys,json;[print(v['name'],v['ssmlGender']) for v in json.load(sys.stdin)['voices'] if 'Chirp3-HD' in v['name']]"
  ```
- **Structural safeguard:** the voice's `languageCode` forces target-language
  pronunciation, so a bare cognate can't be read with the wrong language's phonetics.
  (This is why we moved off ad-hoc TTS: isolated cognates got mispronounced.)

### GitHub Pages — free static hosting
- Static SPA, **no build step**. Source on `main`, site served from `gh-pages`.
- **Deploy = push both branches:**
  ```bash
  git push origin main && git push origin main:gh-pages
  ```
- Pages occasionally serves stale; re-trigger with an empty commit if needed. Verify the
  raw branch first (`raw.githubusercontent.com/...`), then the Pages URL.

---

## Project scaffold (files)

```
<slug>/
  index.html                 # landing: course map (module list, counts)
  app.html                   # the whole SPA (inline JS/CSS, no build)
  manifest.json  sw.js  icon.svg     # PWA (sw versioned "<PREFIX>-vNN")
  data/
    curriculum/lesson_00_*.json … lesson_NN_*.json
    stories.json             # graded readings (lectures)
    quiz_culture.json        # target-language-only culture MC
    spoken_grammar.json      # tense system + bridge-language "traps"
    spoken_essentials.json   # register / how people really talk
    audio_manifest.json      # generated: backends, version, clip index
  scripts/
    synth.py                 # backend dispatch (google | elevenlabs)
    google_tts.py            # Chirp3-HD REST
    tts.py                   # ElevenLabs (optional)
    voices.py                # voice registry — each voice has a GENDER
    gender_guard.py          # assert self-descriptions match voice gender
    build_audio.py           # collect clips → generate → write manifest
  docs/                      # charter, curriculum map, this file
  audio_build/<backend>/     # local generated mp3s (gitignored)
```

Fastest start: **copy this repo**, wipe `data/`, keep `scripts/`, `app.html`, `sw.js`,
`index.html`, then re-parameterize (see checklist at the end).

---

## Data schemas

Field names below use `fr`/`es` from the original; **rename to `t` (target) / `b`
(bridge)** or just keep `fr`/`es` as generic slots — the app only cares about position.
Keep it consistent with whatever the renderer reads.

### Lesson — `data/curriculum/lesson_NN_slug.json`
```jsonc
{
  "id": "L07", "order": 7, "slug": "verbs-er",
  "title": "<target title>", "es_title": "<bridge title>",
  "focus": "<one-line bridge-language framing>",
  "objectives": ["…","…"],
  "orientation": {                     // "how it's formed" box, bridge default + gloss toggle
    "title_es": "…", "title_en": "…",
    "es": "<HTML>", "en": "<HTML>"     // use .fx (target words), .opat (pattern), .oform (table)
  },
  "reader": [                          // bilingual reader, target-first
    { "t": "h3", "text": "<target heading>" },
    { "t": "pair", "fr": "<target sentence>", "es": "<literal bridge>", "en": "<gloss>" }
  ],
  "vocab": [
    { "id":"L07-x", "fr":"…", "es":"…", "en":"…", "ipa":"…", "pos":"verb",
      "cognate_type":"transparent|semi|non_cognate", "star":true,
      "gender":"m|f",                  // for nouns → drives le/la quiz
      "ex":"<full sentence>", "voice":"emilie", "audio":"L07-x" }
  ],
  "sentences": [ { "id":"L07-s01","fr":"…","es":"…","en":"…","voice":"oris","audio":"L07-s01" } ],
  "drills": [                          // concept MC → auto-feeds the Grammar quiz
    { "q":"…","sub":"…","ans":"…","opts":["…","…","…","…"] }
  ],
  // OPTIONAL for conjugation modules:
  "grammar": { "conjugation": { "verb":"…","present":[{"pron":"je","form":"…","ex":"…","audio":"…"}] },
               "spoken_notes":["…"] }
}
```
Gendered self-description items carry `fr_m`/`fr_f` + `audio_m`/`audio_f` (e.g.
fatigué/fatiguée) so the male and female voices each say their own agreeing form.

### Story / graded reading — `data/stories.json`
```jsonc
{ "stories": [
  { "id":"ST5","order":5,"level":2,"level_label":"2 · <short bridge tag>",
    "title":"<target>","title_es":"<bridge>",
    "narrator":"m|f|none","voice":"oris","audio":"ST5",
    "vocab":[{ "fr":"…","es":"…","en":"…" }],   // ONLY the non-guessable words
    "text":"<one flowing target-language passage>" }
] }
```
Cards show a **sequential number** with **★ difficulty**; `level` is 1–5.

### Audio manifest — `data/audio_manifest.json` (generated)
```jsonc
{ "audio_base":"https://storage.googleapis.com/bmount-public-share/<slug>/",
  "version": 6, "default_backend":"gg",
  "backends": { "gg":{"prefix":"gg","label":"Google HD","engine":"google"},
                "el":{"prefix":"el","label":"ElevenLabs","engine":"elevenlabs"} },
  "count": 810, "clips": { "<audio_id>": {…} } }
```
The app builds each URL as `audio_base + prefix + "/" + id + ".mp3?v=" + version`.

---

## Audio build pipeline

`scripts/build_audio.py`:
1. `collect()` globs every lesson + `stories.json` + essentials and yields
   `(audio_id, text, voice_key)` for each clip.
2. **Every clip is a full SENTENCE.** Isolated words/conjugated forms are voiced via their
   `ex` field — bare tokens mispronounce even on the enforced model.
3. Voice choice: gendered variants → male/female voice; else explicit `voice`, else
   alternate for diversity.
4. Each clip passes **both safeguards or the build fails loudly** (never ship an unguarded clip).
5. Writes `audio_build/<backend>/<id>.mp3` and the manifest. Cached clips are skipped, so
   re-runs only generate new/changed text.

Run: `python3 scripts/build_audio.py --google` (or `--elevenlabs`). Then upload `gg/`.

**voices.py** — registry; every voice has a `gender` (`f`/`m`) and `BY_GENDER` defaults.
Swap the two entries for the target-locale Chirp3-HD names from Phase 0.

**google_tts.py** — set `GOOGLE_VOICES = {"f": "<xx-XX>-Chirp3-HD-…", "m": "…"}` and the
`languageCode` to the target locale. Everything else is generic.

---

## Pedagogy fundamentals (the non-negotiables)

These are what make the method work; port them verbatim, adapting only the language pair.

1. **Bridge-cognate method.** Instruction is in the bridge language. Teach explicit
   cognate-transformation rules (e.g. `-ar → -er`, spelling correspondences). Lead with
   what transfers for free; flag false friends explicitly.
2. **Full-sentence audio, always.** Never synthesize a lone word.
3. **Voice-gender safeguard** (`gender_guard.assert_gender_ok`): a voice may only speak
   first-person predicate adjectives that agree with its grammatical gender. A male voice
   must never say the feminine self-form. Enforced in the build.
4. **Force target pronunciation** via the voice's `languageCode` — structural, not a prompt.
5. **Spoken-register charter** (write one per project in `docs/`): use the living spoken
   forms, name obsolescent ones for recognition only, restrict to the tenses people
   actually speak, avoid literary/artificial constructions. For *frances*: `on` not `nous`,
   passé composé + imparfait only, no passé simple. Adapt the specifics to the target
   language, keep the principle.
6. **Bilingual readers**: target sentence first, then a **literal 1:1 bridge translation**,
   paragraph-by-paragraph in visually paired blocks (show the shared Latin/root structure).
   A toggle swaps the bridge gloss for the secondary language; bridge is default.
7. **Orientation boxes**: every module opens with a "how this is *formed*" explainer
   (formation tables, pattern boxes), bridge default + gloss toggle. Explaining mechanism
   beats listing examples.
8. **Graded readings via a writer↔critic loop.** The magic is that the learner can read a
   real passage almost entirely through cognates ("I can read it!"). Writer maximizes
   bridge-cognate word choice while staying natural; a strict critic scores cognate density
   (target ≥~80%), enforces the charter, and proposes concrete cognate swaps until it
   passes. Vocab block lists ONLY non-guessable words. Progressive difficulty 1→5. Use a
   strong general model, not a lightweight one, for the writer. (See
   `[[lectures-cognate-magic]]` memory / the `cognate-stories` workflow.)
9. **Quizzes**: mostly multiple-choice, many **listening-based** (hear a clip → pick
   meaning or transcription). Culture/content quizzes are **target-language only** (simple
   words + cognates, no bridge sentences). `drills` in lessons auto-feed a Grammar
   category; bridge-language "traps" feed a Pitfalls category.
10. **Flashcards (Cartes)**: tap-to-reveal (see target, hear it, reveal bridge + gloss).
    Spacing is cognate-aware — surface hard/non-cognate items more, sprinkle cognates for
    confidence, don't dwell on freebies. Backed by a local progress store.

---

## App modes & UX conventions (already built in `app.html`)

- **Home** toggles four modes: **Leçons / Quiz / Cartes / Lectures** (`fpb_mode`).
- **Language toggle** (`fpb_lang`, default bridge) swaps reader/orientation gloss.
- **Progress store** in `localStorage` (`fpb_progress`, versioned) + a **Settings** gear to
  observe/clear it (keep reset easy during dev).
- **Audio controls**: clicking a play button again pauses/resumes; switching clips stops
  the previous. Lecture reader uses a native `<audio controls>` (scrub/rewind) plus
  ↺/«10s/⏸ buttons.
- **Navigation** scrolls to top on hashchange (in-place re-renders keep scroll).
- Rename the storage keys/prefixes (`fpb_*`, `fpb-vNN`) to `<PREFIX>_*` per project.

---

## Deploy & PWA versioning

- Bump `sw.js` `VER` (`<PREFIX>-vNN`) whenever cached files change (lesson JSON, app.html,
  manifest). List new data files in the `CORE` array so offline works.
- `node --check` the extracted inline JS from `app.html` before every deploy.
- Validate all JSON. Run the gender guard dry-run across all clips.
- Push both branches; verify the Pages URL serves the new `VER` and content.

---

## New-project quickstart checklist

1. **Phase 0 interview** → fill the project spec (languages, learner, gender, goal, size,
   voices, `<slug>`, `<PREFIX>`).
2. `gh repo create <slug>` (or copy this repo); enable Pages from `gh-pages`.
3. Point audio at `gs://bmount-public-share/<slug>/`; confirm bucket is public + CORS.
4. List target-locale Chirp3-HD voices; set them in `voices.py` + `google_tts.py`
   (`GOOGLE_VOICES` + `languageCode`).
5. Write `docs/teaching-charter.md` (spoken register for the target language) and a
   `docs/curriculum-map.md`.
6. Author Chapter 0 (sounds/spelling) + core grammar lessons + topical modules; keep the
   schemas above. Every clip a full sentence; gendered self-forms split m/f.
7. Generate readings with the writer↔critic loop (cognate density ≥~80%, charter-clean).
8. `python3 scripts/build_audio.py --google` → guard passes → upload `gg/`.
9. Wire modules into `app.html` boot list, `index.html` course map, `sw.js` CORE; bump `VER`.
10. node-check, validate JSON, deploy both branches, verify live.

---

## What changes per project vs. what's fixed

| Fixed (reuse as-is) | Per-project (from Phase 0) |
|---|---|
| GCP project/bucket `bmount-public-share`, public+CORS | `<slug>` path prefix, live URL |
| Google Chirp3-HD REST + gcloud auth pattern | target-locale voice names + `languageCode` |
| GitHub Pages two-branch deploy, PWA sw pattern | `<PREFIX>` cache prefix, storage keys |
| App shell: 4 modes, toggles, progress store, audio player | the bridge/target/gloss language slots |
| Build pipeline + both safeguards + manifest format | learner gender, register/charter specifics |
| Pedagogy rules 1–10 above | themes, destination, module list, size |

*Derived from Français pour bébas. The point is that only the right-hand column is new work.*
