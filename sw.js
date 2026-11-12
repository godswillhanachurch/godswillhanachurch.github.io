// 높은뜻 하나되는 교회 — 홈 화면 앱용 서비스 워커
// 항상 인터넷의 최신 내용을 먼저 보여 주고(브라우저 임시 저장도 건너뜀), 인터넷이 끊겼을 때만 저장해 둔 화면을 보여 줍니다.
const CACHE = 'hana-v84';
const CORE = ['/', '/index.html', '/greeting.html', '/about.html', '/news.html', '/mission.html',
  '/nk.html', '/welcome.html', '/en.html',
  '/style.css?v=20261112zj', '/site.js?v=20261112d', '/logo.svg', '/logo-header.svg', '/logo-header-m.svg', '/icons/icon-192.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  if (req.headers.has('range') || /\.(mp4|mov|webm)$/i.test(new URL(req.url).pathname)) return; // 영상은 캐시하지 않고 바로 받음
  e.respondWith(
    fetch(req, { cache: 'no-cache' }).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req).then(r => r || (req.mode === 'navigate' ? caches.match('/index.html') : undefined)))
  );
});
