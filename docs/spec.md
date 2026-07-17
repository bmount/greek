# Ἑλληνικά — Greek as One Continuous Culture

**A cross-linked reader + grammar course for Ancient (Koine/Classical/Homeric) and
Modern Greek, treated as one language tradition across time.**

Derived from the *Language Course Creator* playbook (`language-course-creator-reference.md`),
adapted from a bridge-cognate *conversation* course into a **reading-and-grammar** course
built around authentic canonical texts.

---

## Phase 0 — Project spec

| Field | Value |
|---|---|
| **Target** | Greek, all eras: Koine (Septuagint, GNT), Classical/epic (Homer, Herodotus, pre-Socratics), Modern. Treated as **one continuous culture**. |
| **Bridge language** | **English** (language of instruction, primary gloss). |
| **Second gloss** | **Spanish** (toggle; learner is native-level). |
| **Learner** | Adult, top ~0.5% receptive vocabulary (National Merit level), native English + Spanish. Vocabulary breadth is largely *free*; the hard, new material is **morphology** (declension, conjugation, aspect, voice, mood) and reading real syntax. |
| **Register / pronunciation** | Modern/Byzantine pronunciation applied to **all** eras (consistent with "one culture"), because audio uses Modern Greek voices. |
| **Audio** | Google Chirp3-HD, `el-GR` voices (1 m + 1 f). Full-sentence clips only. *(Phase 2 — not in first deploy.)* |
| **Orthography** | Polytonic for ancient texts (authentic accents/breathings); monotonic for Modern. |
| **Naming** | slug `greek`, cache prefix `grk`. Live: `https://bmount.github.io/greek/`. Repo: `git@github.com:bmount/greek.git`. |
| **Hosting** | GitHub Pages, static SPA, no build step. Audio (later) on `gs://bmount-public-share/greek/`. |

---

## The core divergence from the reference playbook

The playbook's signature trick is a **writer↔critic loop generating cognate-dense passages
(~80% guessable)** for the "I can read it!" hit. Our motivational spine is instead
**authentic canonical texts** — Homer, John, Ecclesiastes, Heraclitus, Herodotus — which we
must **not** rewrite. So "readings" split into two types:

1. **Authentic texts** (the spine) — real excerpts, *unaltered*, presented with heavy
   scaffolding: tap-to-parse, lemma glosses, grammar/parsing notes, cultural-theological
   commentary, full-sentence audio. Graded by *scaffolding needed*, not cognate density.
2. **Generated confidence-builders** (optional, early modules only) — short cognate-dense
   Modern-Greek passages via the writer↔critic loop, for momentum before Homer.

The learner's huge erudite vocabulary means glosses **assume** learned English/Spanish and
chain Greek root → sophisticated derivative: λόγος → *logos, -logy, eulogy*; χθών →
*chthonic*; δίκη → *theodicy*; ἀρετή → *arete*; κένωσις → *kenosis*.

---

## Architecture — one cross-linked content graph

Three first-class node types, bidirectionally linked:

1. **Text tokens** — every word in every excerpt: surface form, lemma ref, full parse,
   (later) sentence audio. Links → its lemma and its grammar concepts.
2. **Lemma / lexicon entries** — dictionary form, EN gloss (default) / ES gloss (toggle),
   erudite derivative chains, cognate type, and every occurrence across all texts.
3. **Grammar concepts** — each morphological feature is a lesson node (e.g. *genitive
   absolute*, *aorist middle*, *3rd-declension -ματ stems*, *predicate nominative*). Lists
   real occurrences pulled from the texts.

### Two views into the same graph
- **Textbook track (A-style):** sequential, traditional grammar course — paradigm tables,
  explanations, drills — chapter by chapter. The linear spine.
- **Reading track (C-style):** authentic excerpts where **tapping a word opens a parse
  modal** (surface → lemma → full parse → gloss + derivatives → "▸ Learn this: [concept]"
  deep-link into the exact Textbook lesson). Tapping the lemma opens the lexicon entry with
  all occurrences.

