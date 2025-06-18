const STATIC_CACHE_NAME = 'site-static-v1';
const DYNAMIC_CACHE_NAME = 'site-dynamic-v1';

// Lista de arquivos essenciais da nossa aplicação (a "casca")
const ASSETS = [
    '/',
    '/login',
    '/calendario',
    '/static/css/style.css',
    '/static/js/script.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/sweetalert2@11',
    'https://cdn.jsdelivr.net/npm/fullcalendar@6.1.14/index.global.min.js',
    '/static/images/cesmac-logo.png'
];

// Evento de Instalação: Salva a "casca" da aplicação no cache
self.addEventListener('install', event => {
    console.log('Service Worker: Instalando...');
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME).then(cache => {
            console.log('Service Worker: Colocando a "casca" da aplicação no cache estático.');
            return cache.addAll(ASSETS);
        })
    );
});

// Evento de Ativação: Limpa caches antigos
self.addEventListener('activate', event => {
    console.log('Service Worker: Ativando...');
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(keys
                .filter(key => key !== STATIC_CACHE_NAME && key !== DYNAMIC_CACHE_NAME)
                .map(key => caches.delete(key))
            );
        })
    );
});

// Evento Fetch: Intercepta todas as requisições
self.addEventListener('fetch', event => {
    // Para nossas APIs, usamos a estratégia "Network falling back to Cache"
    if (event.request.url.indexOf('/api/') > -1) {
        event.respondWith(
            caches.open(DYNAMIC_CACHE_NAME).then(cache => {
                return fetch(event.request).then(networkResponse => {
                    cache.put(event.request.url, networkResponse.clone());
                    return networkResponse;
                }).catch(() => {
                    // Se a rede falhar, tenta pegar do cache
                    return cache.match(event.request);
                });
            })
        );
        return;
    }

    // Para a "casca" da aplicação, usamos a estratégia "Cache falling back to Network"
    event.respondWith(
        caches.match(event.request).then(cacheRes => {
            return cacheRes || fetch(event.request).then(fetchRes => {
                return caches.open(STATIC_CACHE_NAME).then(cache => {
                    // Não salvamos requisições que não sejam GET no cache estático
                    if (event.request.method === 'GET') {
                        cache.put(event.request, fetchRes.clone());
                    }
                    return fetchRes;
                });
            });
        }).catch(() => {
            // Se tudo falhar (offline e sem cache), podemos mostrar uma página de fallback
            // Por enquanto, o navegador mostrará sua página de erro padrão
        })
    );
});