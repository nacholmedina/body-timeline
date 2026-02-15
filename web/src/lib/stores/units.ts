import { writable, get } from 'svelte/store';
import { browser } from '$app/environment';

export type UnitSystem = 'metric' | 'imperial';

function createUnitStore() {
	let initial: UnitSystem = 'metric';

	if (browser) {
		const saved = localStorage.getItem('wv_units') as UnitSystem;
		if (saved === 'metric' || saved === 'imperial') {
			initial = saved;
		}
	}

	const store = writable<UnitSystem>(initial);

	function setUnit(unit: UnitSystem) {
		store.set(unit);
		if (browser) {
			localStorage.setItem('wv_units', unit);
		}
	}

	return {
		subscribe: store.subscribe,
		set: setUnit,
		toggle() {
			const current = get(store);
			setUnit(current === 'metric' ? 'imperial' : 'metric');
		}
	};
}

export const unitStore = createUnitStore();