The two are the *same* nodes: a concept lesson lists text occurrences that deep-link into
Reading; a text word points back to its concept lesson. Truly bidirectional.

### Extra cross-link UI
- **Parse modal** (from any word) — the primary bridge from Reading → Grammar.
- **Lexicon entry** (from any lemma) — gloss, derivatives, all occurrences.
- **Concept occurrences** — from any Grammar lesson back into the live texts.

---

## Content sourcing — ingest, don't hand-parse

Tap-to-parse requires every token morphologically analysed. This exists as **open tagged
data** matching our text list, so content is an *ingest-and-annotate* job:

| Text | Source corpus |
|---|---|
| Gospel of John (Koine) | MorphGNT / SBLGNT (fully parsed + lemmatized) |
| Ecclesiastes (Septuagint) | CATSS/CCAT LXX morphology |
| Homer, Herodotus, Hesiod, pre-Socratics | Perseus & PROIEL / Diorisis treebanks |
| Lemma → gloss + derivative chains | our lexicon layer, authored once per lemma |

Pipeline: import tagged corpus → map to our token schema → attach glosses / derivative
chains / grammar-concept IDs → dedupe lemmas into the lexicon.

---

## Content pillars (motivational spine)

- **Koine** — Gospel of John, Ecclesiastes (Septuagint).
- **Homer** — excerpts on worldview, morality, theology.
- **History** — Herodotus (extensive narrative).
- **Philosophers** — pre-Socratics + idiosyncratic/relatable figures (Cynics).
- **Modern Greek** — excerpts & explainers (the living end of the continuum).
- **Grammar** — extensive, textbook-style: phonology, the case system, all declensions,
  the verb (aspect/voice/mood), participles, μι-verbs, syntax.

Progressive reading difficulty: John / Ecclesiastes (regular Koine) → philosophers (denser)
→ Herodotus (Ionic prose) → Homer (epic/dialectal) last.

## Quizzes
- Content quizzes in **Greek only** (per playbook rule 9), scaled up for this learner:
  **history & specific narratives** (Herodotus accounts), then **substance of mythology**
  (who/what/why), then theology/philosophy comprehension.
- Grammar quizzes: parsing drills, paradigm production, decline/conjugate-this, and
  false-friend "traps".
- Many listening-based once audio lands (Phase 2).

---

## App modes & UX
- **Home** toggles modes: **Reading / Textbook / Quiz / Cards** (`grk_mode`).
- **Gloss toggle** EN↔ES (`grk_lang`, English default).
- **Progress store** in `localStorage` (`grk_progress`, versioned) + Settings gear to
  clear it.
- Mobile-first, responsive, **highly legible** — refined serif for Greek, clean sans for UI.
- PWA: `sw.js` versioned `grk-vNN`.

---

## Phasing

**Phase 1 (first deploy — now):** prove the whole loop on **Gospel of John 1:1–5** (fully
parsed, most cognate-accessible). Reading view with tap-to-parse modal; Textbook view with
the grammar concepts the prologue touches; EN/ES gloss toggle; cross-linking both ways;
mobile-first legible design; PWA + GitHub Pages deploy. **No audio yet.**

**Phase 2:** audio pipeline (`el-GR` Chirp3-HD, full-sentence clips, gender guard) + GCS
upload; listening quizzes.

**Phase 3:** corpus ingest scripts (MorphGNT, LXX, Perseus/PROIEL) → scale texts; full
Textbook spine; Quiz + Cards modes; generated cognate confidence-builders; Herodotus/Homer.

---

## What's fixed vs. per-project (from the playbook)

| Fixed (reuse) | This project |
|---|---|
| GCP bucket `bmount-public-share`, Pages 2-branch deploy, PWA pattern | slug `greek`, prefix `grk` |
| Chirp3-HD REST + gcloud auth | `el-GR` voice names + `languageCode` |
| Full-sentence audio, gender guard, force-target-pronunciation | Modern pronunciation for all eras |
| Bilingual reader, orientation boxes, tap-to-reveal cards | **new:** tap-to-parse graph, dual cross-linked tracks, morphology-first difficulty |
