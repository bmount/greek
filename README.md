# Ἑλληνικά — Greek across the ages

A cross-linked reader + grammar course that treats Greek as **one continuous culture** —
Koine, Classical/epic, and Modern as a single language across time. Read the real texts
(Homer, John, Ecclesiastes, Herodotus, the pre-Socratics) with every word one tap away from
its full grammatical parse and the lesson that explains it.

- **Bridge language:** English (instruction + primary gloss), Spanish as a second gloss.
- **Method:** authentic canonical texts as the motivational spine; morphology-first grammar
  (the hard, new part for an English/Spanish speaker); erudite cognate leverage.
- Built on the [Language Course Creator](./language-course-creator-reference.md) framework.
  Full design in [`docs/spec.md`](./docs/spec.md).

**Live:** https://bmount.github.io/greek/

## This build (Phase 1)
Proves the whole loop on the **Prologue of John (1:1–5)** — fully parsed:

- **Reading** — tap any Greek word → parse, gloss (EN/ES), the English/Spanish vocabulary it
  unlocks, exegetical notes, and a jump into the grammar lesson.
- **Textbook** — 18 sequential grammar lessons (the article, five cases, three declensions,
  the verb & its aspects), each cross-linked to where it appears in the live text.
- Truly bidirectional: words link into grammar; grammar lessons list live occurrences that
  jump back into the text.

Static SPA, no build step. Runs offline as a PWA.

## Structure
```
index.html                landing / course map
app.html                  the SPA (inline JS/CSS)
manifest.json  sw.js  icon.svg   PWA
data/
  texts/john.json         parsed tokens (lemma, morphology, gloss, derivatives)
  grammar.json            cross-linked grammar concept lessons
docs/spec.md              full design
```

## Local preview
```bash
python3 -m http.server 8731   # then open http://localhost:8731/
```

## Deploy
```bash
git push origin main && git push origin main:gh-pages
```
Bump `VER` in `sw.js` whenever cached files change.

## Roadmap
- **Phase 2:** audio (Modern Greek `el-GR` Chirp3-HD, full-sentence clips) + listening quizzes.
- **Phase 3:** ingest tagged corpora (MorphGNT, LXX, Perseus/PROIEL) to scale texts; Homer,
  Herodotus, Ecclesiastes, pre-Socratics, Modern Greek; history/mythology quizzes; flashcards.
