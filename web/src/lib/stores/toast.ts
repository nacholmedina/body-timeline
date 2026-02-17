import { writable } from 'svelte/store';

export type ToastType = 'success' | 'error' | 'info';

export interface Toast {
	id: number;
	message: string;
	type: ToastType;
}

function createToastStore() {
	const { subscribe, update } = writable<Toast[]>([]);
	let nextId = 0;

	return {
		subscribe,
		show: (message: string, type: ToastType = 'success', duration = 3000) => {
			const id = nextId++;
			const toast: Toast = { id, message, type };

			update(toasts => [...toasts, toast]);

			setTimeout(() => {
				update(toasts => toasts.filter(t => t.id !== id));
			}, duration);
		},
		success: (message: string, duration = 3000) => {
			createToastStore().show(message, 'success', duration);
		},
		error: (message: string, duration = 4000) => {
			createToastStore().show(message, 'error', duration);
		},
		info: (message: string, duration = 3000) => {
			createToastStore().show(message, 'info', duration);
		},
		dismiss: (id: number) => {
			update(toasts => toasts.filter(t => t.id !== id));
		}
	};
}

export const toastStore = createToastStore();
