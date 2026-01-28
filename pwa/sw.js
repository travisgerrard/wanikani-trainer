const CACHE_NAME = 'wk-trainer-v22';
const ASSETS = [
    './',
    './index.html',
    './manifest.json',
    './sentences.json',
    './audio/manifest.json'
];

// Install - cache everything
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(async cache => {
            await cache.addAll(ASSETS);
            
            // Audio/Images caching logic
            try {
                const audioRes = await fetch('./audio/manifest.json');
                if (audioRes.ok) {
                    const manifest = await audioRes.json();
                    const audioFiles = manifest.map(item => `./audio/${item.file}`);
                    await cache.addAll(audioFiles);
                }
                const sentRes = await fetch('./sentences.json');
                if (sentRes.ok) {
                    const sentences = await sentRes.json();
                    const images = [];
                    sentences.forEach(i => i.sentences.forEach(s => { if(s.image) images.push(`./${s.image}`); }));
                    await cache.addAll(images);
                }
            } catch (e) { console.log("Pre-cache error", e); }
            
            return self.skipWaiting();
        })
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => Promise.all(
            keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
        )).then(() => self.clients.claim())
    );
});

// Fetch Strategy
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);
    
    // NETWORK FIRST for the main HTML/Root to ensure updates
    if (url.pathname === '/' || url.pathname.endsWith('index.html')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
        return;
    }

    // CACHE FIRST for everything else (Images, Audio, JSON)
    event.respondWith(
        caches.match(event.request).then(cached => {
            return cached || fetch(event.request).then(response => {
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                }
                return response;
            });
        })
    );
});