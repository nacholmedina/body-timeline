import { writable } from 'svelte/store';
import { browser } from '$app/environment';

function createOnlineStore() {
	const { subscribe, set } = writable<boolean>(browser ? navigator.onLine : true);

	if (browser) {
		window.addEventListener('online', () => set(true));
		window.addEventListener('offline', () => set(false));
	}

	return { subscribe };
}

export const onlineStore = createOnlineStore();
