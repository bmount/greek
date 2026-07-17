// Ἑλληνικά service worker — bump VER whenever any cached file changes.
const VER = 'grk-v06';
const CORE = [
  './',
  './index.html',
  './app.html',
  './manifest.json',
  './icon.svg',
  './data/texts/john.json',
  './data/grammar.json',
  './data/audio_manifest.json',
  './data/modern.json',
  './data/vocab.json',
  './data/gym_manifest.json'
];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(VER).then(c => c.addAll(CORE)).catch(() => {}));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== VER).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// IMPORTANT: only handle same-origin, non-range GETs. Audio lives on a different origin
// (storage.googleapis.com) and uses HTTP range requests; intercepting those and returning a
// non-range response makes iOS Safari bail out and open the media URL as a top-level page.
// So we let ALL cross-origin requests — and any request with a Range header — pass straight
// through to the network, untouched.
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   // audio + any 3rd-party: don't touch
  if (req.headers.has('range')) return;              // never intercept range requests

  e.respondWith(
    fetch(req)
      .then(res => {
        const copy = res.clone();
        caches.open(VER).then(c => c.put(req, copy)).catch(() => {});
        return res;
      })
      .catch(() =>
        caches.match(req).then(m =>
          m || (req.mode === 'navigate' ? caches.match('./index.html') : Response.error())
        )
      )
  );
});
