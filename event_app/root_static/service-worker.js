var version = '1.3.6';

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

    const urlToCheck = new URL(data.options.data.url, self.location.origin).href;

    const promiseChain = self.clients.matchAll({
        type: 'window',
        includeUncontrolled: true
    }).then((windowClients) => {
        let matchingClient = null;

        for (let i = 0; i < windowClients.length; i++) {
            const windowClient = windowClients[i];
            if (windowClient.url === urlToCheck) {
                matchingClient = windowClient;
                break;
            }
        }

        if (matchingClient) {
            return matchingClient.focus();
        } else {
            return self.registration.showNotification(data.title, data.options)
        }
    });

    event.waitUntil(promiseChain);
});

self.addEventListener('notificationclick', function (event) {
    const clickedNotification = event.notification;
    const data = clickedNotification.data;

    const urlToOpen = new URL(data.url, self.location.origin).href;

    const promiseChain = self.clients.matchAll({
        type: 'window',
        includeUncontrolled: true
    }).then((windowClients) => {
        let matchingClient = null;

        for (let i = 0; i < windowClients.length; i++) {
            const windowClient = windowClients[i];
            if (windowClient.url === urlToOpen) {
                matchingClient = windowClient;
                break;
            }
        }

        if (matchingClient) {
            return matchingClient.focus();
        } else {
            return self.clients.openWindow(urlToOpen);
        }
    });

    event.waitUntil(promiseChain);
});