// Ἑλληνικά service worker — bump VER whenever any cached file changes.
const VER = 'grk-v03';
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

// Network-first for course data & pages (so updates show), cache fallback for offline.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request)
      .then(res => {
        const copy = res.clone();
        caches.open(VER).then(c => c.put(e.request, copy)).catch(() => {});
        return res;
      })
      .catch(() => caches.match(e.request).then(m => m || caches.match('./index.html')))
  );
});
