import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import { en } from './en';
import { es } from './es';

export type Locale = 'en' | 'es';
type Translations = typeof en;

const translations: Record<Locale, Translations> = { en, es };

function createLocaleStore() {
	let initial: Locale = 'en';
	if (browser) {
		const saved = localStorage.getItem('wv_locale') as Locale;
		if (saved === 'en' || saved === 'es') {
			initial = saved;
		} else if (navigator.language.startsWith('es')) {
			initial = 'es';
		}
	}

	const { subscribe, set } = writable<Locale>(initial);

	return {
		subscribe,
		set(locale: Locale) {
			set(locale);
			if (browser) {
				localStorage.setItem('wv_locale', locale);
				document.documentElement.lang = locale;
			}
		}
	};
}

export const locale = createLocaleStore();

export const t = derived(locale, ($locale) => {
	const dict = translations[$locale];
	return function translate(key: string): string {
		const keys = key.split('.');
		let value: any = dict;
		for (const k of keys) {
			value = value?.[k];
		}
		return (value as string) ?? key;
	};
});
