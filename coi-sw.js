// Cross-origin isolation for hosts that cannot send headers.
//
// The game is a pthreads build: it needs SharedArrayBuffer, which a browser
// only hands to a page served with
//
//   Cross-Origin-Opener-Policy: same-origin
//   Cross-Origin-Embedder-Policy: require-corp
//
// GitHub Pages cannot set response headers. A service worker can: it sits
// between the page and the network and adds the two headers to every response
// it passes through, including the page itself and the worker scripts the
// threads start from. index.html registers this file only when the page is
// not already isolated, then reloads once so the page is fetched through it.
//
// Everything the game loads is same-origin, so nothing needs a
// Cross-Origin-Resource-Policy header to get past require-corp.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));

self.addEventListener('fetch', e => {
  const req = e.request;
  // Chrome sends this for some devtools requests; fetch() would throw on it.
  if (req.cache === 'only-if-cached' && req.mode !== 'same-origin') return;
  e.respondWith(fetch(req).then(res => {
    if (res.status === 0) return res;   // opaque: cannot be rewrapped
    const headers = new Headers(res.headers);
    headers.set('Cross-Origin-Opener-Policy', 'same-origin');
    headers.set('Cross-Origin-Embedder-Policy', 'require-corp');
    return new Response(res.body, { status: res.status, statusText: res.statusText, headers });
  }));
});
