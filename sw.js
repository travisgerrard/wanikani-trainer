const CACHE_NAME = 'wk-trainer-v10';
const ASSETS = [
    './',
    './index.html',
    './manifest.json',
    './sentences.json',
    './audio/manifest.json'
];

// Install - cache assets AND audio files
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(async cache => {
            // 1. Cache static assets
            await cache.addAll(ASSETS);

            // 2. Fetch and cache audio files from manifest
            try {
                const response = await fetch('./audio/manifest.json');
                if (response.ok) {
                    const manifest = await response.json();
                    const audioFiles = manifest.map(item => `./audio/${item.file}`);
                    if (audioFiles.length > 0) {
                        await cache.addAll(audioFiles);
                        console.log(`[SW] Cached ${audioFiles.length} audio files`);
                    }
                }
            } catch (err) {
                console.error('[SW] Failed to cache audio files:', err);
            }

            // 3. Fetch and cache images from sentences.json
            try {
                const response = await fetch('./sentences.json');
                if (response.ok) {
                    const sentences = await response.json();
                    const imageFiles = [];
                    sentences.forEach(item => {
                        item.sentences.forEach(s => {
                            if (s.image) {
                                imageFiles.push(`./${s.image}`);
                            }
                        });
                    });
                    if (imageFiles.length > 0) {
                        await cache.addAll(imageFiles);
                        console.log(`[SW] Cached ${imageFiles.length} image files`);
                    }

                    // Notify clients that we are ready
                    const allClients = await self.clients.matchAll();
                    allClients.forEach(client => {
                        client.postMessage({ type: 'OFFLINE_READY' });
                    });
                }
            } catch (err) {
                console.error('[SW] Failed to cache image files:', err);
            }

            return self.skipWaiting();
        })
    );
});

// Activate - clean old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch - Strict Cache First (No background revalidation)
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(cached => {
                if (cached) {
                    return cached;
                }
                // Not cached - fetch and cache
                return fetch(event.request).then(response => {
                    // Only cache valid responses
                    if (response.ok && response.type === 'basic') {
                        const clone = response.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => cache.put(event.request, clone));
                    }
                    return response;
                });
            })
    );
});
