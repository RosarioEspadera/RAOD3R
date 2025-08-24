const CACHE_NAME = "raod3r-cache-v1";
const urlsToCache = [
  "./",             // resolves to /docs/
  "./index.html",
  "./styles.css",
  "./reader.html",
  "./library.html"
];

// Install and cache files
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache);
    }).catch(err => {
      console.error("Failed to pre-cache:", err);
    })
  );
});

// Activate and clean old caches
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      )
    )
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request).catch(err => {
        console.error("Fetch failed; returning offline page instead.", err);
        // You could return a fallback page here if it's an HTML request
        return caches.match("./index.html");
      });
    })
  );
});
