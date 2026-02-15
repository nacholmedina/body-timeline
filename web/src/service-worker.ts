/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';

const sw = self as unknown as ServiceWorkerGlobalScope;

const CACHE_NAME = `wellvio-${version}`;
const APP_SHELL = [...build, ...files];

// Install: cache app shell
sw.addEventListener('install', (event) => {
	event.waitUntil(
		caches
			.open(CACHE_NAME)
			.then((cache) => cache.addAll(APP_SHELL))
			.then(() => sw.skipWaiting())
	);
});

// Activate: clean old caches
sw.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then((keys) =>
			Promise.all(
				keys
					.filter((key) => key !== CACHE_NAME)
					.map((key) => caches.delete(key))
			)
		).then(() => sw.clients.claim())
	);
});

// Fetch strategy
sw.addEventListener('fetch', (event) => {
	const url = new URL(event.request.url);

	// Skip non-GET requests
	if (event.request.method !== 'GET') return;

	// API requests: network-first with cache fallback (stale-while-revalidate)
	if (url.pathname.startsWith('/api/')) {
		event.respondWith(
			caches.open(CACHE_NAME).then(async (cache) => {
				try {
					const networkResponse = await fetch(event.request);
					if (networkResponse.ok) {
						cache.put(event.request, networkResponse.clone());
					}
					return networkResponse;
				} catch {
					const cached = await cache.match(event.request);
					return cached || new Response(
						JSON.stringify({ error: 'Offline', message: 'No cached data available' }),
						{ status: 503, headers: { 'Content-Type': 'application/json' } }
					);
				}
			})
		);
		return;
	}

	// App shell: cache-first
	if (APP_SHELL.includes(url.pathname)) {
		event.respondWith(
			caches.match(event.request).then((cached) => cached || fetch(event.request))
		);
		return;
	}

	// Navigation: network-first with offline fallback
	if (event.request.mode === 'navigate') {
		event.respondWith(
			fetch(event.request).catch(() =>
				caches.match(event.request).then((cached) =>
					cached || caches.match('/') || new Response('Offline', { status: 503 })
				)
			)
		);
		return;
	}

	// Other requests: stale-while-revalidate
	event.respondWith(
		caches.open(CACHE_NAME).then(async (cache) => {
			const cached = await cache.match(event.request);
			const networkFetch = fetch(event.request).then((response) => {
				if (response.ok) {
					cache.put(event.request, response.clone());
				}
				return response;
			}).catch(() => cached);

			return cached || (await networkFetch) || new Response('Offline', { status: 503 });
		})
	);
});
