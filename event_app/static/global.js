//Load Service Worker
var serviceWorker;

if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
        serviceWorker = registerServiceWorker();
    });
} else {
    //Give Error
}

function registerServiceWorker() {
    return navigator.serviceWorker.register('/service-worker')
        .then(function (registration) {
            console.log('Service worker successfully registered.');
            return registration;
        })
        .catch(function (err) {
            console.error('Unable to register service worker.', err);
        });
}

function requestWebPush() {
    return new Promise(function (resolve, reject) {
        const permissionResult = Notification.requestPermission(function (result) {
            resolve(result);
        });

        if (permissionResult) {
            permissionResult.then(resolve, reject);
        }
    }).then(function (permissionResult) {
        if (permissionResult !== 'granted') {
            throw new Error('We weren\'t granted permission.');
        }
    });
}
