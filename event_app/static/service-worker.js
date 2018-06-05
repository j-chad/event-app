var version = '1.0.0';

self.addEventListener('install', function (event) {
    console.log('[ServiceWorker] Installed version', version);
    console.log('[ServiceWorker] Skip waiting on install');
    event.waitUntil(
        self.skipWaiting()
    );
});

self.addEventListener('activate', function (event) {
    self.clients.matchAll({
        includeUncontrolled: true
    }).then(function (clientList) {
        var urls = clientList.map(function (client) {
            return client.url;
        });
        console.log('[ServiceWorker] Matching clients:', urls.join(', '));
    });

    console.log('[ServiceWorker] Claiming clients for version', version);
    event.waitUntil(
        self.clients.claim()
    );
});

self.addEventListener('push', function (event) {
    var data = event.data.json();
    event.waitUntil(
        self.registration.showNotification(data.title, data.options)
    );
});