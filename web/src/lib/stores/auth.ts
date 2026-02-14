import { writable } from 'svelte/store';
import { browser } from '$app/environment';

interface User {
	id: string;
	email: string;
	role: 'devadmin' | 'professional' | 'patient';
	first_name: string;
	last_name: string;
	is_active: boolean;
	created_at: string;
	profile?: {
		bio?: string;
		phone?: string;
		date_of_birth?: string;
		height_cm?: number;
		avatar_storage_key?: string;
	};
	weight_stats?: {
		initial_weight_kg: number | null;
		initial_weight_date: string | null;
		current_weight_kg: number | null;
		current_weight_date: string | null;
	};
	my_professional?: {
		first_name: string;
		last_name: string;
		email: string;
		phone?: string;
		bio?: string;
	} | null;
}

interface AuthState {
	user: User | null;
	accessToken: string | null;
	refreshToken: string | null;
	isAuthenticated: boolean;
}

function createAuthStore() {
	let initial: AuthState = {
		user: null,
		accessToken: null,
		refreshToken: null,
		isAuthenticated: false
	};

	if (browser) {
		try {
			const saved = localStorage.getItem('bt_auth');
			if (saved) {
				const parsed = JSON.parse(saved);
				initial = { ...parsed, isAuthenticated: !!parsed.accessToken };
			}
		} catch {}
	}

	const { subscribe, set, update } = writable<AuthState>(initial);

	function persist(state: AuthState) {
		if (browser) {
			localStorage.setItem('bt_auth', JSON.stringify(state));
		}
	}

	return {
		subscribe,
		login(user: User, accessToken: string, refreshToken: string) {
			const state: AuthState = { user, accessToken, refreshToken, isAuthenticated: true };
			set(state);
			persist(state);
		},
		setTokens(accessToken: string, refreshToken: string) {
			update((s) => {
				const state = { ...s, accessToken, refreshToken };
				persist(state);
				return state;
			});
		},
		updateUser(user: User) {
			update((s) => {
				const state = { ...s, user };
				persist(state);
				return state;
			});
		},
		logout() {
			const state: AuthState = {
				user: null,
				accessToken: null,
				refreshToken: null,
				isAuthenticated: false
			};
			set(state);
			if (browser) {
				localStorage.removeItem('bt_auth');
			}
		}
	};
}

export const authStore = createAuthStore();
