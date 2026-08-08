/*
 * Service worker for the Image Converter PWA.
 *
 * Purpose: make the app installable and usable fully offline once served over
 * http(s). This does NOT run under file:// — browsers refuse to register a
 * service worker from a file URL, and the app doesn't need it there anyway.
 *
 * Strategy: cache-first for the app shell (the HTML, manifest, and icons).
 * JSZip is loaded from a CDN and is intentionally NOT cached here to avoid
 * cross-origin opaque-response bloat; if you want the ZIP feature offline,
 * vendor jszip.min.js locally and add it to APP_SHELL below.
 */
const CACHE = "image-converter-v2";

const APP_SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/camera.svg",
  "./icons/favicon.ico",
  "./icons/favicon-16.png",
  "./icons/favicon-32.png",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  // Only handle same-origin GETs from our shell; let everything else (e.g. the
  // JSZip CDN request) go straight to the network.
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;

  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((res) => {
        // Runtime-cache successful same-origin responses.
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((cache) => cache.put(req, copy));
        }
        return res;
      }).catch(() => cached);
    })
  );
});
