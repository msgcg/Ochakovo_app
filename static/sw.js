const CACHE_NAME = 'ochakovo-v1.0.0';
const OFFLINE_URL = '/offline/';

const STATIC_ASSETS = [
  '/',
  '/game/',
  '/vacancies/',
  '/story/',
  '/offline/',
  '/static/css/ochakovo.css',
  '/static/js/app.js',
  '/static/js/simulator.js',
  '/static/img/ochakovo_logo.svg',
  '/static/img/ochakovo_logo_white.svg',
  '/static/img/ochakovo_emblem.svg',
  '/static/img/icon-192.png',
  '/static/img/icon-512.png',
  '/static/img/mentor_brewer.jpg',
  '/static/img/mentor_engineer.jpg',
  '/static/img/ochakovo_hero_banner.jpg',
  '/static/img/equipment/valve_cooling.svg',
  '/static/img/equipment/starter_culture.svg',
  '/static/img/equipment/cip_wash.svg',
  '/static/img/equipment/emergency_stop.svg',
  '/static/img/equipment/refractometer.svg',
  '/static/img/equipment/tasting_mug.svg',
  '/static/img/equipment/intercom_radio.svg',
  '/static/img/equipment/ph_meter.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Ochakovo SW] Pre-caching static assets');
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[Ochakovo SW] Pre-cache partial warning:', err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[Ochakovo SW] Removing old cache:', key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Не кэшируем POST запросы и API вызовы
  if (req.method !== 'GET' || url.pathname.startsWith('/api/')) {
    return;
  }

  // Навигационные запросы (HTML страницы) -> Network First с fallback на кэш или OFFLINE_URL
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(req);
          if (cached) return cached;
          return caches.match(OFFLINE_URL);
        })
    );
    return;
  }

  // Статические файлы (CSS, JS, картинки, шрифты) -> Cache First с обновлением в фоне
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(req).then((cachedResponse) => {
        if (cachedResponse) {
          // Фоновое обновление
          fetch(req).then((netResp) => {
            if (netResp && netResp.status === 200) {
              caches.open(CACHE_NAME).then((cache) => cache.put(req, netResp));
            }
          }).catch(() => {});
          return cachedResponse;
        }
        return fetch(req).then((netResp) => {
          const copy = netResp.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          return netResp;
        });
      })
    );
    return;
  }

  // Стандартный fallback
  event.respondWith(
    caches.match(req).then((cached) => cached || fetch(req))
  );
});
