const CACHE_NAME = 'ochakovo-v1.1.0';
const OFFLINE_URL = '/offline/';

const STATIC_ASSETS = [
  // Основные навигационные страницы
  '/',
  '/game/',
  '/vacancies/',
  '/story/',
  '/progress/',
  '/offline/',
  '/manifest.json',

  // Все 7 производственных кейсов симулятора завода
  '/game/brew-yeast-flex/',
  '/game/brew-double-fermentation/',
  '/game/krones-robot-tilt/',
  '/game/bot-line-glitch/',
  '/game/okroshka-detective/',
  '/game/warehouse-drift/',
  '/game/secret-drop-1978/',

  // Стили и скрипты
  '/static/css/ochakovo.css',
  '/static/js/app.js',
  '/static/js/simulator.js',
  '/static/manifest.json',

  // Логотипы и брендовые элементы
  '/static/img/ochakovo_logo_official.png',
  '/static/img/ochakovo_logo.svg',
  '/static/img/ochakovo_logo_white.svg',
  '/static/img/ochakovo_emblem.svg',
  '/static/img/icon-192.png',
  '/static/img/icon-512.png',
  '/static/favicon.ico',

  // Фотографии наставников и промо-баннер
  '/static/img/mentor_brewer.jpg',
  '/static/img/mentor_engineer.jpg',
  '/static/img/mentor_lab.jpg',
  '/static/img/mentor_logistics.jpg',
  '/static/img/mentor_marketing.jpg',
  '/static/img/ochakovo_hero_banner.jpg',

  // Фоны цехов для визуального симулятора
  '/static/img/vn_bg/bg_brewhouse.jpg',
  '/static/img/vn_bg/bg_brewhouse_cct.jpg',
  '/static/img/vn_bg/bg_bottling_line.jpg',
  '/static/img/vn_bg/bg_bottling_conveyor.jpg',
  '/static/img/vn_bg/bg_laboratory.jpg',
  '/static/img/vn_bg/bg_warehouse.png',
  '/static/img/vn_bg/bg_rnd_lab.jpg',

  // Иконки оборудования цеха
  '/static/img/equipment/valve_cooling.svg',
  '/static/img/equipment/starter_culture.svg',
  '/static/img/equipment/cip_wash.svg',
  '/static/img/equipment/emergency_stop.svg',
  '/static/img/equipment/refractometer.svg',
  '/static/img/equipment/tasting_mug.svg',
  '/static/img/equipment/intercom_radio.svg',
  '/static/img/equipment/ph_meter.svg',

  // Исторические фотографии
  '/static/img/history/history_5.png',
  '/static/img/history/history_6.png',
  '/static/img/history/history_2.png',
  '/static/img/history/history_3.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      console.log('[Ochakovo SW] Pre-caching static assets & all 7 game scenarios...');
      // Добавляем по одному с отловом ошибок, чтобы ни один отсутствующий ассет не сломал кэширование остальных
      for (const asset of STATIC_ASSETS) {
        try {
          await cache.add(asset);
        } catch (err) {
          console.warn('[Ochakovo SW] Failed to pre-cache individual asset:', asset, err);
        }
      }
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

  // 1. Полностью игнорируем POST запросы, API вызовы, авторизацию и видеопотоки
  if (
    req.method !== 'GET' ||
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/auth/') ||
    url.pathname.startsWith('/media/') ||
    url.pathname.startsWith('/video/') ||
    req.headers.get('range') ||
    req.destination === 'video' ||
    req.destination === 'audio'
  ) {
    return;
  }

  // 2. Навигационные запросы (HTML страницы) -> Network First с интеллектуальным офлайн-поиском
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((response) => {
          if (response && response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          }
          return response;
        })
        .catch(async () => {
          // 1. Ищем точное совпадение
          let cached = await caches.match(req);
          if (cached) return cached;

          // 2. Ищем без query параметров (?from=stand_qr, ?session=..., etc.)
          cached = await caches.match(req, { ignoreSearch: true });
          if (cached) return cached;

          // 3. Ищем с нормализованным завершающим слэшем
          const normalizedPath = url.pathname.endsWith('/') ? url.pathname : (url.pathname + '/');
          cached = await caches.match(normalizedPath);
          if (cached) return cached;

          // 4. Если открывался сценарий /game/<slug>/, пробуем вернуть /game/ (каталог смен)
          if (url.pathname.startsWith('/game/')) {
            const gameHub = await caches.match('/game/');
            if (gameHub) return gameHub;
          }

          // 5. Если открывалась вакансия /vacancies/<slug>/, пробуем вернуть /vacancies/
          if (url.pathname.startsWith('/vacancies/')) {
            const vacHub = await caches.match('/vacancies/');
            if (vacHub) return vacHub;
          }

          // 6. Возвращаем обогащенную офлайн-страницу
          const offlinePage = await caches.match(OFFLINE_URL);
          if (offlinePage) return offlinePage;

          return new Response('Офлайн-режим Очаково: нет соединения с сетью.', {
            status: 503,
            headers: { 'Content-Type': 'text/plain; charset=utf-8' }
          });
        })
    );
    return;
  }

  // 3. Статические файлы (CSS, JS, картинки, шрифты) -> Cache First с фоновым обновлением
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(req).then((cachedResponse) => {
        if (cachedResponse) {
          // Фоновое обновление кэша
          fetch(req).then((netResp) => {
            if (netResp && netResp.status === 200) {
              caches.open(CACHE_NAME).then((cache) => cache.put(req, netResp));
            }
          }).catch(() => {});
          return cachedResponse;
        }
        return fetch(req)
          .then((netResp) => {
            if (netResp && netResp.status === 200) {
              const copy = netResp.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
            }
            return netResp;
          })
          .catch(() => caches.match('/static/img/icon-192.png'));
      })
    );
    return;
  }

  // 4. Стандартный fallback с безопасным catch (без Uncaught TypeError)
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).catch(() => {
        return new Response('', { status: 408, statusText: 'Request Timeout / Offline' });
      });
    })
  );
});
