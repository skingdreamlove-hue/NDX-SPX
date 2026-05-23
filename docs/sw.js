var CACHE_NAME = 'ussentiment-v6';

var STATIC_ASSETS = [
  'manifest.json'
];

self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function(e) {
  e.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(k) { return k !== CACHE_NAME })
          .map(function(k) { return caches.delete(k) })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function(e) {
  if (e.request.method !== 'GET') return;

  var url = e.request.url;
  if (url.indexOf('query1.finance.yahoo.com') >= 0) return;
  if (url.indexOf('.json') >= 0) return;

  if (url.indexOf('manifest.json') >= 0) {
    e.respondWith(
      caches.match(e.request).then(function(cached) {
        return cached || fetch(e.request);
      })
    );
    return;
  }

  e.respondWith(
    fetch(e.request).then(function(response) {
      if (response && response.status === 200) {
        var cloned = response.clone();
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(e.request, cloned);
        });
      }
      return response;
    }).catch(function() {
      return caches.match(e.request);
    })
  );
});