import { writable, get } from 'svelte/store';
import { browser } from '$app/environment';

type Theme = 'light' | 'dark';

function createThemeStore() {
	let initial: Theme = 'light';

	if (browser) {
		const saved = localStorage.getItem('bt_theme') as Theme;
		if (saved === 'dark' || saved === 'light') {
			initial = saved;
		} else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
			initial = 'dark';
		}
	}

	const store = writable<Theme>(initial);

	function apply(theme: Theme) {
		if (browser) {
			document.documentElement.classList.toggle('dark', theme === 'dark');
			localStorage.setItem('bt_theme', theme);
		}
	}

	// Apply initial theme
	if (browser) {
		apply(initial);
	}

	function setTheme(theme: Theme) {
		store.set(theme);
		apply(theme);
	}

	return {
		subscribe: store.subscribe,
		set: setTheme,
		toggle() {
			const current = get(store);
			setTheme(current === 'dark' ? 'light' : 'dark');
		}
	};
}

export const themeStore = createThemeStore();
